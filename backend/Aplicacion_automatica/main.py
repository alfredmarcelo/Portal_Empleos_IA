#!/usr/bin/env python3
"""
Agente Autónomo de Postulación a Vacantes con Playwright y Ollama Local
======================================================================
Este script utiliza un modelo local de Ollama (ej: 'maternion/ling-3.0-tiny:8b')
y Playwright con Chromium para:
1. Acceder a la vacante de empleo indicada (por defecto en TrabajosDiarios).
2. Extraer los datos clave (puesto, empresa, ubicación, requisitos y descripción).
3. Analizar la vacante con la IA local de Ollama.
4. Localizar y accionar el botón de postulación ("Postularme al trabajo").
5. Analizar el formulario o portal de postulación resultante.
6. Si se proporcionan credenciales (--email y --password), intentar completar el inicio
   de sesión para formalizar la postulación.
7. Guardar capturas de pantalla de cada etapa en 'screenshots/'.
8. Proporcionar un dictamen final elaborado por la IA.
"""

import sys
import os
import re
import json
import time
import argparse
from typing import Dict, Any, Optional
import requests
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext

# URL por defecto solicitada
DEFAULT_VACANCY_URL = "https://do.trabajosdiarios.com/trabajo/3080286/vendedora-pre-venta-en-santo-domingo"

# Colores y estilo de terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'

def log_info(msg: str):
    print(f"{Colors.CYAN}ℹ [INFO]{Colors.RESET} {msg}")

def log_ai(msg: str):
    print(f"{Colors.HEADER}🤖 [OLLAMA AI]{Colors.RESET} {msg}")

def log_browser(msg: str):
    print(f"{Colors.BLUE}🌐 [PLAYWRIGHT]{Colors.RESET} {msg}")

def log_success(msg: str):
    print(f"{Colors.GREEN}✔ [ÉXITO]{Colors.RESET} {msg}")

def log_warning(msg: str):
    print(f"{Colors.YELLOW}⚠ [ALERTA]{Colors.RESET} {msg}")

def log_error(msg: str):
    print(f"{Colors.RED}✖ [ERROR]{Colors.RESET} {msg}")


class OllamaAgent:
    """Cliente para interactuar con la IA de Ollama local."""
    
    def __init__(self, host: str = "http://localhost:11434", preferred_model: Optional[str] = None):
        self.host = host.rstrip('/')
        self.model = self._select_model(preferred_model)

    def _select_model(self, preferred: Optional[str] = None) -> str:
        """Detecta modelos instalados en Ollama y selecciona el más apto."""
        try:
            res = requests.get(f"{self.host}/api/tags", timeout=5)
            res.raise_for_status()
            data = res.json()
            models = [m['name'] for m in data.get('models', [])]
            
            if not models:
                raise RuntimeError("No se encontraron modelos instalados en Ollama. Ejecuta: ollama pull <modelo>")

            if preferred:
                for m in models:
                    if preferred in m:
                        log_info(f"Usando modelo especificado: {Colors.BOLD}{m}{Colors.RESET}")
                        return m

            for m in models:
                if "embed" not in m.lower():
                    log_info(f"Modelo detectado automáticamente: {Colors.BOLD}{m}{Colors.RESET}")
                    return m
            
            return models[0]
        except requests.exceptions.ConnectionError:
            log_error(f"No se pudo conectar a Ollama en {self.host}. ¿Está iniciado el servicio?")
            sys.exit(1)
        except Exception as e:
            log_error(f"Error al consultar Ollama: {e}")
            sys.exit(1)

    def query(self, prompt: str) -> str:
        """Envía un prompt a Ollama y retorna la respuesta limpia sin etiquetas think."""
        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        try:
            res = requests.post(url, json=payload, timeout=60)
            res.raise_for_status()
            raw = res.json().get("response", "")
            
            # Limpiar etiquetas de pensamiento de modelos tipo DeepSeek/Ling
            if "</think>" in raw:
                cleaned = raw.split("</think>")[-1].strip()
            else:
                cleaned = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
            return cleaned
        except Exception as e:
            log_error(f"Error al consultar a Ollama: {e}")
            raise

    def analyze_vacancy(self, vacancy_data: Dict[str, str]) -> str:
        """La IA analiza los requisitos, perfil y recomendación para la vacante."""
        prompt = (
            "Eres un reclutador y asistente experto de Recursos Humanos e Inteligencia Artificial.\n"
            "Analiza detalladamente la siguiente vacante de empleo a la que se desea postular:\n\n"
            f"- **Puesto:** {vacancy_data.get('title', 'No especificado')}\n"
            f"- **Empresa:** {vacancy_data.get('company', 'No especificada')}\n"
            f"- **Ubicación:** {vacancy_data.get('location', 'No especificada')}\n"
            f"- **Detalles/Descripción:**\n'''\n{vacancy_data.get('description', '')[:2000]}\n'''\n\n"
            "Proporciona en español un análisis estructurado con los siguientes 3 puntos:\n"
            "1. **Resumen del puesto y funciones esperadas**.\n"
            "2. **Requisitos indispensables y competencias clave**.\n"
            "3. **Evaluación de viabilidad y recomendación para la postulación**."
        )
        return self.query(prompt)

    def analyze_application_status(self, current_url: str, page_title: str, form_details: str) -> str:
        """La IA evalúa el estado de la página de postulación."""
        prompt = (
            "Eres un agente inteligente encargado de postular candidatos a ofertas de empleo.\n"
            f"Acabamos de hacer clic en 'Postularme al trabajo'. Nos encontramos en:\n"
            f"- URL: {current_url}\n"
            f"- Título de página: {page_title}\n"
            f"- Elementos del formulario detectados: {form_details}\n\n"
            "Explica en español en 2 o 3 oraciones concisas el estado actual de la postulación, "
            "qué solicita el portal para continuar y qué debe hacer el candidato."
        )
        return self.query(prompt)


class VacancyApplicationBot:
    """Controlador Playwright para la automatización de la vacante."""

    def __init__(self, headless: bool = False, delay_ms: int = 1500):
        self.headless = headless
        self.delay_ms = delay_ms
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.screenshots_dir = os.path.join(os.path.dirname(__file__), "screenshots")
        os.makedirs(self.screenshots_dir, exist_ok=True)

    def start(self):
        """Inicia Chromium en modo visual o headless."""
        log_browser(f"Iniciando Chromium (headless={self.headless})...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--start-maximized"
            ]
        )
        self.context = self.browser.new_context(
            locale="es-DO",
            viewport={"width": 1280, "height": 850},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        )
        self.page = self.context.new_page()
        self.page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")

        # Bloquear anuncios de Google para evitar popups molestos (#google_vignette) que bloqueen clics
        self.page.route("**/*googlesyndication.com/**", lambda route: route.abort())
        self.page.route("**/*googleads.g.doubleclick.net/**", lambda route: route.abort())
        self.page.route("**/*adservice.google.com/**", lambda route: route.abort())
        self.page.route("**/pagead/**", lambda route: route.abort())

        log_success("Chromium inicializado correctamente (con bloqueo de anuncios activos).")

    def close(self):
        """Cierra el navegador."""
        if self.browser:
            log_browser("Cerrando navegador...")
            try:
                self.browser.close()
            except Exception:
                pass
        if self.playwright:
            try:
                self.playwright.stop()
            except Exception:
                pass
        log_info("Sesión de Playwright finalizada.")

    def take_screenshot(self, filename: str) -> str:
        """Toma una captura de pantalla y retorna la ruta."""
        path = os.path.join(self.screenshots_dir, filename)
        try:
            self.page.screenshot(path=path, full_page=False, timeout=5000)
            log_info(f"Captura guardada: {Colors.DIM}{path}{Colors.RESET}")
            return path
        except Exception as e:
            log_warning(f"No se pudo tomar la captura {filename}: {e}")
            return ""

    def load_vacancy(self, url: str) -> Dict[str, str]:
        """Carga la página de la vacante y extrae información básica."""
        log_browser(f"Cargando vacante: {Colors.CYAN}{url}{Colors.RESET}")
        self.page.goto(url, timeout=35000, wait_until="domcontentloaded")
        self.page.wait_for_timeout(self.delay_ms)

        # Extraer título del puesto
        title = "Puesto de empleo"
        for sel in ["h1", "h2.font_2", "h3.font_2", "div.card-body h1"]:
            el = self.page.locator(sel).first
            if el.count() > 0 and el.is_visible():
                title = el.inner_text().strip()
                break

        # Extraer empresa y ubicación
        body_text = self.page.inner_text("body")
        lines = [line.strip() for line in body_text.split("\n") if line.strip()]

        company = "Empresa confidencial / No especificada"
        company_loc = self.page.locator('a[href*="/empresa/"], p.text-secondary').first
        if company_loc.count() > 0 and company_loc.is_visible():
            company = company_loc.inner_text().strip()

        location = "Santo Domingo, República Dominicana"
        for l in lines:
            if "Santo Domingo" in l or "Distrito Nacional" in l or "Santiago" in l:
                location = l
                break

        log_success(f"Vacante cargada: '{Colors.BOLD}{title}{Colors.RESET}'")
        log_info(f"Empresa: {company} | Ubicación: {location}")

        self.take_screenshot("1_vacante_detalle.png")

        return {
            "url": url,
            "title": title,
            "company": company,
            "location": location,
            "description": body_text[:3000]
        }

    def click_apply_button(self) -> bool:
        """Encuentra y hace clic en el botón de postulación visible."""
        log_browser("Buscando botón de postulación...")

        # Selectores posibles para el botón de postulación
        selectors = [
            'a[href*="/trabajo/postular/"]:visible',
            'a:has-text("Postularme al trabajo"):visible',
            'a:has-text("Postularme"):visible',
            'button:has-text("Postularme"):visible',
            'button:has-text("Aplicar"):visible'
        ]

        target_btn = None
        for sel in selectors:
            btn = self.page.locator(sel).first
            if btn.count() > 0 and btn.is_visible():
                target_btn = btn
                break

        if not target_btn:
            log_error("No se encontró un botón de postulación visible en la página.")
            return False

        btn_text = target_btn.inner_text().strip()
        log_browser(f"Botón encontrado: '{Colors.BOLD}{btn_text}{Colors.RESET}'. Resaltando y haciendo scroll...")

        # Resaltar visualmente el botón con borde rojo para feedback en pantalla
        try:
            target_btn.evaluate("el => el.style.border = '4px solid #ff0055'")
            target_btn.evaluate("el => el.style.boxShadow = '0 0 15px #ff0055'")
            self.page.wait_for_timeout(600)
        except Exception:
            pass

        target_btn.scroll_into_view_if_needed()
        self.page.wait_for_timeout(800)

        btn_href = target_btn.get_attribute("href") or ""
        log_browser("Haciendo clic en 'Postularme al trabajo'...")
        target_btn.click()

        # Esperar la navegación a la página de postulación
        self.page.wait_for_load_state("domcontentloaded")
        self.page.wait_for_timeout(self.delay_ms)

        # Si el clic no redirigió por un overlay/hash, asegurar la navegación al portal de postulación
        if "candidatos/postular" not in self.page.url and btn_href:
            postular_url = btn_href if btn_href.startswith("http") else f"https://do.trabajosdiarios.com{btn_href}"
            log_browser(f"Redirigiendo al formulario de postulación: {postular_url}...")
            self.page.goto(postular_url, wait_until="domcontentloaded")
            self.page.wait_for_timeout(self.delay_ms)

        log_success(f"Navegación tras clic completada: {self.page.url}")
        self.take_screenshot("2_postulacion_formulario.png")
        return True

    def inspect_application_form(self) -> Dict[str, Any]:
        """Inspecciona los elementos del formulario de postulación."""
        current_url = self.page.url
        title = self.page.title()

        has_login_form = self.page.locator("#CLoginForm, form[action*='candidato']").count() > 0
        has_email_input = self.page.locator("input[type='email'], input#email").is_visible()
        has_password_input = self.page.locator("input[type='password'], input#password").is_visible()
        has_register_link = self.page.locator("a[href*='registro']").count() > 0

        headings = [h.inner_text().strip() for h in self.page.locator("h1, h2, h3").all() if h.is_visible()]

        return {
            "current_url": current_url,
            "title": title,
            "headings": headings,
            "has_login_form": has_login_form,
            "has_email_input": has_email_input,
            "has_password_input": has_password_input,
            "has_register_link": has_register_link
        }

    def attempt_login_postulation(self, email: str, password: str) -> bool:
        """Si el usuario proporciona credenciales, intenta completar el login de postulación."""
        log_browser(f"Intentando postular con cuenta de candidato ({email})...")

        email_input = self.page.locator("input#email, input[type='email']").first
        pass_input = self.page.locator("input#password, input[type='password']").first

        if email_input.count() == 0 or pass_input.count() == 0:
            log_warning("No se encontraron los campos de credenciales.")
            return False

        email_input.click()
        email_input.fill(email)
        self.page.wait_for_timeout(500)

        pass_input.click()
        pass_input.fill(password)
        self.page.wait_for_timeout(500)

        submit_btn = self.page.locator("button[type='submit']:has-text('Iniciar sesión'), button[type='submit']").first
        if submit_btn.count() > 0:
            log_browser("Enviando credenciales para formalizar la postulación...")
            submit_btn.click()
            self.page.wait_for_load_state("domcontentloaded")
            self.page.wait_for_timeout(3000)
            self.take_screenshot("3_postulacion_resultado.png")
            log_success(f"Formulario enviado. URL actual: {self.page.url}")
            return True

        return False


def main():
    parser = argparse.ArgumentParser(description="Agente Autónomo de Postulación a Vacantes")
    parser.add_argument("-u", "--url", type=str, default=DEFAULT_VACANCY_URL, help="URL de la vacante de empleo")
    parser.add_argument("-e", "--email", type=str, default=None, help="Correo de la cuenta de candidato (opcional)")
    parser.add_argument("-p", "--password", type=str, default=None, help="Contraseña de la cuenta de candidato (opcional)")
    parser.add_argument("-m", "--model", type=str, default=None, help="Modelo de Ollama a utilizar")
    parser.add_argument("--headless", action="store_true", help="Ejecutar sin interfaz gráfica")
    parser.add_argument("--keep-open", type=int, default=8, help="Segundos que permanece abierto el navegador al terminar (default: 8)")
    args = parser.parse_args()

    print(f"\n{Colors.BOLD}{Colors.HEADER}==================================================================={Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.HEADER}   🎯 AGENTE DE POSTULACIÓN A VACANTES - PLAYWRIGHT + OLLAMA      {Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.HEADER}==================================================================={Colors.RESET}\n")

    # 1. Conexión con Ollama
    log_info("Conectando con la IA de Ollama local...")
    ai = OllamaAgent(preferred_model=args.model)

    # 2. Iniciar navegador
    bot = VacancyApplicationBot(headless=args.headless)
    bot.start()

    try:
        # 3. Cargar la vacante
        vacancy_info = bot.load_vacancy(args.url)

        # 4. Ollama analiza la oferta de empleo
        log_info("Ollama está analizando los requisitos y el perfil de la vacante...")
        analysis = ai.analyze_vacancy(vacancy_info)

        print(f"\n{Colors.BOLD}{Colors.CYAN}================ ANÁLISIS DE LA VACANTE (OLLAMA) ================={Colors.RESET}")
        print(analysis)
        print(f"{Colors.BOLD}{Colors.CYAN}==================================================================={Colors.RESET}\n")

        # 5. Ejecutar la acción de postularse
        clicked = bot.click_apply_button()
        if not clicked:
            log_error("No se pudo iniciar el proceso de postulación.")
            return

        # 6. Inspeccionar el formulario de postulación
        log_info("Inspeccionando el portal de postulación resultante...")
        form_info = bot.inspect_application_form()

        print(f"\n{Colors.BOLD}--- Estado de la Postulación ---{Colors.RESET}")
        print(f"URL de destino: {Colors.CYAN}{form_info['current_url']}{Colors.RESET}")
        print(f"Título: {form_info['title']}")
        print(f"Encabezados detectados: {form_info['headings']}")
        print(f"¿Requiere inicio de sesión/registro?: {'Sí' if form_info['has_login_form'] else 'No'}")
        print("--------------------------------\n")

        # 7. Si hay credenciales, enviarlas; si no, documentar el estado
        if args.email and args.password:
            bot.attempt_login_postulation(args.email, args.password)
        else:
            log_warning("TrabajosDiarios requiere autenticación de candidato ('Ingresa como Candidato').")
            log_info("No se proporcionaron credenciales (--email / --password), por lo que la sesión queda lista en la pantalla de postulación.")
            log_info(f"Se ha guardado la captura en: {Colors.BOLD}Aplicacion_automatica/screenshots/2_postulacion_formulario.png{Colors.RESET}")

        # 8. Ollama emite su reporte del estado de la postulación
        log_info("Ollama está evaluando el estado del proceso de postulación...")
        form_summary = (
            f"Formulario de login presente: {form_info['has_login_form']}. "
            f"Campos: email={form_info['has_email_input']}, password={form_info['has_password_input']}. "
            f"Opciones de acceso social: Google, Facebook. Enlace de registro disponible."
        )
        status_report = ai.analyze_application_status(
            current_url=form_info["current_url"],
            page_title=form_info["title"],
            form_details=form_summary
        )

        print(f"\n{Colors.BOLD}{Colors.GREEN}================ ESTADO FINAL DE LA POSTULACIÓN =================={Colors.RESET}")
        print(status_report)
        print(f"{Colors.BOLD}{Colors.GREEN}==================================================================={Colors.RESET}\n")

        if args.keep_open > 0:
            log_info(f"Manteniendo Chromium visible por {args.keep_open} segundos para que puedas interactuar o verificar...")
            time.sleep(args.keep_open)

    except Exception as e:
        log_error(f"Ocurrió un error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        bot.close()
        log_success("Proceso de postulación finalizado.")


if __name__ == "__main__":
    main()
