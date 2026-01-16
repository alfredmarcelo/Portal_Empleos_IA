from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance, Filter, FieldCondition, MatchValue
from ollama import Client
import json

cliente = QdrantClient(host='localhost', port=6333)
ollama_model = Client(host='http://localhost:11434/')

def Convertir_texto_a_lenguaje_natural(v):
    beneficios = ", ".join(v["Beneficios"])
    return (
        f"Se busca {v['Puesto']} en modalidad {v['Modalidad']} "
        f"ubicado en {v['Ubicacion']}. "
        f"El horario es {v['Horario']}. "
        f"{v['Descripcion']} "
        f"Ofrece beneficios como {beneficios}."
    )


# vacante_prueba = ollama_model.embeddings(model="nomic-embed-text:latest", prompt=prompt)

# search = ollama_model.embed(model="nomic-embed-text:latest", input='busco una vacante de barbero con sueldo menor a 20000')
# result = cliente.query_points(
#     collection_name="vacantes_prueba",
#     query=search['embeddings'][0],
#     with_payload=True,
#     score_threshold=0.6,
#     limit=100
# ) 

# print(result)

with open('ofertas_tuempleord_2026-01-14.json', 'r', encoding='utf-8') as e:
    prompt = json.load(e)

try:
    for e, i in enumerate(prompt['oferta']):

        texto = Convertir_texto_a_lenguaje_natural(i)

        for h in i:
            vacante_prueba = ollama_model.embeddings(model="qwen3-embedding:8b", prompt=h.lower())

        if not cliente.collection_exists("vacantes_prueba"):
            cliente.create_collection(
                collection_name="vacantes_prueba",
                vectors_config=VectorParams(size=4096, distance=Distance.COSINE),
            )
            print('Coleccion Creada!')

        if cliente.collection_exists("vacantes_prueba"):
            
            metadata = PointStruct(
                    id=e,
                    vector=vacante_prueba["embedding"],
                    payload={
                        "URL": i['URL'],
                        "Puesto": i['Puesto'],
                        "Modalidad": i['Modalidad'],
                        "Sueldo": i['Sueldo'],
                        "Horario": i['Horario'],
                        "Fecha_Publicacion": i['Fecha_Publicacion'],
                        "Fecha_Expiracion": i['Fecha_Expiracion'],
                        "Sexo": i['Sexo'],
                        "Ubicacion": i['Ubicacion'],
                        "Nombre_Empresa": i['Nombre_Empresa'],
                        "Numero_Telefono": i['Numero_Telefono'],
                        "Email": i['Email'],
                        "Direccion": i['Direccion'],
                        "Descripcion": i['Descripcion'],
                        "Beneficios": i['Beneficios'],
                        "Palabras_clave": i['Palabras_clave']
                    }
                )

            cliente.upsert(
                collection_name="vacantes_prueba",
                points=[metadata]
            )
            
            if cliente:
                print("Vacante insertada perfectamente", e)
    print("Hecho!")
except AttributeError as e:
    print("Error encontrado: ", e)