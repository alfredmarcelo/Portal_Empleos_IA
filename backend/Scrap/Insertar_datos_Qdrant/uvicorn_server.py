from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Any
from Qdrant_search import buscar
import httpx
import json
from IA_Chat import route as IA_Chat

COORDS_RD = {
    'la romana': (18.4273, -68.9728),
    'santo domingo este': (18.4884, -69.8571),
    'santo domingo oeste': (18.4905, -69.9912),
    'herrera': (18.4682, -69.9733),
    'bavaro': (18.6813, -68.4443),
    'bávaro': (18.6813, -68.4443),
    'punta cana': (18.5601, -68.3725),
    'hato del yaque': (19.4358, -70.7672),
    'santiago': (19.4517, -70.6970),
    'santiago de los caballeros': (19.4517, -70.6970),
    'el millón': (18.4687, -69.9472),
    'el millon': (18.4687, -69.9472),
    'sector renacimiento': (18.4485, -69.9675),
    'renacimiento': (18.4485, -69.9675),
    'winston churchill': (18.4719, -69.9405),
    'piantini': (18.4740, -69.9360),
    'naco': (18.4764, -69.9270),
    'bella vista': (18.4550, -69.9500),
    'barahona': (18.2085, -71.1008),
    'san juan': (18.8059, -71.2299),
    'ciudad nueva': (18.4716, -69.8890),
    'zona colonial': (18.4735, -69.8856),
    'distrito nacional': (18.4861, -69.9312),
    'santo domingo': (18.4861, -69.9312),
}

def resolver_coordenadas(payload: dict) -> tuple:
    lat = payload.get('latitud')
    lng = payload.get('longitud')
    if lat is not None and lng is not None:
        try:
            return float(lat), float(lng)
        except (ValueError, TypeError):
            pass
    texto = f"{payload.get('Ubicacion', '')} {payload.get('Direccion', '')} {payload.get('sector', '')}".lower()
    for k, v in COORDS_RD.items():
        if k in texto:
            return v
    return 18.4861, -69.9312

app = FastAPI()
app.include_router(IA_Chat)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class datos(BaseModel):
    payloads: Any
    texto: str

class user_prompt(BaseModel):
    prompt: str

@app.post('/prueba/')
def obtener_datos(datos: datos):
    datos = buscar(datos)
    return datos

@app.post('/pruebas_frontend/')
async def obtener_prompt_usuario(prompt: user_prompt):
    print(f'buscando vacante para prompt: "{prompt.prompt}"')
    # 1. Intentar a través de n8n si está disponible
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            resp = await client.post(
                url='http://localhost:5678/webhook-test/78c7647f-80d1-45ef-91f0-c83821d935e5',
                json=prompt.prompt
            )
            if resp.status_code == 200:
                jsondata = resp.json()
                print("Respuesta de n8n recibida exitosamente")
                if jsondata.get('res') == 'Vacio':
                    return {'datos': 'Vacio'}
                return {'datos': jsondata}
            else:
                print(f"n8n retornó código {resp.status_code}, usando búsqueda directa en Qdrant...")
    except Exception as e:
        print(f"n8n no disponible o timeout ({e}), usando búsqueda directa en Qdrant...")

    # 2. Fallback directo a Qdrant si n8n no responde
    try:
        qdrant_res = buscar(datos(payloads={}, texto=prompt.prompt))
        puntos = getattr(qdrant_res, 'points', [])
        if not puntos:
            print("No se encontraron puntos en Qdrant")
            return {'datos': 'Vacio'}

        vacantes_list = []
        for p in puntos:
            payload = getattr(p, 'payload', {}) or {}
            c_lat, c_lng = resolver_coordenadas(payload)
            payload['latitud'] = c_lat
            payload['longitud'] = c_lng
            vacantes_list.append({
                "id": getattr(p, 'id', None),
                "payload": payload
            })

        top_puestos = [v['payload'].get('Puesto', '') for v in vacantes_list[:5] if v['payload'].get('Puesto')]
        resumen_bullets = "\n".join([f"- **{p}**" for p in top_puestos])

        ia_text = (
            f"### Resultados de la Búsqueda 🎯\n\n"
            f"Hemos identificado **{len(vacantes_list)} vacantes** que coinciden con tu búsqueda de **'{prompt.prompt}'**:\n\n"
            f"{resumen_bullets}\n\n"
            f"💡 *Selecciona cualquier vacante en la lista para ver la ubicación en el mapa, cálculo de distancia, sueldo y aplicar.*"
        )

        return {
            'datos': {
                'IA_text': ia_text,
                'Vacantes': vacantes_list
            }
        }
    except Exception as e:
        print(f"Error en búsqueda directa de Qdrant: {e}")
        return {'datos': 'Vacio'}