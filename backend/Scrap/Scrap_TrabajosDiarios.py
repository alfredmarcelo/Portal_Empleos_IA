#!/usr/bin/env python3
"""
Scraper de Vacantes Recientes en Santo Domingo Este (TrabajosDiarios)
====================================================================
Este script extrae las ofertas de empleo recientes de:
https://do.trabajosdiarios.com/ofertas-trabajo/en-santo-domingo/en-santo-domingo-este

Estructura los datos obtenidos en un formato JSON limpio y completo,
incluyendo datos de la tarjeta y los metadatos estructurados oficiales (JobPosting).
Opcionalmente, puede insertar las vacantes extraídas directamente en la
base de datos vectorial Qdrant utilizando el módulo Qdrant_fill.
"""

import sys
import os
import re
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

BASE_URL = "https://do.trabajosdiarios.com"
OFERTAS_URL = "https://do.trabajosdiarios.com/ofertas-trabajo"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
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
    """Limpia saltos de línea repetidos y espacios redundantes."""
    if not texto:
        return ""
    texto = re.sub(r'\r\n|\r|\n', '\n', texto)
    texto = re.sub(r'[ \t]+', ' ', texto)
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    return texto.strip()


PROVINCIAS_RD_SLUGS = {
    "azua": "azua",
    "baoruco": "baoruco",
    "bahoruco": "baoruco",
    "barahona": "barahona",
    "dajabon": "dajabon",
    "distrito-nacional": "distrito-nacional",
    "santo-domingo-de-guzman": "distrito-nacional/en-santo-domingo-de-guzman",
    "santo-domingo": "santo-domingo",
    "santo-domingo-este": "santo-domingo/en-santo-domingo-este",
    "santo-domingo-oeste": "santo-domingo/en-santo-domingo-oeste",
    "santo-domingo-norte": "santo-domingo/en-santo-domingo-norte",
    "duarte": "duarte",
    "san-francisco-de-macoris": "duarte",
    "el-seibo": "el-seibo",
    "elias-pina": "elias-pina",
    "espaillat": "espaillat",
    "moca": "espaillat",
    "hato-mayor": "hato-mayor",
    "hermanas-mirabal": "hermanas-mirabal",
    "salcedo": "hermanas-mirabal",
    "independencia": "independencia",
    "la-altagracia": "la-altagracia",
    "punta-cana": "la-altagracia/en-punta-cana",
    "bavaro": "la-altagracia/en-bavaro",
    "higuey": "la-altagracia/en-higuey",
    "la-romana": "la-romana",
    "la-vega": "la-vega",
    "maria-trinidad-sanchez": "maria-trinidad-sanchez",
    "nagua": "maria-trinidad-sanchez",
    "monsenor-nouel": "monsenor-nouel",
    "bonao": "monsenor-nouel",
    "monte-cristi": "monte-cristi",
    "monte-plata": "monte-plata",
    "pedernales": "pedernales",
    "peravia": "peravia",
    "bani": "peravia",
    "puerto-plata": "puerto-plata",
    "samana": "samana",
    "san-cristobal": "san-cristobal",
    "san-jose-de-ocoa": "san-jose-de-ocoa",
    "san-juan": "san-juan",
    "san-pedro-de-macoris": "san-pedro-de-macoris",
    "sanchez-ramirez": "sanchez-ramirez",
    "cotui": "sanchez-ramirez",
    "santiago": "santiago",
    "santiago-de-los-caballeros": "santiago/en-santiago-de-los-caballeros",
    "santiago-rodriguez": "santiago-rodriguez",
    "valverde": "valverde",
    "mao": "valverde"
}

PROVINCIAS_PRINCIPALES_RD = [
    "distrito-nacional", "santo-domingo", "santiago", "la-altagracia",
    "la-romana", "san-cristobal", "puerto-plata", "la-vega",
    "san-pedro-de-macoris", "duarte", "espaillat", "peravia",
    "azua", "barahona", "monsenor-nouel", "samana", "valverde",
    "monte-plata", "sanchez-ramirez", "maria-trinidad-sanchez"
]


def normalizar_slug_provincia(provincia: str) -> str:
    """Convierte el nombre de provincia o municipio a formato slug sin tildes."""
    p = provincia.lower().strip()
    p = p.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")
    slug = re.sub(r'[^a-z0-9]+', '-', p).strip('-')
    if slug.startswith("en-"):
        slug = slug[3:]
    return slug


def construir_url_busqueda(provincia: Optional[str] = None) -> str:
    """
    Construye la URL de búsqueda en TrabajosDiarios según la provincia indicada.
    - Si provincia es None, 'todas', 'nacional' o 'rd', utiliza la URL raíz de ofertas
      que agrega vacantes de toda República Dominicana (todas las provincias).
    - Si se especifica una provincia (ej: 'santiago', 'la-romana', 'punta-cana'),
      modifica la URL a https://do.trabajosdiarios.com/ofertas-trabajo/en-{provincia}.
    """
    if not provincia or provincia.lower().strip() in ["todas", "all", "nacional", "rd", "todo"]:
        return OFERTAS_URL

    slug = normalizar_slug_provincia(provincia)
    destino = PROVINCIAS_RD_SLUGS.get(slug, slug)
    
    if destino.startswith("en-"):
        return f"{OFERTAS_URL}/{destino}"
    return f"{OFERTAS_URL}/en-{destino}"


def extraer_ciudad_y_provincia(ubicacion_str: str) -> Tuple[str, str]:
    """Separa una cadena de ubicación 'Ciudad, Provincia' en ciudad y provincia."""
    if not ubicacion_str:
        return "Santo Domingo", "República Dominicana"
    partes = [p.strip() for p in ubicacion_str.split(",") if p.strip()]
    if len(partes) >= 2:
        return partes[0], partes[-1]
    return partes[0], partes[0]


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


def extraer_metadatos_detalle(url_vacante: str) -> Dict[str, Any]:
    """
    Visita la página individual de la vacante para extraer el objeto
    oficial de schema.org (JobPosting) con la descripción completa y requisitos.
    """
    detalles = {
        "descripcion_completa": "",
        "requisitos_educativos": "",
        "fecha_expiracion": "",
        "fecha_publicacion_iso": "",
        "salario_estructurado": None,
        "puestos_disponibles": 1,
        "modalidad_contrato": ""
    }

    try:
        res = requests.get(url_vacante, headers=HEADERS, impersonate="chrome", timeout=12)
        if res.status_code != 200:
            return detalles

        soup = BeautifulSoup(res.text, "html.parser")

        # Buscar correo electrónico de contacto en el texto de la vacante
        match_email = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', soup.get_text())
        if match_email:
            detalles["email_contacto"] = match_email.group(0).strip()
        else:
            detalles["email_contacto"] = ""

        # Buscar bloques JSON-LD schema.org
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string)
                items = data.get("@graph", [data]) if isinstance(data, dict) else []
                for item in items:
                    if item.get("@type") == "JobPosting":
                        raw_desc = item.get("description", "")
                        detalles["descripcion_completa"] = limpiar_texto(raw_desc)
                        detalles["fecha_expiracion"] = item.get("validThrough", "")
                        detalles["fecha_publicacion_iso"] = item.get("datePosted", "")
                        detalles["modalidad_contrato"] = item.get("employmentType", "")

                        edu = item.get("educationRequirements")
                        if isinstance(edu, dict):
                            detalles["requisitos_educativos"] = edu.get("credentialCategory", "")
                        elif isinstance(edu, str):
                            detalles["requisitos_educativos"] = edu

                        detalles["puestos_disponibles"] = item.get("totalJobOpenings", 1)

                        sal = item.get("baseSalary")
                        if isinstance(sal, dict):
                            moneda = sal.get("currency", "DOP")
                            val = sal.get("value", {})
                            monto = val.get("value") if isinstance(val, dict) else val
                            unidad = val.get("unitText", "MONTH") if isinstance(val, dict) else "MONTH"
                            detalles["salario_estructurado"] = {
                                "moneda": moneda,
                                "monto": monto,
                                "periodo": unidad,
                                "texto": f"{moneda} ${monto:,.2f} / {unidad}" if monto else None
                            }
                        return detalles
            except Exception:
                continue

    except Exception as e:
        log_warning(f"No se pudieron obtener detalles completos de {url_vacante}: {e}")

    return detalles


def extraer_vacantes_de_tarjetas(
    soup: BeautifulSoup, 
    fetch_details: bool = True,
    fecha_referencia: Optional[datetime] = None,
    fecha_limite: Optional[datetime] = None
) -> Tuple[List[Dict[str, Any]], bool]:
    """Extrae las ofertas de empleo de las tarjetas HTML de la página de listado."""
    vacantes = []
    fin_por_antiguedad = False
    
    if fecha_referencia is None:
        fecha_referencia = datetime.now()

    tarjetas = soup.find_all("a", attrs={"data-enlace-oferta": "1"})
    if not tarjetas:
        tarjetas = soup.find_all("a", href=lambda h: h and "/trabajo/" in h and "/candidatos/" not in h and "/empresas/" not in h)

    seen_ids = set()

    for card in tarjetas:
        href = card.get("href", "")
        if not href:
            continue

        match_id = re.search(r'/trabajo/(\d+)/', href)
        if not match_id:
            continue
        oferta_id = match_id.group(1)

        if oferta_id in seen_ids:
            continue
        seen_ids.add(oferta_id)

        url_oferta = href if href.startswith("http") else f"{BASE_URL}{href}"
        url_postular = f"{BASE_URL}/candidatos/postular/{oferta_id}"

        # Título / Puesto
        h3 = card.find("h3")
        titulo = h3.get_text(strip=True) if h3 else "No especificado"

        # Empresa
        p_empresa = card.find("p", class_=lambda c: c and "text-secondary" in c)
        empresa = p_empresa.get_text(strip=True) if p_empresa else "Confidencial / No especificada"

        # Logo
        img = card.find("img")
        logo_url = img.get("src") if img else None

        # Resumen de descripción en la tarjeta
        p_desc = card.find("p", class_=lambda c: c and "font_4" in c and "fw-lighter" in c)
        resumen_tarjeta = limpiar_texto(p_desc.get_text(strip=True)) if p_desc else ""

        # Badges / Etiquetas
        badges = [b.get_text(strip=True) for b in card.find_all("span", class_=lambda c: c and "badge" in c)]

        # Ubicación, fecha y salario en el pie de la tarjeta
        footer = card.find("div", class_=lambda c: c and "row" in c and "small" in c)
        ubicacion = "República Dominicana"
        fecha_tarjeta = ""
        salario_tarjeta = "A convenir / No especificado"

        if footer:
            elementos = [t.strip() for t in footer.stripped_strings if t.strip() and t.strip() != '•']
            for elem in elementos:
                if re.search(r'\d{2}/\d{2}/\d{4}', elem) or any(k in elem.lower() for k in ["ayer", "hoy", "hace", "días"]):
                    fecha_tarjeta = elem
                elif any(k in elem.lower() for k in ["rd$", "us$", "$", "mensual", "quincenal"]):
                    salario_tarjeta = elem
                elif any(k in elem.lower() for k in ["santo domingo", "este", "oeste", "norte", "distrito", "santiago", "romana", "vega", "cristóbal", "cristobal", "plata", "república"]):
                    ubicacion = elem

        ciudad, provincia_detectada = extraer_ciudad_y_provincia(ubicacion)

        # Validar fecha contra fecha límite (máximo 1 mes)
        dt_tarjeta = parsear_fecha_publicacion(fecha_tarjeta, fecha_referencia)
        if fecha_limite and dt_tarjeta:
            if dt_tarjeta < fecha_limite:
                fin_por_antiguedad = True
                continue

        oferta_obj = {
            "id_oferta": oferta_id,
            "puesto": titulo,
            "empresa": empresa,
            "logo_empresa": logo_url,
            "ubicacion": ubicacion,
            "ciudad": ciudad,
            "provincia": provincia_detectada,
            "pais": "República Dominicana",
            "modalidad": "Presencial",
            "horario": "Tiempo Completo",
            "salario_mostrado": salario_tarjeta,
            "sueldo": 0,
            "sexo": "Indistinto",
            "telefono": "No especificado",
            "email": "No especificado",
            "requisitos": [],
            "beneficios": [],
            "palabras_clave": badges,
            "etiquetas": badges,
            "resumen_corto": resumen_tarjeta,
            "descripcion": resumen_tarjeta,
            "url_oferta": url_oferta,
            "url_postular": url_postular,
            "detalles": {}
        }

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

            if detalles_profundos.get("salario_estructurado") and detalles_profundos["salario_estructurado"].get("texto"):
                oferta_obj["salario_mostrado"] = detalles_profundos["salario_estructurado"]["texto"]

            if detalles_profundos.get("descripcion_completa"):
                oferta_obj["descripcion"] = detalles_profundos["descripcion_completa"]

            if detalles_profundos.get("modalidad_contrato"):
                oferta_obj["horario"] = detalles_profundos["modalidad_contrato"]

            if detalles_profundos.get("email_contacto"):
                oferta_obj["email"] = detalles_profundos["email_contacto"]
            elif oferta_obj.get("descripcion"):
                m_email = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', oferta_obj["descripcion"])
                if m_email:
                    oferta_obj["email"] = m_email.group(0).strip()

        vacantes.append(oferta_obj)

    return vacantes, fin_por_antiguedad


def scrape_vacantes(
    max_paginas: int = 1, 
    dias_max: int = 30, 
    provincia: str = "todas", 
    fetch_details: bool = True,
    limite: Optional[int] = 20000
) -> List[Dict[str, Any]]:
    """Recorre las páginas de TrabajosDiarios en todas las provincias o una específica y recopila las vacantes recientes."""
    todas_vacantes = []
    ids_registrados = set()

    url_base = construir_url_busqueda(provincia)
    fecha_referencia = datetime.now()
    fecha_limite = fecha_referencia - timedelta(days=dias_max)

    ambito_str = "Toda República Dominicana (Todas las provincias)" if provincia in ["todas", "all", "nacional", "rd"] else f"Provincia: {provincia.title()}"
    log_info(f"Ámbito territorial: {Colors.BOLD}{ambito_str}{Colors.RESET}")
    log_info(f"URL base de búsqueda: {Colors.BOLD}{url_base}{Colors.RESET}")
    log_info(f"Fecha actual (referencia): {Colors.BOLD}{fecha_referencia.strftime('%Y-%m-%d %H:%M')}{Colors.RESET}")
    log_info(f"Límite de antigüedad: {Colors.BOLD}{dias_max} días{Colors.RESET} (publicadas desde {Colors.BOLD}{fecha_limite.strftime('%Y-%m-%d')}{Colors.RESET})")
    if limite and limite > 0:
        log_info(f"Límite rápido configurado: {Colors.BOLD}máximo {limite} vacantes{Colors.RESET} para agilizar pruebas")

    for pagina in range(1, max_paginas + 1):
        url = f"{url_base}?page={pagina}" if pagina > 1 else url_base
        log_info(f"Escaneando página {pagina}: {url}")

        try:
            res = requests.get(url, headers=HEADERS, impersonate="chrome", timeout=15)
            if res.status_code != 200:
                log_warning(f"La página {pagina} devolvió status HTTP {res.status_code}. Deteniendo paginación.")
                break

            soup = BeautifulSoup(res.text, "html.parser")
            vacantes_pagina, fin_por_antiguedad = extraer_vacantes_de_tarjetas(
                soup, 
                fetch_details=fetch_details,
                fecha_referencia=fecha_referencia,
                fecha_limite=fecha_limite
            )

            nuevas = 0
            for v in vacantes_pagina:
                if v["id_oferta"] not in ids_registrados:
                    ids_registrados.add(v["id_oferta"])
                    todas_vacantes.append(v)
                    nuevas += 1
                    if limite and limite > 0 and len(todas_vacantes) >= limite:
                        break

            log_success(f"Página {pagina}: {nuevas} vacantes dentro del rango de {dias_max} días.")

            if limite and limite > 0 and len(todas_vacantes) >= limite:
                log_info(f"Se alcanzó el límite de {limite} vacantes para pruebas rápidas. Deteniendo scraping.")
                break

            if fin_por_antiguedad:
                log_info(f"Se alcanzaron vacantes anteriores al {fecha_limite.strftime('%Y-%m-%d')} (> {dias_max} días). Deteniendo escaneo.")
                break

            if nuevas == 0:
                log_info("No se encontraron nuevas vacantes en esta página. Fin del listado.")
                break

            time.sleep(0.4)

        except Exception as e:
            log_error(f"Error procesando la página {pagina}: {e}")
            break

    return todas_vacantes


def scrape_vacantes_todas_provincias(
    max_paginas_por_provincia: int = 2,
    dias_max: int = 30,
    fetch_details: bool = True
) -> List[Dict[str, Any]]:
    """
    Itera por cada provincia de República Dominicana, modificando la URL
    para escanear las vacantes de cada una y combinarlas en un único listado.
    """
    todas_vacantes = []
    ids_registrados = set()
    fecha_referencia = datetime.now()
    fecha_limite = fecha_referencia - timedelta(days=dias_max)

    log_info(f"{Colors.BOLD}Iniciando rastreo por todas las provincias ({len(PROVINCIAS_PRINCIPALES_RD)} demarcaciones)...{Colors.RESET}")

    for idx, prov in enumerate(PROVINCIAS_PRINCIPALES_RD, start=1):
        url_prov = construir_url_busqueda(prov)
        nombre_prov = prov.replace("-", " ").title()
        print(f"\n{Colors.CYAN}--- [{idx}/{len(PROVINCIAS_PRINCIPALES_RD)}] Escaneando provincia: {Colors.BOLD}{nombre_prov}{Colors.RESET} ({url_prov}) ---{Colors.RESET}")

        for pagina in range(1, max_paginas_por_provincia + 1):
            url = f"{url_prov}?page={pagina}" if pagina > 1 else url_prov
            try:
                res = requests.get(url, headers=HEADERS, impersonate="chrome", timeout=15)
                if res.status_code != 200:
                    break

                soup = BeautifulSoup(res.text, "html.parser")
                vacantes_pag, fin_antiguedad = extraer_vacantes_de_tarjetas(
                    soup,
                    fetch_details=fetch_details,
                    fecha_referencia=fecha_referencia,
                    fecha_limite=fecha_limite
                )

                nuevas_prov = 0
                for v in vacantes_pag:
                    if v["id_oferta"] not in ids_registrados:
                        ids_registrados.add(v["id_oferta"])
                        todas_vacantes.append(v)
                        nuevas_prov += 1

                log_success(f"  Pág {pagina}: {nuevas_prov} nuevas vacantes para {nombre_prov}.")

                if fin_antiguedad or nuevas_prov == 0:
                    break

                time.sleep(0.3)
            except Exception as e:
                log_error(f"Error en {nombre_prov} pág {pagina}: {e}")
                break

    return todas_vacantes


def main():
    parser = argparse.ArgumentParser(description="Scraper de Vacantes Recientes en República Dominicana (TrabajosDiarios)")
    parser.add_argument("-p", "--paginas", type=int, default=1, help="Número máximo de páginas a escanear (default: 1)")
    parser.add_argument("-l", "--limite", type=int, default=20000, help="Límite máximo de vacantes a extraer para pruebas rápidas (default: 5, use 0 para ilimitadas)")
    parser.add_argument("-d", "--dias", type=int, default=30, help="Antigüedad máxima en días (default: 30 días / 1 mes)")
    parser.add_argument("--provincia", type=str, default="todas", help="Provincia a buscar (default: 'todas' para toda República Dominicana, o ej: 'santiago', 'la-romana', 'santo-domingo', etc.)")
    parser.add_argument("--todas-provincias", action="store_true", help="Recorrer cada provincia de RD una por una modificando la URL")
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
            args.output = os.path.join(default_dir, "vacantes_trabajosdiarios_todas_provincias.json")
        elif args.provincia in ["todas", "all", "nacional", "rd"]:
            args.output = os.path.join(default_dir, "vacantes_trabajosdiarios.json")
        else:
            slug = normalizar_slug_provincia(args.provincia).replace("-", "_")
            args.output = os.path.join(default_dir, f"vacantes_trabajosdiarios_{slug}.json")

    print(f"\n{Colors.BOLD}{Colors.CYAN}==================================================================={Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}  💼 SCRAPER DE VACANTES - TRABAJOSDIARIOS (REPÚBLICA DOMINICANA)   {Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}==================================================================={Colors.RESET}\n")

    fetch_details = not args.sin_detalles
    log_info(f"Iniciando escaneo de hasta {args.paginas} página(s)...")
    log_info(f"Filtro temporal: Últimos {args.dias} días (máximo 1 mes)")
    log_info(f"Extracción profunda de descripción y requisitos: {'Activada' if fetch_details else 'Desactivada'}")

    inicio = time.time()
    if args.todas_provincias:
        vacantes = scrape_vacantes_todas_provincias(
            max_paginas_por_provincia=args.paginas,
            dias_max=args.dias,
            fetch_details=fetch_details
        )
        url_usada = f"{OFERTAS_URL} (Crawl por {len(PROVINCIAS_PRINCIPALES_RD)} provincias individuales)"
        ambito_guardado = "todas_provincias_individuales"
    else:
        vacantes = scrape_vacantes(
            max_paginas=args.paginas, 
            dias_max=args.dias, 
            provincia=args.provincia, 
            fetch_details=fetch_details,
            limite=args.limite
        )
        url_usada = construir_url_busqueda(args.provincia)
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
            "portal": "TrabajosDiarios República Dominicana",
            "url_origen": url_usada,
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

    print(f"\n{Colors.BOLD}{Colors.GREEN}======================= RESUMEN DE EXTRACCIÓN ======================={Colors.RESET}")
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
            log_success(f"¡{total_insertados} vacantes indexadas en Qdrant exitosamente!")
        except Exception as e:
            log_error(f"No se pudo completar la inserción en Qdrant: {e}")
            import traceback
            traceback.print_exc()

    print(f"{Colors.BOLD}{Colors.GREEN}====================================================================={Colors.RESET}\n")


if __name__ == "__main__":
    main()
