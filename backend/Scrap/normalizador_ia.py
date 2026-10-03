#!/usr/bin/env python3
"""
Módulo de Normalización de Vacantes con Inteligencia Artificial (Ollama)
========================================================================
Este módulo toma las vacantes extraídas por los scrapers (TrabajosDiarios, TuEmpleoRD, etc.),
utiliza un modelo de lenguaje en Ollama local (por ejemplo, 'maternion/ling-3.0-tiny:8b' o
'lfm2.5-thinking:latest') para:
  1. Normalizar y estandarizar todos los campos (puesto, empresa, ubicación,
     modalidad, horario, salario, sexo, contactos, requisitos y beneficios).
  2. Redactar una descripción profesional, rica y estructurada creada por la IA
     acorde a lo que expone la vacante.
"""

import os
import sys
import re
import json
import time
import argparse
from typing import List, Dict, Any, Optional

try:
    from curl_cffi import requests
except ImportError:
    import requests


class Colors:
    HEADER = '\033[95m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'


def log_info(msg: str):
    print(f"{Colors.CYAN}ℹ [INFO IA]{Colors.RESET} {msg}")


def log_success(msg: str):
    print(f"{Colors.GREEN}✔ [ÉXITO IA]{Colors.RESET} {msg}")


def log_warning(msg: str):
    print(f"{Colors.YELLOW}⚠ [ALERTA IA]{Colors.RESET} {msg}")


def log_error(msg: str):
    print(f"{Colors.RED}✖ [ERROR IA]{Colors.RESET} {msg}")


def extraer_empresa_de_dominio_email(email: str) -> Optional[str]:
    """
    Analiza el correo electrónico y su dominio para identificar el nombre de la empresa contratante.
    Descarta proveedores públicos genéricos (gmail, hotmail, etc.).
    Ejemplos:
      'contabilidad@almonteyco.com' -> 'Almonteyco'
      'rrhh@cepm.com.do' -> 'CEPM'
      'empleos@bhd.com.do' -> 'BHD'
      'talento@grupomarca.do' -> 'Grupomarca'
      'contacto@hotel-colonial.com' -> 'Hotel Colonial'
    """
    if not email or "@" not in email:
        return None

    email = email.strip()
    partes = email.split("@")
    if len(partes) != 2:
        return None

    usuario, dominio = partes[0].lower(), partes[1].lower()

    dominios_genericos = {
        "gmail.com", "hotmail.com", "yahoo.com", "outlook.com", "live.com",
        "icloud.com", "protonmail.com", "mail.com", "zoho.com", "aol.com",
        "yandex.com", "gmx.com", "tuempleord.do", "trabajosdiarios.com",
        "empleos.com", "interbank.com"
    }

    if dominio in dominios_genericos:
        return None

    # Quitar extensiones de dominio comunes
    d_limpio = re.sub(r'\.(com|org|net|edu|gob)?(\.do|\.es|\.co|\.mx|\.us|\.io)?$', '', dominio)
    d_partes = d_limpio.split(".")
    
    # Descartar subdominios genéricos
    subdominios_a_ignorar = {"mail", "rrhh", "webmail", "reclutamiento", "jobs", "portal", "empleos", "talent", "talento"}
    d_partes = [p for p in d_partes if p not in subdominios_a_ignorar]
    
    if not d_partes:
        return None

    nombre_crudo = d_partes[-1]

    # Si es muy corto (acrónimo como BHD, CGM, CEPM), poner en mayúsculas
    if len(nombre_crudo) <= 4 and nombre_crudo.isalpha():
        return nombre_crudo.upper()

    # Si contiene separadores como guiones
    if "-" in nombre_crudo or "_" in nombre_crudo:
        palabras = re.split(r'[-_]', nombre_crudo)
        return " ".join(p.capitalize() for p in palabras if p)

    return nombre_crudo.capitalize()


class NormalizadorIAVacantes:
    """Gestiona la normalización de vacantes y generación de descripciones usando Ollama local."""

    def __init__(
        self,
        host: str = "http://localhost:11434",
        preferred_model: Optional[str] = "maternion/ling-3.0-tiny:8b"
    ):
        self.host = host.rstrip('/')
        self.preferred_model = preferred_model
        self.model = self._select_model(preferred_model)

    def _select_model(self, preferred: Optional[str] = None) -> str:
        """Detecta modelos instalados en Ollama y selecciona el más apto para razonamiento."""
        try:
            res = requests.get(f"{self.host}/api/tags", timeout=6)
            res.raise_for_status()
            data = res.json()
            models = [m['name'] for m in data.get('models', [])]

            if not models:
                log_warning("No se encontraron modelos instalados en Ollama. Verifica 'ollama list'.")
                return preferred or "maternion/ling-3.0-tiny:8b"

            if preferred:
                for m in models:
                    if preferred in m or m.startswith(preferred):
                        log_info(f"Usando modelo de IA: {Colors.BOLD}{m}{Colors.RESET}")
                        return m

            # Buscar modelo que no sea de embeddings
            for m in models:
                if "embed" not in m.lower():
                    log_info(f"Modelo de IA detectado automáticamente: {Colors.BOLD}{m}{Colors.RESET}")
                    return m

            return models[0]
        except Exception as e:
            log_warning(f"No se pudo consultar lista de modelos de Ollama en {self.host}: {e}")
            return preferred or "maternion/ling-3.0-tiny:8b"

    def _limpiar_respuesta_llm(self, raw_text: str) -> str:
        """Limpia etiquetas de pensamiento <think>...</think> o markdown redundante."""
        if not raw_text:
            return ""
        
        # Eliminar bloques think
        if "</think>" in raw_text:
            raw_text = raw_text.split("</think>")[-1].strip()
        else:
            raw_text = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL).strip()

        # Si viene envuelto en bloque ```json ... ```
        match_block = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_text, flags=re.DOTALL)
        if match_block:
            return match_block.group(1).strip()

        # Si contiene JSON en cualquier parte
        inicio = raw_text.find('{')
        fin = raw_text.rfind('}')
        if inicio != -1 and fin != -1 and fin > inicio:
            return raw_text[inicio:fin + 1].strip()

        return raw_text.strip()

    def normalizar_vacante(self, vacante: Dict[str, Any], timeout: int = 120) -> Dict[str, Any]:
        """
        Envía los datos de la vacante a la IA para normalizar todos sus campos
        y generar una descripción profesional coherente.
        """
        # Extraer información actual disponible
        puesto_orig = vacante.get("puesto") or vacante.get("titulo") or "Vacante no especificada"
        empresa_orig = vacante.get("empresa") or "Confidencial"
        ubicacion_orig = vacante.get("ubicacion") or vacante.get("ciudad") or "República Dominicana"
        salario_orig = vacante.get("salario_mostrado") or ""
        resumen_orig = vacante.get("resumen_corto") or ""
        
        detalles = vacante.get("detalles", {})
        desc_cruda = (
            detalles.get("descripcion_completa")
            or vacante.get("descripcion")
            or resumen_orig
            or ""
        )
        req_orig = detalles.get("requisitos_educativos") or ""
        modalidad_orig = vacante.get("modalidad") or ""
        horario_orig = vacante.get("horario") or ""

        # Detección y análisis del correo electrónico
        email_vacante = (vacante.get("email") or "").strip()
        if not email_vacante or email_vacante.lower() in ["no especificado", "desconocido", "none", "null"]:
            m_email = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', desc_cruda)
            if m_email:
                email_vacante = m_email.group(0).strip()
                vacante["email"] = email_vacante

        # Analizar si el dominio del email indica la empresa
        empresa_sugerida_email = extraer_empresa_de_dominio_email(email_vacante)

        contactos_previos = f"Teléfono: {vacante.get('telefono', '')} | Email: {email_vacante or vacante.get('email', '')}"

        # ─────────────────────────────────────────────────────────────────
        # PROMPT ULTRA-PRECISO: Cero Alucinación, Solo Datos del Texto
        # ─────────────────────────────────────────────────────────────────
        prompt = (
            "Eres un analista senior de Recursos Humanos especializado en el mercado laboral de República Dominicana.\n"
            "Tu ÚNICA tarea es LEER el texto de la vacante y extraer/normalizar los datos que REALMENTE aparecen.\n\n"
            
            "═══════════════════════════════════════════════════════════════\n"
            "REGLAS ABSOLUTAS (VIOLARLAS ES INACEPTABLE):\n"
            "═══════════════════════════════════════════════════════════════\n\n"
            
            "▶ REGLA 1 - CERO INVENCIÓN: Si un dato NO aparece en el texto, escribe EXACTAMENTE 'Desconocido'. "
            "NUNCA inventes nombres, direcciones, salarios, empresas ni teléfonos.\n\n"
            
            "▶ REGLA 2 - PUESTO: Copia el cargo TAL CUAL aparece en la oferta, solo limpiando formato. "
            "Ejemplos correctos: 'Camarero', 'Chofer Categoría 3', 'Asistente Contable'. "
            "PROHIBIDO agregar prefijos como 'Encargado de', 'Gerente de', 'Director de' si NO están en el texto original.\n\n"
            
            "▶ REGLA 3 - EMPRESA (MUY IMPORTANTE - REVISA EL CORREO): La empresa es el NOMBRE DEL NEGOCIO que está contratando.\n"
            "  * OBLIGATORIO: Revisa con especial atención el EMAIL de contacto. Si el correo tiene un dominio corporativo propio "
            "(por ejemplo: 'contabilidad@almonteyco.com', 'rrhh@cepm.com.do', 'empleos@bhd.com.do', 'talento@grupomarca.do'), "
            "el dominio indica directamente el nombre de la empresa ('Almonteyco', 'CEPM', 'BHD', 'Grupomarca'). "
            "Si en el texto no se menciona explícitamente otro nombre de empresa, ¡DEBES usar el nombre del dominio corporativo como empresa!\n"
            "  * Ignora dominios públicos gratuitos (gmail.com, hotmail.com, yahoo.com, outlook.com, etc.).\n"
            "  * Si NO hay nombre de empresa real en el texto ni dominio corporativo → pon 'Confidencial'. NUNCA uses el nombre del puesto como empresa.\n\n"
            
            "▶ REGLA 4 - UBICACIÓN: Extrae la ubicación MÁS PRECISA del texto (sector, barrio, avenida). "
            "Ejemplo: 'Sector Renacimiento, Santo Domingo', 'Herrera, Santo Domingo Oeste'. Si no hay ubicación → 'Desconocido'.\n\n"
            
            "▶ REGLA 5 - MODALIDAD: Solo 3 valores posibles: 'Presencial', 'Remoto' o 'Híbrido'. Si no se indica → 'Presencial'.\n\n"
            
            "▶ REGLA 6 - SALARIO: Solo indica montos que aparezcan EXPLÍCITAMENTE en el texto (ej: 'RD$ 25,000'). "
            "Si no hay cifras de salario → salario_mostrado='No especificado' y sueldo_num=0. NUNCA inventes cifras.\n\n"
            
            "▶ REGLA 7 - CONTACTOS: Solo incluye teléfono/email si aparecen LITERALMENTE en el texto o contactos previos. Si no → 'No especificado'.\n\n"
            
            "▶ REGLA 8 - DESCRIPCIÓN: Redacta una descripción profesional y atractiva basada FIELMENTE en lo que dice la oferta. "
            "Incluye: responsabilidades, perfil buscado, condiciones laborales y beneficios mencionados. Mínimo 3-4 oraciones.\n\n"
            
            "═══════════════════════════════════════════════════════════════\n"
            "DATOS CRUDOS DE LA VACANTE A NORMALIZAR:\n"
            "═══════════════════════════════════════════════════════════════\n"
            f"Puesto detectado: {puesto_orig}\n"
            f"Empresa detectada: {empresa_orig}\n"
            f"Ubicación detectada: {ubicacion_orig}\n"
            f"Salario detectado: {salario_orig or 'No indicado'}\n"
            f"Modalidad detectada: {modalidad_orig or 'No indicada'}\n"
            f"Horario detectado: {horario_orig or 'No indicado'}\n"
            f"Teléfono: {vacante.get('telefono', 'No indicado')}\n"
            f"Email de contacto: {email_vacante or 'No indicado'}\n"
            f"Empresa sugerida por dominio de email: {empresa_sugerida_email or 'Ninguna (proveedor público o no disponible)'}\n"
            f"Requisitos previos: {req_orig or 'No indicados'}\n"
            f"Texto completo de la oferta:\n<<<\n{desc_cruda[:2500]}\n>>>\n\n"
            
            "═══════════════════════════════════════════════════════════════\n"
            "Responde SOLO con un JSON válido (sin texto adicional) con esta estructura:\n"
            "{\n"
            '  "puesto": "Cargo limpio y formal",\n'
            '  "empresa": "Nombre real del negocio o Confidencial",\n'
            '  "ubicacion": "Sector/Barrio, Ciudad lo más preciso posible",\n'
            '  "provincia": "Provincia de RD",\n'
            '  "ciudad": "Municipio o ciudad",\n'
            '  "modalidad": "Presencial | Remoto | Híbrido",\n'
            '  "horario": "Horario de trabajo",\n'
            '  "salario_mostrado": "Monto textual o No especificado",\n'
            '  "sueldo_num": 0,\n'
            '  "sexo": "Masculino | Femenino | Indistinto",\n'
            '  "telefono": "Número o No especificado",\n'
            '  "email": "Email o No especificado",\n'
            '  "requisitos": ["requisito1", "requisito2"],\n'
            '  "beneficios": ["beneficio1", "beneficio2"],\n'
            '  "palabras_clave": ["palabra1", "palabra2"],\n'
            '  "descripcion": "Descripción profesional redactada por ti"\n'
            "}"
        )

        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "think": False,
            "options": {
                "temperature": 0.05  # Mínima creatividad para máxima precisión
            }
        }

        try:
            res = requests.post(url, json=payload, timeout=timeout)
            res.raise_for_status()
            res_data = res.json()
            raw_response = res_data.get("response") or res_data.get("thinking") or ""
            cleaned_json_text = self._limpiar_respuesta_llm(raw_response)

            data_ia = json.loads(cleaned_json_text)

            # ─── POST-PROCESAMIENTO: Sanitización de datos de la IA ───

            # 1. PUESTO: evitar prefijos inventados
            puesto_norm = (data_ia.get("puesto") or puesto_orig).strip()
            prefijos_prohibidos = ["encargado de ", "gerente de ", "director de ", "jefe de "]
            for prefijo in prefijos_prohibidos:
                if puesto_norm.lower().startswith(prefijo) and prefijo.split()[0] not in puesto_orig.lower():
                    puesto_norm = puesto_norm[len(prefijo):].strip().capitalize()
                    break

            # 2. EMPRESA: Protección contra alucinaciones y análisis de dominio de correo
            empresa_norm = (data_ia.get("empresa") or "").strip()
            # Limpiar extensiones de dominio si la IA devolvió el dominio literal (ej: almonteyco.com -> Almonteyco)
            if empresa_norm.lower().endswith((".com", ".do", ".net", ".org", ".com.do")):
                empresa_norm = re.sub(r'\.(com|org|net|edu|gob)?(\.do|\.es|\.co|\.mx)?$', '', empresa_norm, flags=re.IGNORECASE).strip().capitalize()

            empresa_lower = empresa_norm.lower()

            terminos_cargo = [
                "camarero", "camarera", "camareros", "camareras", "chofer", "chófer", "choferes",
                "vendedor", "vendedora", "vendedores", "cajero", "cajera", "cajeros", "asistente",
                "secretaria", "secretario", "mantenimiento", "steward", "empleado", "empleada",
                "cocinero", "cocinera", "analista", "asesor", "asesora", "consultor",
                "consultora", "pasante", "gerente", "supervisor", "supervisora", "operador",
                "operadora", "recepcionista", "mensajero", "repartidor", "conserje",
                "vigilante", "guardia", "limpieza", "bartender", "barista", "mesero",
                "mesera", "auxiliar", "auxiliares", "técnico", "tecnico", "mecánico", "mecanico",
                "electricista", "plomero", "pintor", "albañil", "albanil",
                "encargado", "encargada", "ayudante", "subgerente", "coordinador", "coordinadora",
                "ejecutivo", "ejecutiva", "despachador", "despachadora", "operario", "operaria",
                "puesto", "cargo", "empleo", "vacante", "profesional", "especialista",
                "empresa de servicios", "empresa", "no especificado", "no especificada",
                "none", "null", "desconocido", "desconocida", "n/a", "confidencial"
            ]

            palabras_puesto = [w.lower() for w in re.findall(r'\b\w+\b', puesto_norm)]
            es_cargo = (
                empresa_lower == puesto_norm.lower()
                or any(empresa_lower == t for t in terminos_cargo)
                or any(empresa_lower.startswith(t + " ") for t in terminos_cargo)
                or any(empresa_lower.endswith(" " + t) for t in terminos_cargo)
                or (len(palabras_puesto) > 0 and empresa_lower == palabras_puesto[0])
                or (len(palabras_puesto) > 1 and empresa_lower == f"{palabras_puesto[0]} {palabras_puesto[1]}")
                or empresa_lower in ["", "no especificado", "desconocido", "none", "null"]
            )

            if es_cargo:
                # 1ro: Si el correo tiene un dominio corporativo identificado, usarlo
                if empresa_sugerida_email:
                    empresa_norm = empresa_sugerida_email
                    log_info(f"Empresa inferida por dominio de email corporativo: '{empresa_norm}' ({email_vacante})")
                # 2do: Intentar recuperar desde datos originales del scraper
                elif empresa_orig and empresa_orig.lower() not in ["", "confidencial", "no especificado", "desconocido"] \
                        and not any(empresa_orig.lower() == t for t in terminos_cargo) \
                        and empresa_orig.lower() != puesto_norm.lower():
                    empresa_norm = empresa_orig
                else:
                    empresa_norm = "Confidencial"
            elif empresa_norm.lower() in ["confidencial", "desconocido", "no especificado", "none", "null", ""] and empresa_sugerida_email:
                empresa_norm = empresa_sugerida_email
                log_info(f"Empresa inferida por dominio de email corporativo: '{empresa_norm}' ({email_vacante})")

            # 3. UBICACIÓN, PROVINCIA, CIUDAD
            ubicacion_norm = (data_ia.get("ubicacion") or ubicacion_orig or "República Dominicana").strip()
            if ubicacion_norm.lower() in ["desconocido", "desconocida", "no especificado", "none", "null"]:
                ubicacion_norm = ubicacion_orig or "República Dominicana"
            provincia_norm = (data_ia.get("provincia") or vacante.get("provincia") or ubicacion_norm).strip()
            ciudad_norm = (data_ia.get("ciudad") or vacante.get("ciudad") or ubicacion_norm).strip()

            # 4. MODALIDAD (estricta)
            modalidad_norm = (data_ia.get("modalidad") or modalidad_orig or "Presencial").strip()
            if modalidad_norm not in ["Presencial", "Remoto", "Híbrido"]:
                modalidad_norm = "Presencial"

            # 5. HORARIO
            horario_norm = (data_ia.get("horario") or horario_orig or "Tiempo Completo").strip()

            # 6. SALARIO
            salario_norm = (data_ia.get("salario_mostrado") or salario_orig or "No especificado").strip()
            sueldo_num = data_ia.get("sueldo_num", 0)
            if not isinstance(sueldo_num, (int, float)) or sueldo_num <= 0:
                sueldo_num = vacante.get("sueldo", 0)

            # 7. SEXO
            sexo_norm = (data_ia.get("sexo") or vacante.get("sexo", "Indistinto")).strip()
            if sexo_norm.lower() in ["", "null", "none", "no especificado", "desconocido"]:
                sexo_norm = "Indistinto"

            # 8. CONTACTOS: priorizar datos reales del scraper sobre la IA
            tel_norm = (data_ia.get("telefono") or "").strip()
            if not tel_norm or tel_norm.lower() in ["no especificado", "desconocido", "none", "null", ""]:
                tel_norm = vacante.get("telefono", "No especificado")
            if tel_norm.lower() in ["no especificado", ""] and vacante.get("telefono") and vacante["telefono"] != "No especificado":
                tel_norm = vacante["telefono"]

            email_norm = (data_ia.get("email") or "").strip()
            if not email_norm or email_norm.lower() in ["no especificado", "desconocido", "none", "null", ""]:
                email_norm = vacante.get("email", "No especificado")
            if email_norm == "No especificado" and vacante.get("email") and "@" in str(vacante.get("email", "")):
                email_norm = vacante["email"]

            # 9. LISTAS (Limpieza, filtrado de vacíos y deduplicación)
            valores_invalidos = {"no especificado", "no especificada", "desconocido", "desconocida", "ninguno", "ninguna", "n/a", "none", "null", "...", "no aplica"}

            requisitos_norm = data_ia.get("requisitos") or []
            if isinstance(requisitos_norm, str):
                requisitos_norm = [r.strip() for r in requisitos_norm.split("\n") if r.strip()]
            req_limpios = []
            for r in requisitos_norm:
                r_str = str(r).strip()
                if r_str and r_str.lower() not in valores_invalidos and r_str not in req_limpios:
                    req_limpios.append(r_str)
            requisitos_norm = req_limpios

            beneficios_norm = data_ia.get("beneficios") or []
            if isinstance(beneficios_norm, str):
                beneficios_norm = [b.strip() for b in beneficios_norm.split("\n") if b.strip()]
            ben_limpios = []
            for b in beneficios_norm:
                b_str = str(b).strip()
                if b_str and b_str.lower() not in valores_invalidos and b_str not in ben_limpios:
                    ben_limpios.append(b_str)
            beneficios_norm = ben_limpios

            palabras_clave_norm = data_ia.get("palabras_clave") or vacante.get("etiquetas", [])
            if isinstance(palabras_clave_norm, str):
                palabras_clave_norm = [p.strip() for p in palabras_clave_norm.split(",") if p.strip()]
            kw_limpios = []
            kw_vistas = set()
            for p in palabras_clave_norm:
                p_str = str(p).strip()
                if p_str and p_str.lower() not in valores_invalidos and p_str.lower() not in kw_vistas:
                    kw_vistas.add(p_str.lower())
                    kw_limpios.append(p_str)
            palabras_clave_norm = kw_limpios

            # 10. DESCRIPCIÓN creada por la IA
            descripcion_ia = (data_ia.get("descripcion") or "").strip()
            if not descripcion_ia or len(descripcion_ia) < 40:
                descripcion_ia = desc_cruda if desc_cruda else puesto_norm

            # ─── CONSTRUIR VACANTE LIMPIA (solo datos normalizados) ───
            # Preservar ID y URLs originales
            vacante_limpia = {
                "id_oferta": vacante.get("id_oferta"),
                "puesto": puesto_norm,
                "empresa": empresa_norm,
                "ubicacion": ubicacion_norm,
                "provincia": provincia_norm,
                "ciudad": ciudad_norm,
                "pais": vacante.get("pais", "República Dominicana"),
                "modalidad": modalidad_norm,
                "horario": horario_norm,
                "salario_mostrado": salario_norm,
                "sueldo": int(sueldo_num) if sueldo_num else 0,
                "sexo": sexo_norm,
                "telefono": tel_norm,
                "email": email_norm,
                "requisitos": requisitos_norm,
                "beneficios": beneficios_norm,
                "palabras_clave": palabras_clave_norm,
                "descripcion": descripcion_ia,
                "fecha_publicacion": vacante.get("fecha_publicacion", ""),
                "url_oferta": vacante.get("url_oferta", ""),
                "url_postular": vacante.get("url_postular", ""),
                "normalizado_con_ia": True
            }

            # Conservar logo si existe
            if vacante.get("logo_empresa"):
                vacante_limpia["logo_empresa"] = vacante["logo_empresa"]

            # Actualizar el diccionario original in-place para compatibilidad
            vacante.clear()
            vacante.update(vacante_limpia)
            return vacante

        except Exception as e:
            log_warning(f"No se pudo normalizar vacante '{puesto_orig}' con IA ({e}). Se conservan datos heurísticos.")
            vacante["normalizado_con_ia"] = False
            if not vacante.get("descripcion"):
                vacante["descripcion"] = desc_cruda or puesto_orig
            return vacante

    def normalizar_lote(
        self, 
        vacantes: List[Dict[str, Any]], 
        max_items: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Normaliza secuencialmente una lista de vacantes mostrando progreso en consola."""
        total = len(vacantes) if max_items is None else min(len(vacantes), max_items)
        if total == 0:
            log_info("No hay vacantes para normalizar.")
            return vacantes

        print(f"\n{Colors.BOLD}{Colors.HEADER}==================================================================={Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.HEADER}  🤖 NORMALIZACIÓN CON IA Y GENERACIÓN DE DESCRIPCIONES (OLLAMA)   {Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.HEADER}==================================================================={Colors.RESET}")
        log_info(f"Total a procesar: {Colors.BOLD}{total}{Colors.RESET} vacantes")
        log_info(f"Modelo activo: {Colors.BOLD}{self.model}{Colors.RESET}")

        t_inicio = time.time()
        exitosos = 0

        for idx, vacante in enumerate(vacantes[:total], start=1):
            puesto_prev = vacante.get("puesto") or vacante.get("titulo") or f"Vacante #{idx}"
            print(f"\n{Colors.CYAN}[{idx}/{total}]{Colors.RESET} Procesando con IA: {Colors.BOLD}{puesto_prev[:50]}{Colors.RESET}...")

            t0 = time.time()
            self.normalizar_vacante(vacante)
            duracion = time.time() - t0

            if vacante.get("normalizado_con_ia"):
                exitosos += 1
                desc_prev = vacante.get("descripcion", "")[:90].replace("\n", " ")
                print(f"  {Colors.GREEN}✔ Puesto normalizado:{Colors.RESET} {vacante.get('puesto')} | {vacante.get('empresa')}")
                print(f"  {Colors.GREEN}✔ Ubicación/Modalidad:{Colors.RESET} {vacante.get('ubicacion')} ({vacante.get('modalidad')}) | Salario: {vacante.get('salario_mostrado')}")
                print(f"  {Colors.GREEN}✔ Descripción IA generada:{Colors.RESET} \"{desc_prev}...\" ({duracion:.1f}s)")
            else:
                print(f"  {Colors.YELLOW}⚠ Usando datos originales (Fallo IA o timeout){Colors.RESET}")

        t_total = time.time() - t_inicio
        print(f"\n{Colors.BOLD}{Colors.GREEN}-------------------------------------------------------------------{Colors.RESET}")
        log_success(f"Normalización finalizada: {exitosos}/{total} vacantes enriquecidas con IA en {t_total:.1f}s")
        print(f"{Colors.BOLD}{Colors.GREEN}==================================================================={Colors.RESET}\n")

        return vacantes


def main():
    parser = argparse.ArgumentParser(description="Normalizar vacantes en archivo JSON con IA de Ollama")
    parser.add_argument("archivo", type=str, help="Ruta al archivo JSON con vacantes")
    parser.add_argument("-o", "--output", type=str, default=None, help="Ruta de guardado (sobrescribe si no se indica)")
    parser.add_argument("-m", "--model", type=str, default="maternion/ling-3.0-tiny:8b", help="Modelo de Ollama")
    parser.add_argument("--host", type=str, default="http://localhost:11434", help="Host de Ollama")
    parser.add_argument("--limit", type=int, default=None, help="Límite máximo de vacantes a normalizar")
    args = parser.parse_args()

    if not os.path.exists(args.archivo):
        log_error(f"Archivo no encontrado: {args.archivo}")
        sys.exit(1)

    with open(args.archivo, "r", encoding="utf-8") as f:
        data = json.load(f)

    vacantes = data.get("vacantes", data if isinstance(data, list) else [])
    normalizador = NormalizadorIAVacantes(host=args.host, preferred_model=args.model)
    normalizadas = normalizador.normalizar_lote(vacantes, max_items=args.limit)

    output_path = args.output or args.archivo
    if isinstance(data, dict) and "vacantes" in data:
        data["vacantes"] = normalizadas
        data["metadata"] = data.get("metadata", {})
        data["metadata"]["normalizado_con_ia"] = True
        data["metadata"]["modelo_ia"] = normalizador.model
        data["metadata"]["fecha_normalizacion"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        a_guardar = data
    else:
        a_guardar = normalizadas

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(a_guardar, f, ensure_ascii=False, indent=2)

    log_success(f"Archivo guardado exitosamente en: {output_path}")


if __name__ == "__main__":
    main()
