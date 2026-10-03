#!/usr/bin/env python3
"""
Módulo de Geolocalización y Búsqueda de Ubicación Exacta con IA
===============================================================
Este módulo actúa como proceso independiente o post-proceso tras el scraping:
1. Utiliza la IA de Ollama para analizar la vacante, el nombre de la empresa,
   sucursales, plazas, avenidas y zonas industriales en República Dominicana.
2. Deduce la dirección física exacta o la zona/sector más preciso donde opera el negocio.
3. Consulta OpenStreetMap (Nominatim) para obtener coordenadas GPS (latitud y longitud),
   permitiendo la visualización precisa en mapas y cálculo de distancia.
"""

import os
import sys
import re
import json
import time
import argparse
from typing import List, Dict, Any, Optional, Tuple

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
    print(f"{Colors.CYAN}📍 [INFO UBICACIÓN]{Colors.RESET} {msg}")


def log_success(msg: str):
    print(f"{Colors.GREEN}✔ [ÉXITO UBICACIÓN]{Colors.RESET} {msg}")


def log_warning(msg: str):
    print(f"{Colors.YELLOW}⚠ [ALERTA UBICACIÓN]{Colors.RESET} {msg}")


def log_error(msg: str):
    print(f"{Colors.RED}✖ [ERROR UBICACIÓN]{Colors.RESET} {msg}")


class LocalizadorUbicacionIA:
    """Identifica la dirección física exacta de un negocio con IA y obtiene sus coordenadas GPS."""

    def __init__(
        self,
        host: str = "http://localhost:11434",
        model: str = "maternion/ling-3.0-tiny:8b"
    ):
        self.host = host.rstrip('/')
        self.model = model
        self.geo_cache: Dict[str, Tuple[Optional[float], Optional[float], str]] = {}

    def _limpiar_json(self, raw_text: str) -> str:
        """Extrae el bloque JSON limpio descartando reflexiones <think>."""
        if not raw_text:
            return "{}"
        if "</think>" in raw_text:
            raw_text = raw_text.split("</think>")[-1].strip()
        else:
            raw_text = re.sub(r'<think>.*?</think>', '', raw_text, flags=re.DOTALL).strip()

        match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_text, flags=re.DOTALL)
        if match:
            return match.group(1).strip()

        inicio = raw_text.find('{')
        fin = raw_text.rfind('}')
        if inicio != -1 and fin != -1 and fin > inicio:
            return raw_text[inicio:fin + 1].strip()

        return raw_text.strip()

    def geocodificar(self, query: str) -> Tuple[Optional[float], Optional[float], str]:
        """Obtiene latitud y longitud de OpenStreetMap (Nominatim) con caché en memoria."""
        if not query or query in self.geo_cache:
            return self.geo_cache.get(query, (None, None, ""))

        try:
            url = "https://nominatim.openstreetmap.org/search"
            params = {
                "q": query,
                "format": "json",
                "limit": 1,
                "countrycodes": "do"
            }
            headers = {"User-Agent": "PortalEmpleosRD-GeoEngine/1.0"}
            
            res = requests.get(url, params=params, headers=headers, timeout=8)
            if res.status_code == 200:
                data = res.json()
                if data and isinstance(data, list) and len(data) > 0:
                    lat = float(data[0].get("lat", 0.0))
                    lon = float(data[0].get("lon", 0.0))
                    display = data[0].get("display_name", "")
                    self.geo_cache[query] = (lat, lon, display)
                    return lat, lon, display
        except Exception:
            pass

        self.geo_cache[query] = (None, None, "")
        return None, None, ""

    def buscar_ubicacion_negocio(self, vacante: Dict[str, Any], timeout: int = 40) -> Dict[str, Any]:
        """
        Analiza con IA la empresa y el texto de la vacante para determinar
        la dirección física más exacta posible en República Dominicana.
        """
        empresa = vacante.get("empresa") or "Confidencial"
        puesto = vacante.get("puesto") or "Puesto de empleo"
        ubicacion_gen = vacante.get("ubicacion") or vacante.get("ciudad") or "República Dominicana"

        # Evitar que nombres de cargos pasen como empresas
        terminos_cargo = ["camarero", "chofer", "vendedor", "cajero", "asistente", "secretaria", "mantenimiento"]
        if any(empresa.lower() == t for t in terminos_cargo) or empresa.lower() in ["desconocido", "none", ""]:
            empresa = "Confidencial"
        
        detalles = vacante.get("detalles", {})
        texto_vacante = (
            vacante.get("descripcion")
            or detalles.get("descripcion_completa")
            or vacante.get("resumen_corto")
            or ""
        )

        prompt = (
            "Eres un experto en geolocalización, urbanismo y empresas en República Dominicana.\n"
            "Tu objetivo es identificar la UBICACIÓN EXACTA o la más precisa posible del negocio o lugar de trabajo.\n\n"
            f"- Empresa: {empresa}\n"
            f"- Puesto: {puesto}\n"
            f"- Ubicación general indicada: {ubicacion_gen}\n"
            f"- Contenido de la oferta:\n'''\n{texto_vacante[:2000]}\n'''\n\n"
            "Instrucciones:\n"
            "1. NO INVENTES DIRECCIONES NI EMPRESAS. Si un dato no se conoce con certeza, usa 'Desconocido' o la zona general.\n"
            "2. Busca menciones de calles, avenidas principales, números, esquinas, plazas comerciales (ej. BlueMall, Sambil, Ágora), "
            "parques industriales, zonas francas (ej. Haina, San Isidro, La Vega), o barrios/sectores específicos (ej. Piantini, Naco, Bella Vista, Herrera, Renacimiento, Villa Juana, Gurabo, Bávaro, etc.).\n"
            "3. Si la empresa es 'Confidencial' o no se conoce, NUNCA inventes una empresa. Céntrate en extraer el sector o municipio del puesto de trabajo según el texto.\n"
            "4. Si la empresa es conocida en RD o se indica la sucursal o lugar exacto en el texto (ej. 'Lugar: Dumplings Express, Sector: Renacimiento'), usa esa información real.\n\n"
            "Responde ÚNICAMENTE con un JSON válido con este formato:\n"
            "{\n"
            '  "direccion_exacta": "Calle, avenida, plaza, sector y ciudad (lo más preciso posible)",\n'
            '  "sector": "Nombre del sector, barrio o parque industrial",\n'
            '  "ciudad": "Municipio o ciudad (ej: Santo Domingo de Guzmán, Santo Domingo Este, Santiago)",\n'
            '  "provincia": "Provincia (ej: Distrito Nacional, Santo Domingo, Santiago)",\n'
            '  "referencia": "Punto de referencia o indicación de cómo llegar"\n'
            "}"
        )

        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "think": False,
            "options": {"temperature": 0.1}
        }

        try:
            res = requests.post(url, json=payload, timeout=timeout)
            res.raise_for_status()
            res_data = res.json()
            raw = res_data.get("response") or res_data.get("thinking") or ""
            data_loc = json.loads(self._limpiar_json(raw))

            sector = (data_loc.get("sector") or "").strip()
            if not sector or sector.lower() in ["desconocido", "desconocida", "no especificado", "none", "null"]:
                sector = vacante.get("ciudad") or ubicacion_gen

            ciudad = (data_loc.get("ciudad") or "").strip()
            if not ciudad or ciudad.lower() in ["desconocido", "desconocida", "no especificado", "none", "null"]:
                ciudad = vacante.get("ciudad") or ubicacion_gen

            provincia = (data_loc.get("provincia") or "").strip()
            if not provincia or provincia.lower() in ["desconocido", "desconocida", "no especificado", "none", "null"]:
                provincia = vacante.get("provincia") or ciudad

            dir_exacta = (data_loc.get("direccion_exacta") or "").strip()
            if not dir_exacta or dir_exacta.lower() in ["desconocido", "desconocida", "no especificado", "none", "null"]:
                if sector and sector.lower() != ciudad.lower():
                    dir_exacta = f"{sector}, {ciudad}"
                else:
                    dir_exacta = f"{ciudad}, República Dominicana"

            referencia = data_loc.get("referencia") or ""

            # Geocodificar en OpenStreetMap
            lat, lon, display = None, None, ""
            
            # Intento 1: Dirección exacta + RD
            query_1 = f"{dir_exacta}, República Dominicana"
            lat, lon, display = self.geocodificar(query_1)

            # Intento 2: Sector + Ciudad + RD
            if lat is None and sector:
                query_2 = f"{sector}, {ciudad}, República Dominicana"
                lat, lon, display = self.geocodificar(query_2)

            # Intento 3: Ciudad + RD
            if lat is None and ciudad:
                query_3 = f"{ciudad}, República Dominicana"
                lat, lon, display = self.geocodificar(query_3)

            # Enriquecer vacante solo con latitud y longitud (sin duplicar campos)
            vacante["latitud"] = lat
            vacante["longitud"] = lon
            if sector and sector.lower() not in ["desconocido", "desconocida", "no especificado", "none", "null", "república dominicana"]:
                if sector.lower() != vacante.get("ciudad", "").lower() and sector.lower() != vacante.get("ubicacion", "").lower():
                    vacante["sector"] = sector

            return vacante

        except Exception as e:
            log_warning(f"No se pudo determinar ubicación exacta de '{empresa}' ({e}).")
            lat, lon, _ = self.geocodificar(f"{ubicacion_gen}, República Dominicana")
            vacante["latitud"] = lat
            vacante["longitud"] = lon
            return vacante

    def localizar_lote(
        self,
        vacantes: List[Dict[str, Any]],
        max_items: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Procesa la ubicación exacta de un lote de vacantes como proceso separado."""
        total = len(vacantes) if max_items is None else min(len(vacantes), max_items)
        if total == 0:
            return vacantes

        print(f"\n{Colors.BOLD}{Colors.CYAN}==================================================================={Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}  📍 GEOLOCALIZACIÓN Y BÚSQUEDA DE UBICACIÓN EXACTA DE NEGOCIOS     {Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.CYAN}==================================================================={Colors.RESET}")
        log_info(f"Localizando dirección exacta y coordenadas para {Colors.BOLD}{total}{Colors.RESET} negocios...")

        t_inicio = time.time()
        for idx, vacante in enumerate(vacantes[:total], start=1):
            empresa = vacante.get("empresa") or "Empresa"
            ub_previa = vacante.get("ubicacion") or "RD"
            print(f"  [{idx}/{total}] Localizando negocio: {Colors.BOLD}{empresa[:35]}{Colors.RESET} ({ub_previa})...")

            self.buscar_ubicacion_negocio(vacante)
            lat = vacante.get("latitud")
            lon = vacante.get("longitud")
            sector = vacante.get("sector") or vacante.get("ubicacion", "")

            coords_str = f"(GPS: {lat:.4f}, {lon:.4f})" if lat and lon else "(GPS no disponible)"
            print(f"       ✔ Ubicación: {Colors.GREEN}{sector}{Colors.RESET} {coords_str}")
            time.sleep(0.3)  # Pausa respetuosa para OpenStreetMap

        t_total = time.time() - t_inicio
        print(f"{Colors.BOLD}{Colors.GREEN}-------------------------------------------------------------------{Colors.RESET}")
        log_success(f"Geolocalización completada para {total} vacantes en {t_total:.1f}s")
        print(f"{Colors.BOLD}{Colors.GREEN}==================================================================={Colors.RESET}\n")

        return vacantes


def main():
    parser = argparse.ArgumentParser(description="Proceso independiente de búsqueda de ubicación exacta y geocodificación con IA")
    parser.add_argument("archivo", type=str, help="Ruta al archivo JSON de vacantes")
    parser.add_argument("-o", "--output", type=str, default=None, help="Ruta de salida (por defecto sobrescribe)")
    parser.add_argument("-m", "--model", type=str, default="maternion/ling-3.0-tiny:8b", help="Modelo de Ollama")
    parser.add_argument("--host", type=str, default="http://localhost:11434", help="Host de Ollama")
    parser.add_argument("-l", "--limite", type=int, default=20000, help="Límite de vacantes a geolocalizar")
    args = parser.parse_args()

    if not os.path.exists(args.archivo):
        log_error(f"No existe el archivo: {args.archivo}")
        sys.exit(1)

    with open(args.archivo, "r", encoding="utf-8") as f:
        data = json.load(f)

    vacantes = data.get("vacantes", data if isinstance(data, list) else [])
    localizador = LocalizadorUbicacionIA(host=args.host, model=args.model)
    localizadas = localizador.localizar_lote(vacantes, max_items=args.limite)

    out = args.output or args.archivo
    if isinstance(data, dict) and "vacantes" in data:
        data["vacantes"] = localizadas
        data["metadata"] = data.get("metadata", {})
        data["metadata"]["geolocalizado_con_ia"] = True
        data["metadata"]["fecha_geolocalizacion"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        a_guardar = data
    else:
        a_guardar = localizadas

    with open(out, "w", encoding="utf-8") as f:
        json.dump(a_guardar, f, ensure_ascii=False, indent=2)

    log_success(f"Archivo geolocalizado guardado en: {out}")


if __name__ == "__main__":
    main()
