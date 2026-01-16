from curl_cffi import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from playwright.sync_api import sync_playwright
from IA import normalizar_texto
import json
import datetime

def obtener_ofertas_empleo(url):

    oferta = {
        "URL": url,
        "Puesto": "",
        "Descripcion": "",
        "Fecha_Publicacion": "",
        "Fecha_Expiracion": "",
        "Ubicacion": "",
        "tiempo_procesamiento": 0
    }
    tiempo_inicio = time.time()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    try:
        req = requests.get(url, headers=headers, impersonate="chrome")
        req.encoding = 'utf-8'
        if req.status_code == 200:
            sopa = BeautifulSoup(req.text, "html.parser", from_encoding="utf-8")
            oferta["Titulo"] = sopa.find("section", id="title").get_text(strip=True) if sopa.find("section", id="title") else ""
            oferta["Descripcion"] = sopa.find("div", class_="job_description").get_text(strip=True) if sopa.find("div", class_="job_description") else ""
            oferta["Fecha_Publicacion"] = sopa.find("li", class_="posted-date").get_text(strip=True) if sopa.find("li", class_="posted-date") else ""                    
            oferta["Fecha_Expiracion"] = sopa.find("li", class_="expiration-date").get_text(strip=True) if sopa.find("li", class_="expiration-date") else ""
            oferta["Ubicacion"] = sopa.find("li", class_="location").get_text(strip=True) if sopa.find("li", class_="location") else ""
            tiempo_fin = time.time()
            oferta["tiempo_procesamiento"] = tiempo_fin - tiempo_inicio
            if Contar_meses(oferta["Fecha_Publicacion"]):
                return "Limite de ofertas alcanzado"
            
            return oferta
        else:
            print(f"Error al acceder a la página: {req.status_code}")
    except Exception as e:
        print(f"Error en la solicitud HTTP: {e}")
        return oferta
    
def ObtenerURL(Provincia):
    urls = []
    pagina_inicial = f"https://tuempleord.do/busca-tu-trabajo/?search_keywords=%23&search_location={Provincia}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    try:
        req = requests.get(pagina_inicial, headers=headers, impersonate="chrome")
        html = simular_click_selenium(pagina_inicial)
        if req.status_code == 200:
            sopa = BeautifulSoup(html, "html.parser")
            ofertas = sopa.find_all("li", class_="job_listing")
            for oferta in ofertas:
                url_oferta = oferta.find("a").get("href")
                if url_oferta:
                    datos = obtener_ofertas_empleo(url_oferta)
                    if datos == "Limite de ofertas alcanzado":
                        return urls
                    urls.append(datos)
            return urls
        else:
            print(f"Error al acceder a la página inicial: {req.status_code}")
            return urls
    except Exception as e:
        print(f"Error en la solicitud HTTP: {e}")
        return urls
    
def simular_click_selenium(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url)
        
        page.wait_for_selector("a.load_more_jobs")
        page.locator("a.load_more_jobs").click()

        page.wait_for_timeout(2000)
        html = page.content()
        browser.close()

        return html


def provincias_disponibles():
    # provincias_disponibles = [
    #     "Azua", "Bani", "Barahona", "bayaguana", "bayahibe", "Boca+Chica",
    #     "Bonao", "Contanza", "Cotui", "Dajabon", "El+Seibo", "Hato+Mayor",
    #     "Duverge", "el+seibo", "Elias+PiÃ±a", "Espaillat", "haina", "Hato+Mayor",
    #     "Jarabacoa", "Juan+Dolio", "La+Altagracia", "La+Romana", "La+Vega",
    #     "Las+Matas+de+Farfan", "Las+Terrenas", "macao", "Mao", "miches",
    #     "Moca", "Monte+Cristi", "Monte+Plata", "Nagua", "navarrete", "neiba",
    #     "Neyba", "ocoa", "pedernales", "Puerto+Plata", "Punta+Cana",
    #     "sabana+de+la+mar", "San+Cristobal", "San+Francisco+de+Macoris",
    #     "San+Juan", "San+Pedro+de+Macoris", "Sanchez", "Santiago",
    #     "Santo+Domingo", "tamboril", "Tenares", "veron", "villa+altagracia",
    #     "villa+Tapia", "Yamasa"
    # ]

    provincia_prueba = [
         "Azua"
        ]
    
    tiempo_actual = datetime.datetime.now()
    
    resultado_ofertas = []
    resultado_normalizado = []
    marcador_nomalizado = 0

    provincia = ''

    for i in provincia_prueba:
        print(f"Obteniendo ofertas para la provincia: {i}")
        ofertas = ObtenerURL(i)
        resultado_ofertas.extend(ofertas)
        provincia.replace('', str(i))

    for oferta in resultado_ofertas:
        marcador_nomalizado += 1
        print("Normalizando oferta:", marcador_nomalizado)
        res_normalizado = normalizar_texto(oferta)
        resultado_normalizado.append(res_normalizado)

    if resultado_normalizado:
        for i in resultado_normalizado:
            datos_completos = {
                    "metadata": {
                        "fecha_extraccion": datetime.datetime.now().isoformat(),
                        "fecha_legible": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                        "provincia": provincia,
                        "total_ofertas": len(resultado_normalizado),
                        "version_scraper": "1.0"
                    },
                    "oferta": resultado_normalizado 
                }
            
    with open(f"ofertas_tuempleord_{tiempo_actual.date()}.json", "w", encoding="utf-8") as f:
        json.dump(datos_completos, f, ensure_ascii=False, indent=2)   


def Contar_meses(fecha_texto):

    MESES = {
        "enero": "January", "febrero": "February", "marzo": "March",
        "abril": "April", "mayo": "May", "junio": "June",
        "julio": "July", "agosto": "August", "septiembre": "September",
        "setiembre": "September", "octubre": "October",
        "noviembre": "November", "diciembre": "December"
    }

    tiempo_hoy = datetime.datetime.now()

    texto = fecha_texto
    texto = texto[21:]
    print(texto)

    eliminar_texto = ["Publicado en"]

    for eliminar in eliminar_texto:
        texto = texto.replace(eliminar, "").strip()

    for es, en in MESES.items():
        if es in texto:
            texto = texto.replace(es, en)
            time = datetime.datetime.strptime(texto, "%B %d, %Y")
            conteo_meses = tiempo_hoy.month - time.month
            if conteo_meses >= 3:
                print(True)
                return True

print(provincias_disponibles())