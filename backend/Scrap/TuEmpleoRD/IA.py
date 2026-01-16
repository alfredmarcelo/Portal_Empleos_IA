import ollama
import json
import re
import time


def normalizar_texto(texto):
    modelo = "gpt-oss:20b"

    prompt = f"""
    Tu tarea es NORMALIZAR, FILTRAR y ESTRUCTURAR información de un JSON de oferta de empleo.

    INSTRUCCIONES GENERALES (OBLIGATORIAS):

    1. Analiza todo el contenido disponible en la entrada, incluyendo "Descripcion" y cualquier otro campo.  
    - Si encuentras información que pueda completar otros campos del JSON, úsala.  
    - Ejemplo: si detectas el nombre de la empresa en otro campo, colócalo en "Nombre_Empresa".

    2. Normaliza y resume los textos:
    - Elimina palabras de relleno, publicidad y frases innecesarias.
    - Conserva SOLO información esencial.
    - No inventes datos, pero aprovecha pistas implícitas para completar campos vacíos.

    3. FILTRADO Y FORMATO DE CAMPOS:
    - Puesto: elimina prefijos como "Buscamos", "Se solicita", etc.
    - Fecha_Publicacion y Fecha_Expiracion: formato YYYY-MM-DD o "No especificado"
    - Ubicacion: solo ciudad o provincia, usa cualquier pista disponible.
    - Descripcion: aclara el texto de la descripcion, hazlo legible y conciso.
    - Numero_Telefono: formato xxx-xxx-xxxx, si no existe: "No especificado"
    - Sexo: solo si es explícito, si no: "No especificado"
    - Horario: normaliza como "(hora)am-(hora)pm". Si incluye días laborales: "(Dias laborales: Lunes a viernes) (hora)am-(hora)pm". Si no hay info: "No especificado"
    - Sueldo, Email, Direccion y Beneficios: si la información aparece en otro campo, úsala. Si no hay datos: Beneficios -> [], otros campos -> "No especificado"
    - Palabras_clave: usa palabras que describan la vacante y el área, y la modalidad, si no hay info: []
    - Modalidad: si se especifica remota, híbrida o presencial, úsala; si no, por defecto: "Presencial"
    - Pasa el contenido con utf-8
    - Todos los datos que esten en minusculas

    4. FORMATO DE SALIDA:
    - Devuelve ÚNICAMENTE JSON válido.
    - Sin texto adicional ni comentarios.
    - Usa EXACTAMENTE estas claves y orden:

    {{
    "URL": "",
    "Puesto": "",
    "Modalidad": "",
    "Descripcion": "",
    "Beneficios": [],
    "Fecha_Publicacion": "",
    "Fecha_Expiracion": "",
    "Horario": "",
    "Sexo": "",
    "Ubicacion": "",
    "Nombre_Empresa": "",
    "Numero_Telefono": "",
    "Email": "",
    "Direccion": "",
    "Sueldo": "",
    "Palabras_clave": [],
    "tiempo_procesamiento": ""
    }}

    ENTRADA:
    {texto}
    """
    respuesta = ollama.chat(
        model=modelo,
        messages=[{"role": "user", "content": prompt}],
        options={"thinking": False}
    )

    raw = respuesta["message"]["content"].strip()

    # ---- NORMALIZACIÓN CRÍTICA ----

    # 1. Eliminar comillas externas si existen
    if raw.startswith('"') and raw.endswith('"'):
        raw = raw[1:-1]

    # 3. Extraer solo el bloque JSON (seguridad extra)
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError("No se pudo extraer JSON válido")

    json_text = match.group()

    # 4. Convertir a dict
    data = json.loads(json_text)

    return data
