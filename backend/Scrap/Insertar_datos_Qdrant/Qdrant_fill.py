#!/usr/bin/env python3
"""
Inserción de Vacantes en Base de Datos Vectorial Qdrant
======================================================
Este script toma el JSON de vacantes extraídas (por ejemplo, el generado por
'Aplicacion_automatica/Scrap_prueba.py' o 'prueba_vacantes.json'),
genera embeddings vectoriales usando Ollama ('nomic-embed-text:latest')
y los indexa en Qdrant para permitir búsqueda semántica y filtros.
"""

import sys
import os
import re
import json
import time
import argparse
from typing import List, Dict, Any, Optional, Union

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from ollama import Client

# Rutas predeterminadas
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
DEFAULT_JSON_CANDIDATES = [
    os.path.join(BASE_DIR, "Scrap/vacantes_trabajosdiarios.json"),
    os.path.join(BASE_DIR, "Scrap/vacantes_tuempleord.json"),
    os.path.join(BASE_DIR, "Scrap/vacantes_santo_domingo_este.json"),
    os.path.join(BASE_DIR, "Aplicacion_automatica/vacantes_santo_domingo_este.json"),
    os.path.join(BASE_DIR, "prueba_vacantes.json"),
    os.path.join(BASE_DIR, "ofertas_tuempleord_2026-01-14.json")
]

DEFAULT_COLLECTION = "vacantes_prueba"
DEFAULT_EMBED_MODEL = "nomic-embed-text-v2-moe:latest"

# Colores para consola
class Colors:
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


def convertir_texto_a_lenguaje_natural(v: Dict[str, Any]) -> str:
    """Convierte una vacante en una descripción textual rica para calcular su vector semántico."""
    puesto = v.get("puesto") or v.get("Puesto") or "Puesto de empleo"
    empresa = v.get("empresa") or v.get("Nombre_Empresa") or "Empresa confidencial"
    ubicacion = v.get("ubicacion") or v.get("Ubicacion") or "Santo Domingo"
    ciudad = v.get("ciudad") or "Santo Domingo Este"
    modalidad = v.get("modalidad") or v.get("Modalidad") or "Presencial"
    sueldo_txt = v.get("salario_mostrado") or v.get("Sueldo") or "A convenir"

    detalles = v.get("detalles", {})
    desc = detalles.get("descripcion_completa") or v.get("descripcion") or v.get("Descripcion") or v.get("resumen_corto") or ""
    requisitos = detalles.get("requisitos_educativos") or ""
    
    etiquetas = v.get("etiquetas") or v.get("Beneficios") or v.get("Palabras_clave") or []
    etiquetas_str = ", ".join(etiquetas) if isinstance(etiquetas, list) else str(etiquetas)

    return (
        f"Oferta de empleo: {puesto} en la empresa {empresa}. "
        f"Ubicación: {ubicacion} ({ciudad}). Modalidad de trabajo: {modalidad}. "
        f"Compensación/Salario: {sueldo_txt}. "
        f"Requisitos y formación: {requisitos}. "
        f"Detalles y funciones del puesto: {desc[:1500]} "
        f"Beneficios y características: {etiquetas_str}"
    ).strip()


def extraer_sueldo_numerico(v: Dict[str, Any]) -> int:
    """Extrae un valor numérico entero del sueldo para posibilitar filtros numéricos en Qdrant."""
    # 1. Intentar desde salario estructurado
    detalles = v.get("detalles") or {}
    sal_est = detalles.get("salario_estructurado") or {}
    monto = sal_est.get("monto")
    if monto:
        try:
            return int(float(monto))
        except (ValueError, TypeError):
            pass

    # 2. Intentar desde campo sueldo directo
    sueldo_raw = v.get("sueldo") or v.get("Sueldo")
    if isinstance(sueldo_raw, (int, float)):
        return int(sueldo_raw)
    elif isinstance(sueldo_raw, str):
        numeros = re.findall(r'[\d,]+', sueldo_raw)
        if numeros:
            try:
                return int(float(numeros[0].replace(',', '')))
            except ValueError:
                pass

    # 3. Intentar desde salario mostrado
    salario_txt = v.get("salario_mostrado", "")
    if salario_txt:
        numeros = re.findall(r'[\d,]+', str(salario_txt).replace('$', ''))
        for n in numeros:
            limpio = n.replace(',', '')
            if limpio.isdigit() and int(limpio) >= 1000:
                return int(limpio)

    return 0


def cargar_vacantes_de_archivo(ruta_archivo: str) -> List[Dict[str, Any]]:
    """Carga y normaliza la lista de vacantes desde un archivo JSON."""
    if not os.path.exists(ruta_archivo):
        raise FileNotFoundError(f"No se encontró el archivo: {ruta_archivo}")

    with open(ruta_archivo, "r", encoding="utf-8") as f:
        content = f.read().strip()

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        # Intento de recuperación si es una secuencia de objetos {...}, {...} sin [ ... ]
        try:
            repaired = "[" + content.rstrip().rstrip(",") + "]"
            data = json.loads(repaired)
        except Exception:
            raise ValueError(f"No se pudo parsear el archivo JSON: {ruta_archivo}")

    if isinstance(data, dict):
        if "vacantes" in data and isinstance(data["vacantes"], list):
            return data["vacantes"]
        elif "oferta" in data and isinstance(data["oferta"], list):
            return data["oferta"]
        elif "ofertas" in data and isinstance(data["ofertas"], list):
            return data["ofertas"]
    elif isinstance(data, list):
        return data

    raise ValueError(f"Formato no reconocido en el JSON: {ruta_archivo}")


def insertar_vacantes_en_qdrant(
    archivo_json: Optional[Union[str, List[str]]] = None,
    collection_name: str = DEFAULT_COLLECTION,
    qdrant_host: str = "localhost",
    qdrant_port: int = 6333,
    ollama_host: str = "http://localhost:11434",
    embed_model: str = DEFAULT_EMBED_MODEL,
    recreate: bool = False
) -> int:
    """Función principal para generar embeddings e insertar vacantes en Qdrant desde uno o varios JSONs."""

    # 1. Determinar lista de archivos JSON a procesar
    archivos_a_cargar: List[str] = []
    if isinstance(archivo_json, str):
        archivos_a_cargar = [archivo_json]
    elif isinstance(archivo_json, list):
        archivos_a_cargar = [f for f in archivo_json if f]

    if not archivos_a_cargar:
        # Cargar todos los archivos válidos candidatos por defecto
        for candidato in DEFAULT_JSON_CANDIDATES:
            if os.path.exists(candidato) and os.path.getsize(candidato) > 10:
                if candidato not in archivos_a_cargar:
                    archivos_a_cargar.append(candidato)

    if not archivos_a_cargar:
        raise FileNotFoundError(
            "No se encontró ningún archivo JSON de vacantes disponible. "
            "Ejecuta primero: python Scrap/Scrap_TuEmpleoRD.py o Scrap_TrabajosDiarios.py"
        )

    log_info(f"Archivos JSON a indexar ({len(archivos_a_cargar)}):")
    for r in archivos_a_cargar:
        log_info(f"  📁 {Colors.BOLD}{r}{Colors.RESET}")

    vacantes: List[Dict[str, Any]] = []
    claves_vistas = set()
    for ruta in archivos_a_cargar:
        if not os.path.exists(ruta):
            log_warning(f"No existe el archivo: {ruta}")
            continue
        try:
            vacs = cargar_vacantes_de_archivo(ruta)
            log_info(f"  -> {len(vacs)} vacantes leídas de {os.path.basename(ruta)}")
            for v in vacs:
                # Deduplicar por URL o (puesto, empresa, id_oferta)
                clave_dedup = v.get("url_oferta") or v.get("url") or f"{v.get('puesto')}_{v.get('empresa')}_{v.get('id_oferta')}"
                if clave_dedup and clave_dedup in claves_vistas:
                    continue
                claves_vistas.add(clave_dedup)
                vacantes.append(v)
        except Exception as e:
            log_warning(f"Error cargando {ruta}: {e}")

    log_info(f"Total combinado de vacantes únicas a indexar: {Colors.BOLD}{len(vacantes)}{Colors.RESET}")

    if not vacantes:
        log_warning("No se encontraron vacantes para insertar.")
        return 0

    # 2. Conectar a Qdrant y Ollama
    log_info(f"Conectando a Qdrant ({qdrant_host}:{qdrant_port})...")
    try:
        cliente_qdrant = QdrantClient(host=qdrant_host, port=qdrant_port, timeout=10)
        # Probar conexión
        cliente_qdrant.get_collections()
        log_success("Conexión con Qdrant exitosa.")
    except Exception as e:
        log_error(f"No se pudo conectar a Qdrant en {qdrant_host}:{qdrant_port}: {e}")
        log_error("¿Está Qdrant iniciado? Ejecuta: docker start Qdrant")
        sys.exit(1)

    log_info(f"Conectando a Ollama ({ollama_host}) con modelo de embeddings '{embed_model}'...")
    try:
        ollama_client = Client(host=ollama_host)
        test_emb = ollama_client.embeddings(model=embed_model, prompt="test")
        dim_vector = len(test_emb["embedding"])
        log_success(f"Modelo de embeddings activo. Dimensión del vector: {dim_vector}")
    except Exception as e:
        log_error(f"Error al conectar con Ollama o modelo '{embed_model}': {e}")
        sys.exit(1)

    # 3. Validar o crear colección en Qdrant
    if recreate and cliente_qdrant.collection_exists(collection_name):
        log_info(f"Eliminando colección existente '{collection_name}' para recreación limpia...")
        cliente_qdrant.delete_collection(collection_name)

    if not cliente_qdrant.collection_exists(collection_name):
        log_info(f"Creando colección '{collection_name}' (vector size={dim_vector})...")
        cliente_qdrant.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=dim_vector, distance=Distance.COSINE),
        )
        log_success(f"Colección '{collection_name}' creada exitosamente.")
    else:
        # Verificar que la dimensión coincida
        coll_info = cliente_qdrant.get_collection(collection_name)
        existing_size = coll_info.config.params.vectors.size
        if existing_size != dim_vector:
            log_warning(f"Dimensión de colección existente ({existing_size}) no coincide con el modelo ({dim_vector}). Recreando...")
            cliente_qdrant.delete_collection(collection_name)
            cliente_qdrant.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=dim_vector, distance=Distance.COSINE),
            )
            log_success(f"Colección '{collection_name}' recreada con tamaño {dim_vector}.")

    # 4. Procesar e insertar puntos
    puntos = []
    ids_usados = set()
    log_info("Generando embeddings semánticos e indexando en Qdrant...")

    for idx, v in enumerate(vacantes):
        texto_natural = convertir_texto_a_lenguaje_natural(v)
        
        try:
            emb_res = ollama_client.embeddings(model=embed_model, prompt=texto_natural)
            vector = emb_res["embedding"]
        except Exception as e:
            log_warning(f"Error al generar embedding para vacante {idx + 1}: {e}")
            continue

        # ID único numérico garantizado sin colisiones
        point_id = idx + 1
        raw_id = v.get("id_oferta")
        if raw_id and str(raw_id).isdigit() and int(raw_id) not in ids_usados:
            point_id = int(raw_id)
        else:
            cand_id = idx + 1
            while cand_id in ids_usados:
                cand_id += 100000
            point_id = cand_id
        ids_usados.add(point_id)

        # Sueldo numérico
        sueldo_val = extraer_sueldo_numerico(v)

        # Modalidad y horario
        modalidad = v.get("modalidad") or v.get("Modalidad") or "Presencial"
        horario = v.get("horario") or v.get("Horario") or "Tiempo Completo"
        if "Tiempo Completo" in v.get("etiquetas", []):
            horario = "Tiempo Completo"

        # Armar payload limpio y estructurado (sin claves repetidas)
        puesto = v.get("Puesto") or v.get("puesto") or "Puesto no especificado"
        empresa = v.get("Nombre_Empresa") or v.get("empresa") or "Confidencial"
        ubicacion = v.get("Ubicacion") or v.get("ubicacion") or "Santo Domingo Este"
        url = v.get("URL") or v.get("url_oferta") or v.get("url") or ""
        url_postular = v.get("url_postular") or ""
        fecha_pub = v.get("Fecha_Publicacion") or v.get("fecha_publicacion") or ""
        fecha_exp = v.get("detalles", {}).get("fecha_expiracion") or v.get("Fecha_Expiracion") or v.get("fecha_expiracion") or ""
        desc_completa = v.get("detalles", {}).get("descripcion_completa") or v.get("Descripcion") or v.get("descripcion") or v.get("resumen_corto") or ""
        
        etiquetas = v.get("Beneficios") or v.get("beneficios") or v.get("etiquetas") or []
        if isinstance(etiquetas, str):
            etiquetas = [e.strip() for e in etiquetas.split(",") if e.strip()]

        # Generar lista de palabras clave únicas
        palabras_clave = list(dict.fromkeys(
            [w for w in [puesto.lower(), empresa.lower()] + [e.lower() for e in etiquetas if e] if w]
        ))

        payload = {
            "id_oferta": point_id,
            "Puesto": puesto,
            "Nombre_Empresa": empresa,
            "Modalidad": modalidad,
            "Sueldo": sueldo_val,
            "Sueldo_Texto": v.get("salario_mostrado") or v.get("Sueldo_Texto") or (f"RD$ {sueldo_val:,}" if sueldo_val else "No especificado"),
            "Horario": horario,
            "Ubicacion": ubicacion,
            "Direccion": v.get("Direccion") or v.get("direccion_exacta") or v.get("direccion") or v.get("ciudad") or "Santo Domingo Este",
            "latitud": v.get("latitud"),
            "longitud": v.get("longitud"),
            "sector": v.get("sector") or v.get("ciudad") or ubicacion,
            "Fecha_Publicacion": fecha_pub,
            "Fecha_Expiracion": fecha_exp,
            "Sexo": v.get("Sexo") or v.get("sexo") or "No especificado",
            "Numero_Telefono": v.get("Numero_Telefono") or v.get("telefono") or "No especificado",
            "Email": v.get("Email") or v.get("email") or "No especificado",
            "Descripcion": desc_completa,
            "Beneficios": etiquetas,
            "Palabras_clave": palabras_clave,
            "URL": url,
            "url_postular": url_postular
        }

        puntos.append(PointStruct(id=point_id, vector=vector, payload=payload))

        if (idx + 1) % 5 == 0 or (idx + 1) == len(vacantes):
            print(f"  -> Procesadas {idx + 1}/{len(vacantes)} vacantes...")

    # 5. Upsert en batch
    log_info(f"Insertando {len(puntos)} puntos en la colección '{collection_name}'...")
    cliente_qdrant.upsert(collection_name=collection_name, points=puntos)
    log_success(f"¡Insertadas exitosamente {len(puntos)} vacantes en Qdrant!")

    # 6. Verificación rápida de conteo
    conteo = cliente_qdrant.count(collection_name=collection_name).count
    log_info(f"Total de registros actuales en '{collection_name}': {Colors.BOLD}{conteo}{Colors.RESET}")

    return len(puntos)


def main():
    parser = argparse.ArgumentParser(description="Insertar vacantes estructuradas en Qdrant con embeddings de Ollama")
    parser.add_argument("-j", "--json", nargs="*", default=None, help="Ruta o rutas a archivos JSON con vacantes (default: carga todos los JSONs disponibles)")
    parser.add_argument("-c", "--collection", type=str, default=DEFAULT_COLLECTION, help="Nombre de la colección en Qdrant")
    parser.add_argument("-m", "--model", type=str, default=DEFAULT_EMBED_MODEL, help="Modelo de embeddings en Ollama")
    parser.add_argument("--host", type=str, default="localhost", help="Host de Qdrant (default: localhost)")
    parser.add_argument("--port", type=int, default=6333, help="Puerto de Qdrant (default: 6333)")
    parser.add_argument("--recreate", action="store_true", help="Eliminar y recrear la colección desde cero")
    args = parser.parse_args()

    print(f"\n{Colors.BOLD}{Colors.CYAN}==================================================================={Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}     📥 INSERCIÓN DE VACANTES EN QDRANT (EMBEDDINGS OLLAMA)        {Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}==================================================================={Colors.RESET}\n")

    t0 = time.time()
    try:
        total = insertar_vacantes_en_qdrant(
            archivo_json=args.json,
            collection_name=args.collection,
            qdrant_host=args.host,
            qdrant_port=args.port,
            embed_model=args.model,
            recreate=args.recreate
        )
        duracion = time.time() - t0
        print(f"\n{Colors.BOLD}{Colors.GREEN}==================================================================={Colors.RESET}")
        log_success(f"Proceso finalizado: {total} vacantes indexadas en {duracion:.2f}s")
        print(f"{Colors.BOLD}{Colors.GREEN}==================================================================={Colors.RESET}\n")
    except Exception as e:
        log_error(f"Ocurrió un error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()