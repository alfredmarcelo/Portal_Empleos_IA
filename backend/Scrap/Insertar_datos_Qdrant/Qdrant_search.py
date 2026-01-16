from ollama import embed
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

cliente = QdrantClient(host='localhost', port=6333)

def FieldCondition_Dinamico(payloads):

    Tipos = [
        "Puesto",
        "Modalidad",
        "Horario",
        "Ubicacion",
        "Descripcion",
        "Beneficios",
        'Palabras_clave'
    ]

    Guardar_Fieldconditions = []

    for p in payloads:
        if 'sueldo_max' in p and payloads['sueldo_max'] > 0:
            Guardar_Fieldconditions.append(
                FieldCondition(
                    key='sueldo',
                    range=Range(lte=int(payloads['sueldo_max']))
                    )
                )
            
        if 'sueldo_min' in p and payloads['sueldo_min'] > 0:
            print(p)
            Guardar_Fieldconditions.append(
                FieldCondition(
                    key='sueldo',
                    range=Range(gte=int(payloads['sueldo_min']))
                    )
                )
            
        if 'sueldo' in p and payloads['sueldo'] > 0:
            Guardar_Fieldconditions.append(
                FieldCondition(
                    key=p,
                    range=Range(gte=int(payloads['sueldo']))
                    )
                )
                
            # elif p == 'sueldo_max' or p == 'sueldo_min':
            #     print('sueldos', sueldos)
            #     Guardar_Fieldconditions.append(
            #         FieldCondition(
            #             key=p,
            #             range=Range(sueldos)
            #             )
            #         )
        for i in Tipos:
            if p in i:
                print(payloads[i])
                Guardar_Fieldconditions.append(
                    FieldCondition(
                        key=i,
                        match=MatchValue(value=payloads[f"{i}"])
                        )
                    )
                
    print(Guardar_Fieldconditions)
    return Guardar_Fieldconditions

def calcular_threshold(texto):

    palabras = len(texto.split())
    threshold = 0.57

    if palabras <= 4:
        threshold = threshold + 0.04
        print(threshold)
        return threshold
    
    if palabras >= 5 and palabras <=9:
        threshold = threshold + 0.06
        print(threshold)
        return threshold
    
    if palabras >= 10:
        threshold = threshold + 0.13
        print(threshold)
        return threshold
    
    return threshold

# El input de los datos trae los payloads, estos se tienen que agregar de forma dinamica en el query_filter
# Normalizar el texto del payload para aceptar varios parametros. Hacer en n8n o aqui
def buscar(datos):
    # normalizar = datos.payloads.get('palabras_clave').split(',')
    # payloads_new = {"palabras_clave": normalizar}
    # print(payloads_new)
    print('datos', datos)
    try: 
        search = embed(model="qwen3-embedding:8b", input=datos.texto)
        payload = FieldCondition_Dinamico(datos.payloads)
        threshold = calcular_threshold(datos.texto)

        result = cliente.query_points(
            collection_name="vacantes_prueba",
            query=search['embeddings'][0],
            query_filter= Filter(
                must=payload
            ),
            with_payload=True,
            # score_threshold=round(threshold, 2),
            score_threshold=0.30,
            limit=100
        )

        print(result)
        return result
    except ValueError as e:
        print(e)


# "puesto": i['puesto'],
# "modalidad": i['modalidad'],
# "sueldo": i['sueldo'],
# "horario": i['horario'],
# "ubicacion": i['ubicacion'],
# "descripcion": i['descripcion'],
# "beneficios": i['beneficios']