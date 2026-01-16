from curl_cffi import requests
from bs4 import BeautifulSoup
import time


def Obtener_url_vacantes(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        urls = []
        req = requests.get(url=url, headers=headers, impersonate='chrome')
        req.encoding = 'utf-8'
        if req.status_code == 200:
            sopa = BeautifulSoup(req.text, "html.parser", from_encoding="utf-8")
            data = sopa.find_all("a", class_="text-decoration-none text-dark")
            print(data)
            for i in data:
                print(i)
                href = i.get('href')
                urls.append(href)
                
            with open('./url.txt', 'w', encoding='utf-8') as e:
                e.write('\n'.join(urls))
                
            return 'Urls Obtenidas'
        else:
            return 'error'
    except ValueError as e:
        return e

# Obtener las urls de la pagina y devolver los datos para volver hacer scrap a las urls
def Obtener_url(pagina) -> str:
    for i in range(1, pagina):
        time.time(30)
        url = f'https://do.trabajosdiarios.com/ofertas-trabajo?page={i}'
        datos = Obtener_url_vacantes(url)
        print(datos)

Obtener_url(10)
