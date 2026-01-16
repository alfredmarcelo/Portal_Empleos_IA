# Demo del sistema (aun en desarrollo)

https://github.com/user-attachments/assets/2acb73a4-ab89-4654-84b6-17ed9d57eb9c

# Descripción

Este programa es un portal de empleos en la web que hace web scraping a varias páginas de empleos populares en la República Dominicana.

El sistema obtiene los datos de una vacante y los agrega a una base de datos vectorial para que el usuario pueda buscar vacantes de forma semántica.

---

## Frameworks, tools y lenguajes

### Frontend

- React JS
- Vite (para aprovechar Preact)

### Backend

- N8n 2.1.4
- Qdrant
- Python 3.11
- FastAPI

---

## Librerías Backend

annotated-doc 0.0.4  
annotated-types 0.7.0  
anyio 4.12.0  
attrs 25.4.0  
beautifulsoup4 4.14.3  
bs4 0.0.2  
certifi 2025.11.12  
cffi 2.0.0  
charset-normalizer 3.4.4  
click 8.3.1  
colorama 0.4.6  
curl_cffi 0.14.0  
fastapi 0.128.0  
greenlet 3.3.0  
grpcio 1.76.0  
h11 0.16.0  
h2 4.3.0  
hpack 4.1.0  
httpcore 1.0.9  
httpx 0.28.1  
hyperframe 6.1.0  
idna 3.11  
numpy 2.4.0  
ollama 0.6.1  
outcome 1.3.0.post0  
pip 22.3  
playwright 1.57.0  
portalocker 3.2.0  
protobuf 6.33.2  
pycparser 2.23  
pydantic 2.12.5  
pydantic_core 2.41.5  
pyee 13.0.0  
PySocks 1.7.1  
pywin32 311  
qdrant-client 1.16.2  
requests 2.32.5  
selenium 4.39.0  
setuptools 65.5.0  
sniffio 1.3.1  
sortedcontainers 2.4.0  
soupsieve 2.8.1  
starlette 0.50.0  
trio 0.32.0  
trio-websocket 0.12.2  
typing_extensions 4.15.0  
typing-inspection 0.4.2  
urllib3 2.6.2  
uvicorn 0.40.0  
websocket-client 1.9.0  
wsproto 1.3.2

---

## Librerías Frontend

@eslint/js@9.39.2  
@types/react-dom@19.2.3  
@types/react@19.2.7  
@vitejs/plugin-react@5.1.2  
babel-plugin-react-compiler@1.0.0  
eslint-plugin-react-hooks@7.0.1  
eslint-plugin-react-refresh@0.4.26  
eslint@9.39.2  
globals@16.5.0  
leaflet@1.9.4  
react-dom@19.2.3  
react-leaflet@5.0.0-rc.2  
react-markdown@10.1.0  
react@19.2.3  
vite@7.3.0

---

## Bugs y cosas a mejorar

- El mapa tiene problemas al buscar algunas coordenadas.
- El filtrado de datos es vago; se requiere una búsqueda más detallada de las vacantes.
- El white mode está mal implementado (utilizar solo dark mode).
- Fallos con la IA y el workflow de n8n.
