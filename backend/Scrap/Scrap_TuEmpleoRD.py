#!/usr/bin/env python3
"""
Scraper de Vacantes Recientes en Tu Empleo RD (tuempleord.do)
============================================================
Este script extrae las ofertas de empleo recientes del portal Tu Empleo RD:
https://tuempleord.do/

Utiliza el endpoint de listados de WP Job Manager para paginar y recopilar
las vacantes publicadas, visita cada oferta para extraer la descripción completa,
contactos (correo, teléfono), requisitos y metadatos oficiales schema.org (JobPosting).

Opcionalmente, puede insertar las vacantes extraídas directamente en la
base de datos vectorial Qdrant utilizando el módulo Qdrant_fill.
"""

import sys
import os
import re
import html
import json
import time
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

try:
    from curl_cffi import requests
except ImportError:
    import requests

from bs4 import BeautifulSoup

try:
    from normalizador_ia import NormalizadorIAVacantes
    from localizador_ubicacion import LocalizadorUbicacionIA
except ImportError:
    from Scrap.normalizador_ia import NormalizadorIAVacantes
    from Scrap.localizador_ubicacion import LocalizadorUbicacionIA

BASE_URL = "https://tuempleord.do"
AJAX_URL = "https://tuempleord.do/jm-ajax/get_listings/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://tuempleord.do/",
    "Origin": "https://tuempleord.do"
}

# Colores para consola
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
    print(f"{Colors.CYAN}ℹ [INFO]{Colors.RESET} {msg}")

def log_success(msg: str):
    print(f"{Colors.GREEN}✔ [ÉXITO]{Colors.RESET} {msg}")

def log_warning(msg: str):
    print(f"{Colors.YELLOW}⚠ [ALERTA]{Colors.RESET} {msg}")

def log_error(msg: str):
    print(f"{Colors.RED}✖ [ERROR]{Colors.RESET} {msg}")


def limpiar_texto(texto: Optional[str]) -> str:
    """Limpia etiquetas HTML, saltos de línea repetidos y caracteres HTML escapados."""
    if not texto:
        return ""
    texto = html.unescape(texto)
    # Si contiene etiquetas HTML, limpiarlas
    if "<" in texto and ">" in texto:
        soup = BeautifulSoup(texto, "html.parser")
        texto = soup.get_text("\n")
    texto = re.sub(r'\r\n|\r|\n', '\n', texto)
    texto = re.sub(r'[ \t]+', ' ', texto)
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    return texto.strip()


def parsear_fecha_publicacion(fecha_str: str, fecha_referencia: Optional[datetime] = None) -> Optional[datetime]:
    """Interpreta fechas absolutas (DD/MM/YYYY, ISO) o relativas en español."""
    if not fecha_str or not str(fecha_str).strip():
        return None
    if fecha_referencia is None:
        fecha_referencia = datetime.now()

    s = str(fecha_str).strip().lower()

    # 1. ISO (YYYY-MM-DD o YYYY-MM-DDTHH:MM:SS)
    iso_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', s)
    if iso_match:
        y, m, d = map(int, iso_match.groups())
        return datetime(y, m, d)

    # 2. DD/MM/YYYY o DD-MM-YYYY
    dmy_match = re.search(r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})', s)
    if dmy_match:
        d, m, y = map(int, dmy_match.groups())
        return datetime(y, m, d)

    # 3. Expresiones relativas en español
    if 'hoy' in s or any(k in s for k in ['segundo', 'minuto', 'hora']):
        return fecha_referencia

    if 'ayer' in s:
        return fecha_referencia - timedelta(days=1)

    m_dias = re.search(r'hace\s+(\d+)\s+d[íi]a', s)
    if m_dias:
        return fecha_referencia - timedelta(days=int(m_dias.group(1)))

    m_sem = re.search(r'hace\s+(\d+)\s+semana', s)
    if m_sem:
        return fecha_referencia - timedelta(weeks=int(m_sem.group(1)))

    m_mes = re.search(r'hace\s+(\d+)\s+mes', s)
    if m_mes:
        return fecha_referencia - timedelta(days=int(m_mes.group(1)) * 30)

    m_ano = re.search(r'hace\s+(\d+)\s+a[ñn]o', s)
    if m_ano:
        return fecha_referencia - timedelta(days=int(m_ano.group(1)) * 365)

    return None


def detectar_modalidad(texto: str) -> str:
    """Infiere la modalidad del puesto a partir del contenido."""
    t = texto.lower()
    if any(k in t for k in ["100% remoto", "remoto", "teletrabajo", "home office", "desde casa"]):
        return "Remoto"
    if any(k in t for k in ["híbrido", "hibrido", "semi-presencial", "semipresencial"]):
        return "Híbrido"
    return "Presencial"


def detectar_horario(texto: str) -> str:
    """Infiere el horario de trabajo a partir del contenido."""
    t = texto.lower()
    if any(k in t for k in ["medio tiempo", "part time", "medio-tiempo", "media jornada"]):
        return "Medio Tiempo"
    if any(k in t for k in ["rotativo", "turnos rotativos"]):
        return "Turnos Rotativos"
    if any(k in t for k in ["lunes a viernes"]):
        return "Lunes a Viernes"
    return "Tiempo Completo"


def detectar_sexo(texto: str) -> str:
    """Detecta si la oferta especifica algún género."""
    t = texto.lower()
    if re.search(r'\b(femenino|mujer|femenina|damas?|chicas?)\b', t):
        return "Femenino"
    if re.search(r'\b(masculino|hombre|varón|varon|caballeros?|chicos?)\b', t):
        return "Masculino"
    return "No especificado"


def extraer_sueldo_texto(texto: str) -> Optional[str]:
    """Busca patrones de salarios expresados en pesos o dólares."""
    patrones = [
        r'(?:RD\$|DOP\$?|\$)\s*([\d,]+(?:\.\d{2})?)\s*(?:a|hasta|-)\s*(?:RD\$|DOP\$?|\$)?\s*([\d,]+(?:\.\d{2})?)',
        r'(?:RD\$|DOP\$?|\$)\s*([\d,]{4,}(?:\.\d{2})?)',
        r'sueldo\s*(?:base|inicial)?\s*(?:de)?\s*:?\s*(?:RD\$|DOP\$?|\$)?\s*([\d,]{4,})',
        r'salario\s*(?:base|inicial)?\s*(?:de)?\s*:?\s*(?:RD\$|DOP\$?|\$)?\s*([\d,]{4,})'
    ]
    for p in patrones:
        m = re.search(p, texto, re.IGNORECASE)
        if m:
            return m.group(0).strip()
    return None


def extraer_metadatos_detalle(url_vacante: str) -> Dict[str, Any]:
    """
    Visita la página individual de la vacante para extraer el objeto
    oficial de schema.org (JobPosting) con la descripción completa,
    datos de contacto (email, teléfonos) y fechas.
    """
    detalles = {
        "descripcion_completa": "",
        "requisitos_educativos": "",
        "fecha_expiracion": "",
        "fecha_publicacion_iso": "",
        "salario_estructurado": None,
        "email_contacto": "",
        "telefono_contacto": "",
        "empresa_detalle": "",
        "ubicacion_detalle": ""
    }

    try:
        res = requests.get(url_vacante, headers={"User-Agent": HEADERS["User-Agent"]}, impersonate="chrome", timeout=12)
        if res.status_code != 200:
            return detalles

        soup = BeautifulSoup(res.text, "html.parser")

        # 1. Buscar bloques JSON-LD schema.org
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
                items = data.get("@graph", [data]) if isinstance(data, dict) else []
                for item in items:
                    if item.get("@type") == "JobPosting":
                        raw_desc = item.get("description", "")
                        detalles["descripcion_completa"] = limpiar_texto(raw_desc)
                        detalles["fecha_expiracion"] = item.get("validThrough", "")
                        detalles["fecha_publicacion_iso"] = item.get("datePosted", "")

                        # Empresa
                        org = item.get("hiringOrganization", {})
                        if isinstance(org, dict) and org.get("name"):
                            detalles["empresa_detalle"] = org.get("name").strip()

                        # Ubicación
                        job_loc = item.get("jobLocation", {})
                        if isinstance(job_loc, dict):
                            addr = job_loc.get("address", "")
                            if isinstance(addr, dict):
                                detalles["ubicacion_detalle"] = addr.get("addressLocality") or addr.get("name") or ""
                            elif isinstance(addr, str):
                                detalles["ubicacion_detalle"] = addr

                        # Requisitos
                        edu = item.get("educationRequirements")
                        if isinstance(edu, dict):
                            detalles["requisitos_educativos"] = edu.get("credentialCategory", "")
                        elif isinstance(edu, str):
                            detalles["requisitos_educativos"] = edu
            except Exception:
                continue

        # 2. Si la descripción no vino en JSON-LD, extraer del contenedor HTML
        if not detalles["descripcion_completa"]:
            desc_el = soup.find("div", class_="job_description")
            if desc_el:
                detalles["descripcion_completa"] = limpiar_texto(desc_el.get_text("\n"))

        texto_general = detalles["descripcion_completa"]

        # 3. Extraer correo electrónico de postulación
        email_el = soup.find(class_="job_application_email")
        if email_el:
            email_txt = email_el.get_text(strip=True)
            if "@" in email_txt:
                detalles["email_contacto"] = email_txt

        if not detalles["email_contacto"] and texto_general:
            match_email = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', texto_general)
            if match_email:
                detalles["email_contacto"] = match_email.group(0).strip()

        # 4. Extraer números telefónicos dominicanos
        if texto_general:
            telefonos = re.findall(r'(?:(?:809|829|849)[\s.-]?\d{3}[\s.-]?\d{4})', texto_general)
            if telefonos:
                detalles["telefono_contacto"] = telefonos[0].strip()

    except Exception as e:
        log_warning(f"No se pudieron obtener detalles completos de {url_vacante}: {e}")

    return detalles


def extraer_vacantes_de_html(
    html_content: str, 
    fetch_details: bool = True,
    fecha_referencia: Optional[datetime] = None,
    fecha_limite: Optional[datetime] = None
) -> Tuple[List[Dict[str, Any]], bool]:
    """Extrae las ofertas de empleo de los elementos li.job_listing."""
    soup = BeautifulSoup(html_content, "html.parser")
    items = soup.find_all("li", class_=lambda c: c and "job_listing" in c)
    vacantes = []
    fin_por_antiguedad = False
    seen_ids = set()

    if fecha_referencia is None:
        fecha_referencia = datetime.now()

    for item in items:
        link_tag = item.find("a", href=True)
        if not link_tag:
            continue

        url_oferta = link_tag["href"].strip()

        # Extraer ID del post
        classes = item.get("class", [])
        classes_str = " ".join(classes)
        match_id = re.search(r'post-(\d+)', classes_str)
        oferta_id = match_id.group(1) if match_id else None
        if not oferta_id:
            match_id_url = re.search(r'p=(\d+)', url_oferta)
            oferta_id = match_id_url.group(1) if match_id_url else str(abs(hash(url_oferta)) % 10000000)

        if oferta_id in seen_ids:
            continue
        seen_ids.add(oferta_id)

        # Título del puesto
        h3 = item.find("h3")
        titulo = h3.get_text(strip=True) if h3 else "Vacante sin título"

        # Empresa / Tipo de listado
        company_tag = item.find("li", class_="company")
        empresa = company_tag.get_text(strip=True) if company_tag else "Confidencial"

        # Fecha mostrada en la tarjeta
        date_tag = item.find("li", class_="date")
        fecha_tarjeta = date_tag.get_text(strip=True) if date_tag else ""

        # Validar fecha de la tarjeta contra el límite de 30 días
        dt_tarjeta = parsear_fecha_publicacion(fecha_tarjeta, fecha_referencia)
        if fecha_limite and dt_tarjeta:
            if dt_tarjeta < fecha_limite:
                fin_por_antiguedad = True
                continue

        # Ubicación inferida de clases (ej. provincia-santo-domingo) o tarjeta
        ubicacion = "República Dominicana"
        match_prov = re.search(r'provincia-([a-z-]+)', classes_str)
        if match_prov:
            prov_raw = match_prov.group(1).replace("-", " ").title()
            ubicacion = prov_raw

        # Resumen corto
        p_resumen = item.find("p", class_="p2")
        resumen_corto = p_resumen.get_text(strip=True) if p_resumen else ""

        # Construir objeto base
        oferta_obj = {
            "id_oferta": int(oferta_id) if oferta_id.isdigit() else oferta_id,
            "puesto": titulo,
            "empresa": empresa if empresa and empresa.lower() != "confidencial" else "Confidencial",
            "ubicacion": ubicacion,
            "ciudad": ubicacion,
            "provincia": ubicacion,
            "pais": "República Dominicana",
            "modalidad": detectar_modalidad(titulo + " " + resumen_corto),
            "horario": detectar_horario(titulo + " " + resumen_corto),
            "salario_mostrado": "No especificado",
            "sueldo": 0,
            "fecha_publicacion": fecha_tarjeta,
            "resumen_corto": resumen_corto,
            "descripcion": resumen_corto,
            "url_oferta": url_oferta,
            "url_postular": url_oferta,
            "telefono": "No especificado",
            "email": "No especificado",
            "sexo": detectar_sexo(titulo + " " + resumen_corto),
            "requisitos": [],
            "beneficios": [],
            "palabras_clave": [ubicacion],
            "etiquetas": [ubicacion],
            "detalles": {}
        }

        # Extraer metadatos profundos si está habilitado
        if fetch_details:
            detalles_profundos = extraer_metadatos_detalle(url_oferta)
            oferta_obj["detalles"] = detalles_profundos

            # Si viene fecha ISO en el schema, validarla también
            fecha_iso = detalles_profundos.get("fecha_publicacion_iso")
            if fecha_iso:
                dt_iso = parsear_fecha_publicacion(fecha_iso, fecha_referencia)
                if fecha_limite and dt_iso and dt_iso < fecha_limite:
                    fin_por_antiguedad = True
                    continue
                oferta_obj["fecha_publicacion"] = fecha_iso

            if detalles_profundos.get("empresa_detalle"):
                oferta_obj["empresa"] = detalles_profundos["empresa_detalle"]

            if detalles_profundos.get("ubicacion_detalle"):
                oferta_obj["ubicacion"] = detalles_profundos["ubicacion_detalle"]
                oferta_obj["ciudad"] = detalles_profundos["ubicacion_detalle"]

            if detalles_profundos.get("email_contacto"):
                oferta_obj["email"] = detalles_profundos["email_contacto"]

            if detalles_profundos.get("telefono_contacto"):
                oferta_obj["telefono"] = detalles_profundos["telefono_contacto"]

            desc_comp = detalles_profundos.get("descripcion_completa") or ""
            if desc_comp:
                oferta_obj["descripcion"] = desc_comp
                oferta_obj["modalidad"] = detectar_modalidad(titulo + " " + desc_comp)
                oferta_obj["horario"] = detectar_horario(titulo + " " + desc_comp)
                oferta_obj["sexo"] = detectar_sexo(titulo + " " + desc_comp)
                
                # Buscar salario en texto completo
                sal_detectado = extraer_sueldo_texto(desc_comp)
                if sal_detectado:
                    oferta_obj["salario_mostrado"] = sal_detectado

        vacantes.append(oferta_obj)

    return vacantes, fin_por_antiguedad


MAPA_UBICACIONES_TUEMPLEORD = {
    "azua": "Azua",
    "bani": "Bani",
    "peravia": "Bani",
    "barahona": "Barahona",
    "bavaro": "Bavaro",
    "boca-chica": "Boca Chica",
    "bonao": "Bonao",
    "monsenor-nouel": "Bonao",
    "cotui": "Cotui",
    "sanchez-ramirez": "Cotui",
    "dajabon": "Dajabon",
    "el-seibo": "el seibo",
    "elias-pina": "Elias Piña",
    "espaillat": "Espaillat",
    "moca": "Moca",
    "haina": "haina",
    "hato-mayor": "Hato Mayor",
    "higuey": "Higuey",
    "la-altagracia": "Punta Cana",
    "la-romana": "La Romana",
    "la-vega": "La Vega",
    "jarabacoa": "jarabacoa",
    "constanza": "Contanza",
    "mao": "Mao",
    "valverde": "Mao",
    "monte-cristi": "Monte Cristi",
    "monte-plata": "Monte Plata",
    "nagua": "Nagua",
    "maria-trinidad-sanchez": "Nagua",
    "puerto-plata": "Puerto Plata",
    "punta-cana": "Punta Cana",
    "samana": "Samana",
    "san-cristobal": "San Cristobal",
    "san-francisco-de-macoris": "San Francisco de Macoris",
    "duarte": "San Francisco de Macoris",
    "san-juan": "San Juan",
    "san-pedro-de-macoris": "San Pedro de Macoris",
    "santiago": "Santiago",
    "santo-domingo": "Santo Domingo",
    "distrito-nacional": "Santo Domingo",
    "santo-domingo-este": "Santo Domingo",
    "santo-domingo-oeste": "Santo Domingo",
    "santo-domingo-norte": "Santo Domingo",
}

PROVINCIAS_PRINCIPALES_TUEMPLEORD = [
    "Santo Domingo", "Santiago", "Punta Cana", "La Romana", 
    "Puerto Plata", "San Cristobal", "La Vega", "San Pedro de Macoris",
    "San Francisco de Macoris", "Bonao", "Bani", "Moca", 
    "Azua", "Barahona", "Higuey", "Samana", "Mao", "Monte Plata"
]


def normalizar_ubicacion_tuempleord(provincia: str) -> str:
    """Convierte el nombre o slug de provincia a la ubicación esperada por Tu Empleo RD."""
    p = provincia.lower().strip()
    p = p.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")
    slug = re.sub(r'[^a-z0-9]+', '-', p).strip('-')
    if slug.startswith("en-"):
        slug = slug[3:]
    return MAPA_UBICACIONES_TUEMPLEORD.get(slug, provincia.strip().title())


def scrape_vacantes_tuempleord(
    max_paginas: int = 1, 
    dias_max: int = 30, 
    provincia: str = "todas", 
    fetch_details: bool = True,
    limite: Optional[int] = 200000
) -> List[Dict[str, Any]]:
    """Recorre las páginas de Tu Empleo RD utilizando el endpoint AJAX y recopila las vacantes recientes."""
    todas_vacantes = []
    ids_registrados = set()

    fecha_referencia = datetime.now()
    fecha_limite = fecha_referencia - timedelta(days=dias_max)
    
    es_todas = not provincia or provincia.lower().strip() in ["todas", "all", "nacional", "rd", "todo"]
    ambito_str = "Toda República Dominicana (Todas las provincias)" if es_todas else f"Provincia / Demarcación: {normalizar_ubicacion_tuempleord(provincia)}"

    log_info(f"Ámbito territorial: {Colors.BOLD}{ambito_str}{Colors.RESET}")
    log_info(f"Fecha actual (referencia): {Colors.BOLD}{fecha_referencia.strftime('%Y-%m-%d %H:%M')}{Colors.RESET}")
    log_info(f"Límite máximo de antigüedad: {Colors.BOLD}{dias_max} días{Colors.RESET} (publicadas desde {Colors.BOLD}{fecha_limite.strftime('%Y-%m-%d')}{Colors.RESET})")
    if limite and limite > 0:
        log_info(f"Límite rápido configurado: {Colors.BOLD}máximo {limite} vacantes{Colors.RESET} para agilizar pruebas")

    for pagina in range(1, max_paginas + 1):
        log_info(f"Escaneando página {pagina} de Tu Empleo RD...")

        try:
            # Petición al endpoint WP Job Manager
            data_payload = {
                "page": str(pagina),
                "per_page": "25",
                "orderby": "featured",
                "order": "DESC"
            }
            if not es_todas:
                data_payload["search_location"] = normalizar_ubicacion_tuempleord(provincia)

            res = requests.post(AJAX_URL, data=data_payload, headers=HEADERS, impersonate="chrome110", timeout=20)
            
            if res.status_code == 200:
                try:
                    js = res.json()
                    html_content = js.get("html", "")
                except Exception:
                    html_content = res.text
            else:
                # Fallback directo al home si la página 1 falla por AJAX
                if pagina == 1:
                    log_warning(f"Endpoint AJAX retornó {res.status_code}. Intentando home directo...")
                    res = requests.get(BASE_URL, headers={"User-Agent": HEADERS["User-Agent"]}, impersonate="chrome110", timeout=20)
                    html_content = res.text
                else:
                    log_error(f"Error {res.status_code} al solicitar página {pagina}")
                    break

            if not html_content:
                log_info(f"No se recibió contenido en la página {pagina}.")
                break

            vacantes_pagina, fin_por_antiguedad = extraer_vacantes_de_html(
                html_content, 
                fetch_details=fetch_details,
                fecha_referencia=fecha_referencia,
                fecha_limite=fecha_limite
            )

            nuevas_vacantes = []
            for v in vacantes_pagina:
                vid = v["id_oferta"]
                if vid not in ids_registrados:
                    ids_registrados.add(vid)
                    nuevas_vacantes.append(v)
                    todas_vacantes.append(v)
                    if limite and limite > 0 and len(todas_vacantes) >= limite:
                        break

            log_success(f"Página {pagina}: {len(nuevas_vacantes)} vacantes dentro del rango de {dias_max} días.")

            if limite and limite > 0 and len(todas_vacantes) >= limite:
                log_info(f"Se alcanzó el límite de {limite} vacantes para pruebas rápidas. Deteniendo scraping.")
                break

            if fin_por_antiguedad:
                log_info(f"Se alcanzaron vacantes con más de {dias_max} días (anteriores al {fecha_limite.strftime('%Y-%m-%d')}). Finalizando escaneo.")
                break

            if not nuevas_vacantes:
                log_info("No se encontraron nuevas vacantes en esta página. Fin del listado.")
                break

            time.sleep(0.4)

        except Exception as e:
            log_error(f"Error procesando la página {pagina}: {e}")
            break

    return todas_vacantes


def scrape_vacantes_tuempleord_todas_provincias(
    max_paginas_por_provincia: int = 2,
    dias_max: int = 30,
    fetch_details: bool = True
) -> List[Dict[str, Any]]:
    """
    Itera por cada demarcación/provincia de República Dominicana en Tu Empleo RD,
    extrayendo las vacantes recientes de cada una y combinándolas.
    """
    todas_vacantes = []
    ids_registrados = set()
    fecha_referencia = datetime.now()
    fecha_limite = fecha_referencia - timedelta(days=dias_max)

    log_info(f"{Colors.BOLD}Iniciando rastreo por todas las provincias en Tu Empleo RD ({len(PROVINCIAS_PRINCIPALES_TUEMPLEORD)} demarcaciones)...{Colors.RESET}")

    for idx, loc in enumerate(PROVINCIAS_PRINCIPALES_TUEMPLEORD, start=1):
        print(f"\n{Colors.CYAN}--- [{idx}/{len(PROVINCIAS_PRINCIPALES_TUEMPLEORD)}] Escaneando demarcación: {Colors.BOLD}{loc}{Colors.RESET} ---{Colors.RESET}")

        for pagina in range(1, max_paginas_por_provincia + 1):
            data_payload = {
                "page": str(pagina),
                "per_page": "25",
                "search_location": loc,
                "orderby": "featured",
                "order": "DESC"
            }

            try:
                res = requests.post(AJAX_URL, data=data_payload, headers=HEADERS, impersonate="chrome110", timeout=20)
                if res.status_code != 200:
                    break

                try:
                    html_content = res.json().get("html", "")
                except Exception:
                    html_content = res.text

                if not html_content:
                    break

                vacantes_pag, fin_antiguedad = extraer_vacantes_de_html(
                    html_content,
                    fetch_details=fetch_details,
                    fecha_referencia=fecha_referencia,
                    fecha_limite=fecha_limite
                )

                nuevas_prov = 0
                for v in vacantes_pag:
                    vid = v["id_oferta"]
                    if vid not in ids_registrados:
                        ids_registrados.add(vid)
                        todas_vacantes.append(v)
                        nuevas_prov += 1

                log_success(f"  Pág {pagina}: {nuevas_prov} nuevas vacantes para {loc}.")

                if fin_antiguedad or nuevas_prov == 0:
                    break

                time.sleep(0.3)
            except Exception as e:
                log_error(f"Error en {loc} pág {pagina}: {e}")
                break

    return todas_vacantes


def main():
    parser = argparse.ArgumentParser(description="Scraper de vacantes recientes en Tu Empleo RD (tuempleord.do)")
    parser.add_argument("-p", "--paginas", type=int, default=1, help="Número máximo de páginas a escanear (default: 1)")
    parser.add_argument("-l", "--limite", type=int, default=200000, help="Límite máximo de vacantes a extraer para pruebas rápidas (default: 5, use 0 para ilimitadas)")
    parser.add_argument("-d", "--dias", type=int, default=30, help="Antigüedad máxima en días (default: 30 días / 1 mes)")
    parser.add_argument("--provincia", type=str, default="todas", help="Provincia a buscar (default: 'todas' para toda República Dominicana, o ej: 'santiago', 'la-romana', 'punta-cana', etc.)")
    parser.add_argument("--todas-provincias", action="store_true", help="Recorrer cada provincia de RD una por una con el filtro de ubicación")
    parser.add_argument("-o", "--output", type=str, default=None, help="Ruta del archivo JSON de salida")
    parser.add_argument("--sin-detalles", action="store_true", help="No visitar las páginas individuales para extraer descripción completa")
    parser.add_argument("--qdrant", action="store_true", default=True, help="Insertar automáticamente en Qdrant (default: True)")
    parser.add_argument("--no-qdrant", dest="qdrant", action="store_false", help="Desactivar inserción en Qdrant")
    parser.add_argument("--recreate", action="store_true", help="Recrear la colección en Qdrant antes de insertar")
    parser.add_argument("--ai", dest="ai", action="store_true", default=True, help="Normalizar datos y generar descripciones con IA (default: True)")
    parser.add_argument("--no-ai", dest="ai", action="store_false", help="Desactivar normalización con IA")
    parser.add_argument("--ubicacion-exacta", dest="ubicacion_exacta", action="store_true", default=False, help="Buscar ubicación exacta y coordenadas GPS del negocio con IA (default: False, usar localizador_ubicacion.py por separado)")
    parser.add_argument("--no-ubicacion-exacta", dest="ubicacion_exacta", action="store_false", help="Desactivar búsqueda de ubicación exacta")
    parser.add_argument("--ai-model", type=str, default="maternion/ling-3.0-tiny:8b", help="Modelo de Ollama para normalización (default: maternion/ling-3.0-tiny:8b)")
    parser.add_argument("--ai-host", type=str, default="http://localhost:11434", help="Host de Ollama (default: http://localhost:11434)")
    args = parser.parse_args()

    if not args.output:
        default_dir = os.path.dirname(__file__)
        if args.todas_provincias:
            args.output = os.path.join(default_dir, "vacantes_tuempleord_todas_provincias.json")
        elif args.provincia in ["todas", "all", "nacional", "rd"]:
            args.output = os.path.join(default_dir, "vacantes_tuempleord.json")
        else:
            slug = args.provincia.lower().strip().replace(" ", "_").replace("-", "_")
            args.output = os.path.join(default_dir, f"vacantes_tuempleord_{slug}.json")

    print(f"\n{Colors.BOLD}{Colors.CYAN}==================================================================={Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}  💼 SCRAPER DE VACANTES - TU EMPLEO RD (REPÚBLICA DOMINICANA)       {Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}==================================================================={Colors.RESET}\n")

    fetch_details = not args.sin_detalles
    log_info(f"Iniciando escaneo de hasta {args.paginas} página(s)...")
    log_info(f"Filtro temporal: Últimos {args.dias} días (máximo 1 mes)")
    log_info(f"Extracción profunda de descripción y contactos: {'Activada' if fetch_details else 'Desactivada'}")

    inicio = time.time()
    if args.todas_provincias:
        vacantes = scrape_vacantes_tuempleord_todas_provincias(
            max_paginas_por_provincia=args.paginas,
            dias_max=args.dias,
            fetch_details=fetch_details
        )
        ambito_guardado = "todas_provincias_individuales"
    else:
        vacantes = scrape_vacantes_tuempleord(
            max_paginas=args.paginas, 
            dias_max=args.dias, 
            provincia=args.provincia,
            fetch_details=fetch_details,
            limite=args.limite
        )
        ambito_guardado = args.provincia

    tiempo_scraping = time.time() - inicio
    log_success(f"Fase de extracción completada: {len(vacantes)} vacantes obtenidas en {tiempo_scraping:.2f}s")

    # 1. Normalización con IA y generación de descripción profesional
    if args.ai and vacantes:
        normalizador = NormalizadorIAVacantes(host=args.ai_host, preferred_model=args.ai_model)
        vacantes = normalizador.normalizar_lote(vacantes)

    # 2. Proceso aparte posterior: Búsqueda de ubicación exacta y geocodificación
    if args.ubicacion_exacta and vacantes:
        localizador = LocalizadorUbicacionIA(host=args.ai_host, model=args.ai_model)
        vacantes = localizador.localizar_lote(vacantes)

    tiempo_total = time.time() - inicio

    fecha_hoy = datetime.now()
    resultado = {
        "metadata": {
            "portal": "Tu Empleo RD",
            "url_base": BASE_URL,
            "provincia_busqueda": ambito_guardado,
            "fecha_extraccion": fecha_hoy.isoformat(),
            "antiguedad_maxima_dias": args.dias,
            "fecha_corte_limite": (fecha_hoy - timedelta(days=args.dias)).strftime('%Y-%m-%d'),
            "paginas_escaneadas": args.paginas,
            "total_vacantes": len(vacantes),
            "normalizado_con_ia": bool(args.ai),
            "modelo_ia": args.ai_model if args.ai else None,
            "geolocalizado_con_ia": bool(args.ubicacion_exacta),
            "fecha_geolocalizacion": fecha_hoy.isoformat() if args.ubicacion_exacta else None,
            "tiempo_segundos": round(tiempo_total, 2)
        },
        "vacantes": vacantes
    }

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    print(f"\n{Colors.BOLD}======================= RESUMEN DE EXTRACCIÓN ======================={Colors.RESET}")
    log_success(f"Total de vacantes estructuradas: {Colors.BOLD}{len(vacantes)}{Colors.RESET}")
    log_success(f"Tiempo de ejecución: {tiempo_total:.2f} segundos")
    log_success(f"Archivo guardado en: {Colors.BOLD}{args.output}{Colors.RESET}")

    # Inserción en Qdrant usando Qdrant_fill
    if args.qdrant and vacantes:
        print(f"\n{Colors.BOLD}{Colors.HEADER}-------------------------------------------------------------------{Colors.RESET}")
        log_info("Iniciando inserción automática en Qdrant mediante Qdrant_fill...")
        try:
            script_qdrant = os.path.abspath(os.path.join(os.path.dirname(__file__), "../Scrap/Insertar_datos_Qdrant"))
            if script_qdrant not in sys.path:
                sys.path.insert(0, script_qdrant)
            
            from Qdrant_fill import insertar_vacantes_en_qdrant
            total_insertados = insertar_vacantes_en_qdrant(archivo_json=args.output, recreate=args.recreate)
            log_success(f"¡{total_insertados} vacantes de Tu Empleo RD indexadas en Qdrant exitosamente!")
        except Exception as e:
            log_error(f"No se pudo completar la inserción en Qdrant: {e}")
            import traceback
            traceback.print_exc()

    print(f"{Colors.BOLD}{Colors.GREEN}====================================================================={Colors.RESET}\n")


if __name__ == "__main__":
    main()
