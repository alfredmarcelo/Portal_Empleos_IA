from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any
import httpx

route = APIRouter(prefix="/users", tags=["users"])

class prompt(BaseModel):
    ususario_respuesta: str

@route.post('/Chat_llm/')
async def Abrir_session_Chat(usuario_respuesta: prompt):
    try:
        print(usuario_respuesta.ususario_respuesta)
        async with httpx.AsyncClient(timeout=None) as cliente:
            datos = await cliente.post("http://localhost:5678/webhook-test/991a6068-7070-4be8-8515-898a5c9e5579", json=usuario_respuesta.ususario_respuesta)
            print(datos.text)
        return datos.json()
    except ValueError as e:
        print(e)