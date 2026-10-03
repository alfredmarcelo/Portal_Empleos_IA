# Agente Autónomo de Postulación a Vacantes con Playwright y Ollama Local

Este agente utiliza un modelo local de Ollama (por ejemplo, `maternion/ling-3.0-tiny:8b`) y Playwright con Chromium para navegar a una oferta de empleo, analizarla con IA, accionar el botón de postulación e interactuar con el portal de postulación.

---

## 🎯 Vacante Configurada por Defecto

- **URL:** `https://do.trabajosdiarios.com/trabajo/3080286/vendedora-pre-venta-en-santo-domingo`
- **Puesto:** Vendedor/a Pre-Venta
- **Empresa:** Jonathan Desechables
- **Ubicación:** Santo Domingo Este, República Dominicana

---

## 🚀 Flujo de Trabajo

1. **Carga y Extracción**: Playwright abre Chromium en modo visual y navega a la vacante.
2. **Análisis de la Vacante con Ollama**: La IA analiza el puesto, empresa, requisitos indispensables y viabilidad.
3. **Acción de Postulación**: Localiza el botón `"Postularme al trabajo"`, lo resalta visualmente en pantalla y hace clic en él.
4. **Inspección del Portal de Postulación**: Carga `https://do.trabajosdiarios.com/candidatos/postular/3080286` y detecta los requerimientos del formulario (cuenta de candidato / login).
5. **Postulación con Credenciales (Opcional)**: Si se proveen `--email` y `--password`, rellena los campos y envía el formulario de postulación.
6. **Capturas de Pantalla**: Guarda evidencias visuales en `Aplicacion_automatica/screenshots/`:
   - `1_vacante_detalle.png` (detalle de la oferta)
   - `2_postulacion_formulario.png` (pantalla de postulación / login)
   - `3_postulacion_resultado.png` (si se enviaron credenciales)
7. **Reporte Final de la IA**: Ollama emite una conclusión sobre el estado de la postulación.

---

## 💻 Ejemplos de Uso

### 1. Ejecutar en la vacante indicada (modo visual)
```bash
python Aplicacion_automatica/main.py
```

### 2. Proporcionar credenciales para postularse con tu cuenta
```bash
python Aplicacion_automatica/main.py --email "tu_correo@ejemplo.com" --password "tu_contraseña"
```

### 3. Probar con otra URL de vacante
```bash
python Aplicacion_automatica/main.py -u "https://do.trabajosdiarios.com/trabajo/otra-vacante"
```

### 4. Modo en segundo plano (headless)
```bash
python Aplicacion_automatica/main.py --headless
```

### 5. Mantener la ventana abierta más tiempo para interactuar
```bash
python Aplicacion_automatica/main.py --keep-open 15
```
