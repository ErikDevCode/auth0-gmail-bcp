# app/utils.py
import re
from bs4 import BeautifulSoup

CATEGORIAS_MAP = {
    "DIDI": "Transporte",
    "UBER": "Transporte",
    "ARUMA": "Supermercado",
    "PLAZA VEA": "Supermercado",
    "TOTTUS": "Supermercado",
    "NIKE": "Ropa",
    "FALABELLA": "Ropa / Electro",
    "RAPPI": "Comida / Delivery",
    "KFC": "Comida / Delivery",
    "UNACEM": "Comida / Trabajo",
    "TAMBO": "Antojos",
    "MOVISTAR": "Internet / Celular",
    "CLARO": "Internet / Celular",
    "ENTEL": "Internet / Celular",
    "AMAZON": "Compras Internet",
    "aliexpress": "Compras Internet",
    "APUESTA": "Apuestas",
    "BETANO": "Apuestas",
    "YAPE": "Yape",
    "PLIN": "Plin",
    "APPLE": "Apple",
    "CASA ANDINA": "Hospedaje",
    "CAS CHINCHA": "Hospedaje",
    "CASASAFRAN": "Hospedaje",
    "CINEMARK": "Cine",
    "CINEPLANET": "Cine",
    "CINEPOLIS": "Cine",
    "D'JULIA": "Antojos",
    "Google": "Suscripciones",
    "HYM": "Ropa",
    "DONA CHURRITA": "Antojos",
    "MARIA ALMENARA": "Antojos",
    "MARATHON": "Ropa",
    "MC DONALDS": "Comida / Delivery",
    "NETFLIX": "Entretenimiento",
    "NO HAY SIN SUERTE": "Suscripciones",
    "NOTION": "Suscripciones",
    "OPTICAS GMO": "Lentes",
    "REEBOK": "Ropa",
    "RIPLEY": "Ropa",
    "VILLA CHICKEN": "Comida / Delivery",
    "ZARA": "Ropa"
}

MESES_ESP_ING = {
    'enero': 'January', 'febrero': 'February', 'marzo': 'March',
    'abril': 'April', 'mayo': 'May', 'junio': 'June',
    'julio': 'July', 'agosto': 'August', 'septiembre': 'September',
    'octubre': 'October', 'noviembre': 'November', 'diciembre': 'December'
}

def obtener_categoria(empresa, tipo):
    if not empresa:
        return "Otros"
    empresa = empresa.upper()
    for clave, categoria in CATEGORIAS_MAP.items():
        if clave in empresa:
            return categoria
    if tipo.upper() == "YAPE":
        return "Yape"
    elif tipo.upper() == "TARJETA DEBITO":
        if "PLIN" in empresa:
            return "Plin"
        elif "YAPE" in empresa:
            return "Yape"
    return "Otros"

def normalizar_fecha(fecha_str: str) -> str:
    for esp, ing in MESES_ESP_ING.items():
        if esp in fecha_str.lower():
            fecha_str = fecha_str.lower().replace(esp, ing)
            break
    fecha_str = fecha_str.replace("a. m.", "AM").replace("p. m.", "PM")
    return fecha_str

def parse_email_body(html, subject):
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text()
    subjectYape = "Por tu seguridad, te notificaremos por cada yapeo que realices"
    subjectCredito = "Realizaste un consumo con tu Tarjeta de Crédito BCP"

    if subjectYape in subject:
        monto_match = re.search(r'S/ ?([\d.]+)', text)
        empresa_match = re.search(r'Nombre del Beneficiario\s+([^\n\r<]+?)(?:\s*N[\u00ba\u00b0] de operaci\u00f3n|$)', text)
        fecha_match = re.search(r'Fecha y Hora de la operaci\u00f3n\s+(\d{1,2} [a-zA-Z]+ \d{4} - \d{1,2}:\d{2} [ap]\. m\.)', text, re.IGNORECASE)
        operacion_match = re.search(r'N[\u00ba\u00b0] de operaci\u00f3n\s*[\n\r]*\s*(\d+)', text)
        if fecha_match:
            fecha_raw = fecha_match.group(1).strip()
            partes = re.match(r'(\d{1,2}) (\w+) (\d{4}) - (.+)', fecha_raw)
            fecha_formateada = f"{partes.group(1)} de {partes.group(2)} de {partes.group(3)} - {partes.group(4)}" if partes else fecha_raw
        else:
            fecha_formateada = None

        return {
            "Fecha y hora": fecha_formateada,
            "Empresa": f"{empresa_match.group(1).strip()} - YAPE" if empresa_match else "YAPE",
            "Total consumo (S/)": float(monto_match.group(1)) if monto_match else None,
            "Número de operación": operacion_match.group(1) if operacion_match else None,
            "Tipo": "Yape a otro Yape"
        }

    elif subjectCredito in subject:
        tipo_cambio_usd_pen = 3.729
        monto_usd_match = re.search(r'\$ ?([\d.,]+)', text)
        monto_pen = round(float(monto_usd_match.group(1).replace(',', '')) * tipo_cambio_usd_pen, 2) if monto_usd_match else None
        if not monto_pen:
            monto_match = re.search(r'Total del consumo\s+S/ ?([\d.]+)', text)
            monto_pen = float(monto_match.group(1).replace(',', '')) if monto_match else None
        empresa_match = re.search(r'Empresa\s+([^\n\r]+)', text)
        fecha_match = re.search(r'Fecha y hora\s+(\d{1,2} de \w+ de \d{4} - \d{2}:\d{2} [APM]+)', text)
        operacion_match = re.search(r'Número de operación\s+(\d+)', text)

        return {
            "Fecha y hora": fecha_match.group(1).strip() if fecha_match else None,
            "Empresa": empresa_match.group(1).strip() if empresa_match else "TARJETA CREDITO BCP",
            "Total consumo (S/)": monto_pen,
            "Número de operación": operacion_match.group(1) if operacion_match else None,
            "Tipo": "Tarjeta Crédito"
        }

    else:
        bold_tags = soup.find_all('b')
        bold_texts = [b.get_text(strip=True) for b in bold_tags]
        monto = next((t for t in bold_texts if t.startswith("S/")), None)
        empresa_match = re.search(r'Tarjeta de Débito BCP en (.+?)\.', text)
        fecha = re.search(r'Fecha y hora\s+(\d{2} de \w+ de \d{4} - \d{2}:\d{2} [APM]+)', text)
        operacion = re.search(r'Número de operación\s+(\d+)', text)

        return {
            "Fecha y hora": fecha.group(1) if fecha else None,
            "Empresa": empresa_match.group(1).strip() if empresa_match else None,
            "Total consumo (S/)": float(monto.replace("S/", "").replace(",", "").strip()) if monto else None,
            "Número de operación": operacion.group(1) if operacion else None,
            "Tipo": "Yape a otro Operador"
        }
