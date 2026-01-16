from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Any
from Qdrant_search import buscar
import httpx
import json
from IA_Chat import route as IA_Chat

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
    print('buscando vacante')
    try:
        async with httpx.AsyncClient(timeout=100) as client:
            datos = await client.post(url='http://localhost:5678/webhook/78c7647f-80d1-45ef-91f0-c83821d935e5', json=prompt.prompt)
            jsondata = datos.json()
            print(jsondata)
            if jsondata.get('res') == 'Vacio':
                print('vacio')
                return {'datos': 'Vacio'}
            return {'datos': jsondata}
    except ValueError as e:
        print(e)
# Payload: puesto, modalidad, sueldo, horario, ubicacion, descripcion, beneficios