import re
import unicodedata
from typing import Dict, Any, List, Tuple
from ollama import embed
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue, MatchAny, Range, QueryResponse, ScoredPoint

cliente = QdrantClient(host='localhost', port=6333)

def normalizar_texto(texto: str) -> str:
    """Normaliza texto eliminando acentos, puntuación y convirtiendo a minúsculas."""
    if not texto:
        return ""
    texto_nfd = unicodedata.normalize('NFD', texto.lower())
    sin_tildes = ''.join(c for c in texto_nfd if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9\s]', ' ', sin_tildes).strip()

def limpiar_frase_consulta(texto: str) -> str:
    """Elimina envoltorios conversacionales, verbos de búsqueda y cláusulas relativas introductorias."""
    s = texto.strip()
    prev = None
    while prev != s:
        prev = s
        s = re.sub(
            r"^(?:busco|buscar|buscando|deseo|quiero|necesito|me\s+interesa|quisiera)\s+(?:ser\s+|trabajar\s+como\s+|trabajar\s+de\s+|conseguir\s+)?",
            "", s, flags=re.IGNORECASE
        )
        s = re.sub(
            r"^(?:algo\s+)?(?:que\s+tenga\s+que\s+ver\s+con|relacionad[ao]s?\s+(?:a|con)|referente\s+(?:a|con))\s+(?:un|una|uno|unos|unas|el|la|los|las)?\s*",
            "", s, flags=re.IGNORECASE
        )
        s = re.sub(
            r"^(?:algun[ao]s?|algun|algua|un|una|uno|unos|unas|el|la|los|las)?\s*(?:vacantes?|empleos?|trabajos?|puestos?|ofertas?|oportunidad(?:es)?|posici[oó]n(?:es)?|labor(?:es)?|algo)\s*",
            "", s, flags=re.IGNORECASE
        )
        s = re.sub(
            r"^(?:en\s+(?:el|la)\s+que|donde|que)\s+(?:se\s+)?(?:deba|tenga\s+que|haya\s+que|requiera|implique|involucre|pueda|necesite)\s+",
            "", s, flags=re.IGNORECASE
        )
        s = re.sub(
            r"^(?:de|del|para|en|con|sobre|un|una|uno|unos|unas|el|la|los|las)\s+",
            "", s, flags=re.IGNORECASE
        )
        s = re.sub(
            r"\s+(?:que|de|del|en|para|con|por|o|u|y|e|sobre)$",
            "", s, flags=re.IGNORECASE
        )
    return s.strip()

def extraer_subconsultas(texto: str) -> List[str]:
    """
    Descompone consultas compuestas o multi-rol en subconsultas individuales
    eliminando cláusulas relativas ('donde deba conducir' -> 'conducir').
    """
    if not texto:
        return []

    limpio = limpiar_frase_consulta(texto)

    # Separar por comas (evitando separar miles numéricos como 40,000) o conectores 'o', 'u' (evitando 'o mas', 'o superior')
    partes = re.split(r'(?<!\d)[,;](?!\d)|\s+(?:o|u)(?!\s+(?:m[aá]s|menos|mayor|superior|igual))\s+', limpio, flags=re.IGNORECASE)
    subconsultas = []

    for p in partes:
        p_clean = limpiar_frase_consulta(p)
        p_norm = normalizar_texto(p_clean)
        if len(p_clean) >= 3 and p_norm not in [normalizar_texto(s) for s in subconsultas]:
            subconsultas.append(p_clean)

    # Si se detectaron múltiples intenciones, incluir también la frase limpia completa
    if len(subconsultas) > 1 and limpio not in subconsultas and len(limpio) >= 3:
        subconsultas.append(limpio)
    elif not subconsultas and texto.strip():
        subconsultas = [limpio or texto.strip()]

    return subconsultas

def extraer_filtros_desde_texto(texto: str, payloads_existentes: dict = None) -> Tuple[dict, str]:
    """
    Extrae automáticamente entidades (salarios, modalidades) si no fueron enviados en los payloads
    y devuelve una versión limpia del texto sin los fragmentos de filtro.
    Soporta expresiones coloquiales como 'que ronde los 20k o mas', 'mayor a 40,000', 'entre 20k y 30k'.
    """
    filtros = dict(payloads_existentes or {})
    texto_limpio = texto

    tiene_o_mas = bool(re.search(r'\b(?:o\s+m[aá]s|o\s+superior|o\s+mayor|para\s+arriba|hacia\s+arriba|en\s+adelante)\b', texto, re.IGNORECASE))
    es_rango_aproximado = bool(re.search(r'\b(?:ronde|ronden|ronda|rondando|alrededor\s+de|cerca\s+de|aproximadamente)\b', texto, re.IGNORECASE))

    # Prefijo común para salario
    patron_prefijo = r'(?:(?:que\s+)?(?:ronde|ronden|ronda|rondando|alrededor\s+de|cerca\s+de|sobre|a\s+partir\s+de|mayor\s+a|superior\s+a|m[aá]s\s+de|desde|m[ií]nimo|sueldo(?:\s+de)?|salario(?:\s+de)?|pague|paguen|ganar|gane|ganen|pago(?:\s+de)?)\s*(?:los|las|el|la|un|unos)?\s*)'
    patron_sufijo = r'(?:\s*(?:pesos(?: dominicanos)?|dop|rd\$?|dolares|usd))?(?:\s*(?:mensuales|mensual|al\s+mes|por\s+mes|quincenal|quincenales))?(?:\s*(?:o\s+m[aá]s|o\s+superior|o\s+mayor|para\s+arriba|hacia\s+arriba|en\s+adelante))?'

    # 1. Rango explícito: 'entre 20k y 30k', 'de 20000 a 30000'
    m_rango = re.search(r'(?:entre|de)\s+(\d+(?:[.,]\d+)?)\s*(?:mil|k)?\s*(?:y|a|-)\s*(\d+(?:[.,]\d+)?)\s*(?:mil|k)\b' + patron_sufijo, texto, re.IGNORECASE)
    if m_rango:
        n1 = float(m_rango.group(1).replace(',', '.'))
        n2 = float(m_rango.group(2).replace(',', '.'))
        if n1 < 1000: n1 *= 1000
        if n2 < 1000: n2 *= 1000
        filtros['sueldo_min'] = int(min(n1, n2))
        filtros['sueldo_max'] = int(max(n1, n2))
        filtros['_target_sueldo'] = int(min(n1, n2))
        texto_limpio = re.sub(re.escape(m_rango.group(0)), '', texto_limpio, flags=re.IGNORECASE)

    # 2. Cifras con 'k' o 'mil' (ej: 'que ronde los 20k mensuales o mas', '20k', '30 mil')
    m_mil = re.search(rf'(?:{patron_prefijo})?(\d+(?:[.,]\d+)?)\s*(?:mil|k)\b{patron_sufijo}', texto, re.IGNORECASE)
    if m_mil and 'sueldo_min' not in filtros and 'sueldo' not in filtros:
        val = float(m_mil.group(1).replace(',', '.')) * 1000
        filtros['_target_sueldo'] = int(val)
        if es_rango_aproximado and not tiene_o_mas:
            # Si solo dice 'que ronde los 20k' (alrededor de 20k)
            filtros['sueldo_min'] = int(val * 0.85)
            filtros['sueldo_max'] = int(val * 1.30)
        else:
            # Si dice 'que ronde los 20k o mas' o 'mayor a 20k'
            filtros['sueldo_min'] = int(val)
        texto_limpio = re.sub(re.escape(m_mil.group(0)), '', texto_limpio, flags=re.IGNORECASE)

    # 3. Cifras numéricas completas: 'mayor a 40,000', '20000', '20.000'
    m_num = re.search(rf'(?:{patron_prefijo})?(\d{{1,3}}(?:[.,]\d{{3}})+|\d{{4,6}})\b{patron_sufijo}', texto, re.IGNORECASE)
    if m_num and 'sueldo_min' not in filtros and 'sueldo' not in filtros:
        num_str = re.sub(r'[.,]', '', m_num.group(1))
        val = int(num_str)
        if val >= 3000:
            filtros['_target_sueldo'] = val
            if es_rango_aproximado and not tiene_o_mas:
                filtros['sueldo_min'] = int(val * 0.85)
                filtros['sueldo_max'] = int(val * 1.30)
            else:
                filtros['sueldo_min'] = val
            texto_limpio = re.sub(re.escape(m_num.group(0)), '', texto_limpio, flags=re.IGNORECASE)

    # 4. Modalidad
    if re.search(r'\bremoto|teletrabajo|desde casa\b', texto, re.IGNORECASE):
        if 'modalidad' not in filtros:
            filtros['modalidad'] = 'Remoto'
        texto_limpio = re.sub(r'\bremoto|teletrabajo|desde casa\b', '', texto_limpio, flags=re.IGNORECASE)
    elif re.search(r'\bpresencial\b', texto, re.IGNORECASE):
        if 'modalidad' not in filtros:
            filtros['modalidad'] = 'Presencial'
        texto_limpio = re.sub(r'\bpresencial\b', '', texto_limpio, flags=re.IGNORECASE)
    elif re.search(r'\bhibrido\b', texto, re.IGNORECASE):
        if 'modalidad' not in filtros:
            filtros['modalidad'] = 'Híbrido'
        texto_limpio = re.sub(r'\bhibrido\b', '', texto_limpio, flags=re.IGNORECASE)

    # Limpiar frases residuales de salario, moneda y conectores
    texto_limpio = re.sub(
        r'\b(?:mensuales|mensual|al\s+mes|por\s+mes|quincenal|quincenales|o\s+m[aá]s|o\s+superior|o\s+mayor|para\s+arriba|hacia\s+arriba|en\s+adelante|de\s+sueldo|de\s+salario|sueldo|salario|pago|pesos(?: dominicanos)?|dop|rd\$?|dolares|usd|que\s+ronde(?:\s+los)?|que\s+ronden(?:\s+los)?|ronde(?:\s+los)?|ronden(?:\s+los)?|rondando(?:\s+los)?)\b',
        '',
        texto_limpio,
        flags=re.IGNORECASE
    )
    # Limpiar conectores finales o iniciales sueltos
    texto_limpio = re.sub(r'^\s*(?:que|de|del|en|para|con|por|sobre)\s+', '', texto_limpio, flags=re.IGNORECASE)
    texto_limpio = re.sub(r'\s+(?:que|de|del|en|para|con|por|sobre)\s*$', '', texto_limpio, flags=re.IGNORECASE)
    texto_limpio = re.sub(r'\s+', ' ', texto_limpio).strip()
    return filtros, texto_limpio

def es_consulta_generica(texto: str) -> bool:
    """Verifica si el texto solo contiene palabras genéricas de búsqueda sin un rol o profesión específica."""
    palabras_genericas = {
        # Pronombres, determinantes y artículos
        'el', 'la', 'los', 'las', 'un', 'una', 'uno', 'unos', 'unas', 'lo', 'le', 'les',
        'este', 'esta', 'estos', 'estas', 'ese', 'esa', 'esos', 'esas', 'aquel', 'aquella',
        'algo', 'algun', 'alguna', 'alguno', 'algunas', 'algunos', 'algua',
        'cualquier', 'cualquiera', 'cualesquiera', 'todo', 'toda', 'todos', 'todas',
        'alguien', 'nadie', 'nada', 'otro', 'otra', 'otros', 'otras',

        # Verbos de intención y búsqueda
        'busco', 'busca', 'buscan', 'buscar', 'buscando',
        'deseo', 'desea', 'desean', 'desear', 'deseando',
        'quiero', 'quiere', 'quieren', 'querer', 'quisiera',
        'necesito', 'necesita', 'necesitan', 'necesitar', 'necesitando',
        'gustaria', 'interesa', 'interesan', 'interesar',
        'pague', 'paguen', 'paga', 'pagar', 'gane', 'ganen', 'ganar',
        'cobre', 'cobren', 'cobra', 'cobrar',

        # Sustantivos genéricos de trabajo
        'vacante', 'vacantes', 'empleo', 'empleos', 'trabajo', 'trabajos',
        'oferta', 'ofertas', 'puesto', 'puestos', 'posicion', 'posiciones',
        'plaza', 'plazas', 'labor', 'labores', 'chamba', 'oportunidad', 'oportunidades',

        # Salarios y dinero
        'sueldo', 'sueldos', 'salario', 'salarios', 'pago', 'pagos', 'remuneracion',
        'dinero', 'pesos', 'dop', 'rd', 'dolar', 'dolares', 'usd',

        # Temporalidad
        'mensual', 'mensuales', 'mes', 'meses', 'quincenal', 'quincenales', 'quincena',
        'diario', 'diaria', 'diarios', 'diarias', 'semanal', 'semanales', 'semana',
        'hora', 'horas',

        # Comparativos, rangos y aproximaciones
        'mayor', 'mayores', 'menor', 'menores', 'mas', 'menos', 'minimo', 'minima', 'maximo', 'maxima',
        'superior', 'superiores', 'inferior', 'inferiores', 'igual', 'iguales',
        'ronde', 'ronden', 'ronda', 'rondando', 'cerca', 'alrededor', 'sobre', 'partir',
        'aproximado', 'aproximada', 'aproximadamente', 'arriba', 'abajo', 'adelante', 'atras',

        # Calificativos comunes
        'bueno', 'buena', 'buenos', 'buenas', 'bien', 'mejor', 'mejores',
        'excelente', 'excelentes', 'decente', 'decentes',

        # Preposiciones y conectores
        'que', 'de', 'del', 'en', 'para', 'con', 'sin', 'por', 'a', 'al',
        'hacia', 'desde', 'hasta', 'o', 'u', 'y', 'e', 'como'
    }
    tokens = [normalizar_texto(w) for w in re.findall(r'\b\w+\b', texto)]
    roles = [t for t in tokens if t not in palabras_genericas and len(t) >= 3]
    return len(roles) == 0

def FieldCondition_Dinamico(payloads):
    Tipos = [
        "Puesto",
        "Modalidad",
        "Horario",
        "Ubicacion",
        "Descripcion",
        "Beneficios",
        "Palabras_clave"
    ]

    Guardar_Fieldconditions = []
    if not isinstance(payloads, dict):
        return Guardar_Fieldconditions

    for p, val in payloads.items():
        if val is None or val == "":
            continue

        p_str = str(p).lower()
        if p_str.startswith('_'):
            continue
        
        # Filtros numéricos de salario (soportando números con comas o puntos, ej: '40,000')
        if p_str == 'sueldo_max':
            try:
                num = int(re.sub(r'[.,]', '', str(val)))
                if num > 0:
                    Guardar_Fieldconditions.append(
                        FieldCondition(key='Sueldo', range=Range(lte=num))
                    )
            except (ValueError, TypeError):
                pass

        elif p_str in ('sueldo_min', 'sueldo'):
            try:
                num = int(re.sub(r'[.,]', '', str(val)))
                if num > 0:
                    Guardar_Fieldconditions.append(
                        FieldCondition(key='Sueldo', range=Range(gte=num))
                    )
            except (ValueError, TypeError):
                pass

        else:
            for i in Tipos:
                if p_str == i.lower() or p_str in i.lower():
                    if isinstance(val, list):
                        Guardar_Fieldconditions.append(
                            FieldCondition(
                                key=i,
                                match=MatchAny(any=val)
                            )
                        )
                    else:
                        Guardar_Fieldconditions.append(
                            FieldCondition(
                                key=i,
                                match=MatchValue(value=val)
                            )
                        )
                    break
                
    return Guardar_Fieldconditions

RE_GENERICO_VEHICULOS = r"\b(?:conducir|conduzca|conduccion|manejar|maneje|manejando|veh[ií]culos?|carros?|autom[oó]vil(?:es)?|transporte)\b"

def obtener_expansiones_semanticas(texto: str) -> Tuple[List[str], List[str]]:
    """
    Expande intenciones conceptuales o amplias a roles y palabras clave asociadas
    (por ejemplo: 'conducir' -> 'chofer', 'montacargas', 'delivery motor', 'transporte').
    """
    subqs = []
    kw_boost = []

    # 1. Conducción amplia o relacionada a vehículos
    if re.search(RE_GENERICO_VEHICULOS, texto, re.IGNORECASE):
        subqs.extend([
            "chofer conductor",
            "operador montacargas",
            "delivery mensajero motor",
            "conductor transporte"
        ])
        kw_boost.extend([
            "chofer", "chófer", "conductor", "delivery", "mensajero", "transporte",
            "montacarga", "montacargas", "conducir", "manejar", "minibus", "vehiculo",
            "vehículo", "licencia", "motor"
        ])

    # 2. Roles específicos de transporte y maquinaria móvil
    if re.search(r"\b(?:montacargas?|montacarguistas?)\b", texto, re.IGNORECASE):
        if "operador montacargas" not in subqs:
            subqs.append("operador montacargas")
        kw_boost.extend(["montacarga", "montacargas"])

    if re.search(r"\b(?:ch[oó]fer(?:es)?|conductor(?:es|as?)?)\b", texto, re.IGNORECASE):
        if "chofer conductor" not in subqs:
            subqs.append("chofer conductor")
        kw_boost.extend(["chofer", "chófer", "conductor"])

    if re.search(r"\b(?:delivery|mensajer[ao]s?|motoristas?|repartidor(?:es)?)\b", texto, re.IGNORECASE):
        if "delivery mensajero motor" not in subqs:
            subqs.append("delivery mensajero motor")
        kw_boost.extend(["delivery", "mensajero", "motor"])

    # 3. Tecnología / Programación
    if re.search(r"\b(?:programar|programaci[oó]n|desarrollo\s+software|developer|coding)\b", texto, re.IGNORECASE):
        subqs.extend(["desarrollador de software", "programador de sistemas"])
        kw_boost.extend(["desarrollador", "programador", "software", "developer", "sistemas"])

    # 4. Cocina / Gastronomía
    if re.search(r"\b(?:cocinar|gastronom[ií]a)\b", texto, re.IGNORECASE):
        subqs.extend(["cocinero chef", "encargado de cocina"])
        kw_boost.extend(["cocina", "cocinero", "chef", "panaderia", "reposteria"])

    return subqs, list(dict.fromkeys(kw_boost))

def calcular_keyword_boost(payload: dict, query_original: str, sub_q: str, keywords_extra: list = None) -> float:
    """
    Otorga un impulso (Boost) léxico y contextual si hay coincidencia directa
    en el título del puesto, palabras clave o descripción relevante.
    """
    if not payload:
        return 0.0

    puesto = payload.get('Puesto', '')
    desc = payload.get('Descripcion', '')
    palabras_clave = payload.get('Palabras_clave', [])
    palabras_str = " ".join([str(k) for k in palabras_clave]) if isinstance(palabras_clave, list) else str(palabras_clave or '')

    puesto_n = normalizar_texto(puesto)
    desc_n = normalizar_texto(desc)
    pc_n = normalizar_texto(palabras_str)

    boost = 0.0

    # 1. Boost fuerte por coincidencia directa con la consulta del usuario
    palabras_query = [normalizar_texto(w) for w in query_original.split() if len(w) > 3]
    if any(w in puesto_n for w in palabras_query):
        boost += 0.16
    elif any(w in desc_n for w in palabras_query):
        boost += 0.08

    # 2. Boost por coincidencia con la subconsulta evaluada
    palabras_sub = [normalizar_texto(w) for w in sub_q.split() if len(w) > 3]
    if any(w in puesto_n for w in palabras_sub):
        boost += 0.10
    elif any(w in desc_n for w in palabras_sub):
        boost += 0.05

    # 3. Boost secundario por palabras clave del dominio
    if keywords_extra:
        if any(k in puesto_n for k in keywords_extra):
            boost += 0.06
        if any(k in pc_n or k in desc_n for k in keywords_extra):
            boost += 0.03

    return min(boost, 0.22)

def generar_embedding_consulta(texto: str) -> list:
    """Genera el embedding usando el prefijo de búsqueda asimétrica de nomic."""
    prompt_query = f"search_query: {texto.strip()}"
    res = embed(model="nomic-embed-text-v2-moe:latest", input=prompt_query)
    return res['embeddings'][0]

def buscar(datos):
    """
    Búsqueda semántica robusta y precisa:
    - Extracción de entidades de filtros en lenguaje natural (sueldos, modalidades).
    - Detección de consultas basadas puramente en filtros (ej: 'mayor a 40,000') para retorno directo sin penalizar por similitud de texto.
    - Descomposición de consultas compuestas (Multi-Intent).
    - Expansión semántica inteligente de dominios conceptuales (ej: 'conducir' -> 'chofer', 'montacargas', 'delivery').
    - Prefijo search_query: para nomic-embed-text.
    - Boost léxico y contextual en título y descripción de puesto.
    - Filtro adaptativo por caída relativa (Score Dropoff) para eliminar ruido.
    - Deduplicación y preservación del mejor score.
    """
    if isinstance(datos, str):
        texto = datos
        payloads_raw = {}
    elif isinstance(datos, dict):
        texto = datos.get('texto', '')
        payloads_raw = datos.get('payloads', {})
    else:
        texto = getattr(datos, 'texto', '')
        payloads_raw = getattr(datos, 'payloads', {})

    if not texto and not payloads_raw:
        return QueryResponse(points=[])

    try:
        # 1. Enriquecer filtros desde el texto si faltaban y obtener texto limpio
        payloads, texto_limpio = extraer_filtros_desde_texto(texto, payloads_raw)
        condiciones = FieldCondition_Dinamico(payloads)
        query_filter = Filter(must=condiciones) if condiciones else None

        if condiciones:
            print(f"⚙️ Filtros activos: {condiciones}")

        # 2. Verificar si es una consulta puramente basada en filtros (sin profesión o cargo específico)
        es_generica = es_consulta_generica(texto_limpio)

        if es_generica and query_filter:
            print(f"🔍 Búsqueda basada en filtros ({texto}): recuperando vacantes que cumplen las condiciones...")
            puntos_scroll, _ = cliente.scroll(
                collection_name="vacantes_prueba",
                scroll_filter=query_filter,
                with_payload=True,
                limit=50
            )

            target_sueldo = payloads.get('_target_sueldo')
            if target_sueldo:
                # Si el usuario indicó una cifra objetivo (ej: 'que ronde los 20k' o '20k o mas'),
                # ordenar por cercanía al sueldo objetivo para que las ofertas más pertinentes aparezcan primero
                puntos_scroll = sorted(
                    puntos_scroll,
                    key=lambda x: abs((x.payload.get('Sueldo', 0) if x.payload else 0) - target_sueldo)
                )
            elif 'sueldo_min' in payloads:
                # Si hay sueldo mínimo sin target específico, ordenar ascendente desde el mínimo
                puntos_scroll = sorted(
                    puntos_scroll,
                    key=lambda x: x.payload.get('Sueldo', 0) if x.payload else 0
                )
            else:
                # Por defecto ordenar descendente (sueldos más altos primero)
                puntos_scroll = sorted(
                    puntos_scroll,
                    key=lambda x: x.payload.get('Sueldo', 0) if x.payload else 0,
                    reverse=True
                )

            puntos_finales = [
                ScoredPoint(
                    id=p.id,
                    version=1,
                    score=1.0,
                    payload=p.payload,
                    vector=None
                )
                for p in puntos_scroll
            ]
            print(f"✅ Vacantes retenidas por filtro: {len(puntos_finales)}")
            return QueryResponse(points=puntos_finales)

        # 3. Descomponer consultas y expandir intenciones semánticas
        texto_a_buscar = texto_limpio if texto_limpio.strip() else texto
        subconsultas_base = extraer_subconsultas(texto_a_buscar)
        subconsultas_extra, keywords_extra = obtener_expansiones_semanticas(texto_a_buscar)

        subconsultas = list(dict.fromkeys(subconsultas_base + subconsultas_extra))
        print(f"🔍 Búsqueda: '{texto}' | Subconsultas ({len(subconsultas)}): {subconsultas}")
        if keywords_extra:
            print(f"🎯 Dominio semántico detectado ({len(keywords_extra)} keywords)")

        puntos_acumulados = {}

        # 4. Ejecutar búsqueda vectorial para cada subconsulta
        umbral_entrada = 0.15 if query_filter else 0.25

        for sub_q in subconsultas:
            query_vector = generar_embedding_consulta(sub_q)
            qdrant_res = cliente.query_points(
                collection_name="vacantes_prueba",
                query=query_vector,
                query_filter=query_filter,
                with_payload=True,
                score_threshold=umbral_entrada,
                limit=20
            )

            for p in qdrant_res.points:
                boost = calcular_keyword_boost(p.payload, texto_a_buscar, sub_q, keywords_extra)
                score_final = p.score + boost

                # Si ya existía este punto por otra subconsulta, conservar la puntuación más alta
                if p.id not in puntos_acumulados or score_final > puntos_acumulados[p.id]['score']:
                    p_copy = ScoredPoint(
                        id=p.id,
                        version=p.version,
                        score=round(score_final, 4),
                        payload=p.payload,
                        vector=p.vector
                    )
                    puntos_acumulados[p.id] = {
                        'point': p_copy,
                        'score': score_final,
                        'matched_subquery': sub_q
                    }

        if not puntos_acumulados:
            print("ℹ️ No se encontraron vacantes para la búsqueda.")
            return QueryResponse(points=[])

        # 5. Ordenar por score final descendente
        ranking = sorted(puntos_acumulados.values(), key=lambda x: x['score'], reverse=True)
        top_score = ranking[0]['score']

        # 6. Umbral de caída relativa (Score Dropoff)
        if query_filter:
            umbral_corte = max(top_score * 0.55, 0.20)
        else:
            umbral_corte = max(top_score * 0.60, 0.28)

        print(f"📊 Top Score: {top_score:.4f} | Umbral adaptativo: {umbral_corte:.4f}")

        puntos_filtrados = [item['point'] for item in ranking if item['score'] >= umbral_corte]
        print(f"✅ Vacantes retenidas: {len(puntos_filtrados)} (de {len(ranking)} evaluadas)")

        return QueryResponse(points=puntos_filtrados)

    except Exception as e:
        print(f"❌ Error en buscar: {e}")
        return QueryResponse(points=[])

if __name__ == '__main__':
    print("=" * 70)
    print("TEST 1: Consulta de sueldo en lenguaje natural ('mayor a 40,000 mensuales')")
    print("=" * 70)
    res1 = buscar({
        "texto": "Busco algua vacante que ronde los 20k mensuales o mas",
        "payloads": {}
    })
    for p in res1.points:
        print(f"  • [{p.score:.4f}] {p.payload.get('Puesto')} | Sueldo: RD$ {p.payload.get('Sueldo')}")

    print("\n" + "=" * 70)
    print("TEST 2: Consulta multi-rol ('almacen, chofer o asesor de negocio')")
    print("=" * 70)
    res2 = buscar({
        "texto": "Busco ser encargado de algun almacen, chofer o algun asesor de negocio",
        "payloads": {}
    })
    for p in res2.points:
        print(f"  • [{p.score:.4f}] {p.payload.get('Puesto')} | Sueldo: RD$ {p.payload.get('Sueldo')}")

    print("\n" + "=" * 70)
    print("TEST 3: Consulta referida a conducción / vehículo ('donde deba conducir')")
    print("=" * 70)
    res3 = buscar({
        "texto": "Busco una vacante donde deba conducir",
        "payloads": {}
    })
    for p in res3.points:
        print(f"  • [{p.score:.4f}] {p.payload.get('Puesto')} | Sueldo: RD$ {p.payload.get('Sueldo')}")

    print("\n" + "=" * 70)
    print("TEST 4: Consulta sin coincidencia (Descarte total de falsos positivos)")
    print("=" * 70)
    res4 = buscar({
        "texto": "programador python junior en guayaquil",
        "payloads": {}
    })
    if not res4.points:
        print("  ✔ Correcto: 0 falsos positivos encontrados.")
    else:
        for p in res4.points:
            print(f"  • [{p.score:.4f}] {p.payload.get('Puesto')}")