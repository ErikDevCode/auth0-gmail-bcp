# app/gmail_service.py
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import os, sys
from datetime import datetime
from email.utils import parsedate_to_datetime
import base64
from utils.utils import parse_email_body, obtener_categoria, normalizar_fecha

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def get_gmail_service():
    creds = None
    base_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__))
    creds_path = os.path.join(base_dir, "credentials.json")

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)

    return build('gmail', 'v1', credentials=creds)

def extraer_consumos_desde_gmail():
    service = get_gmail_service()
    registros = []
    next_page_token = None

    while True:
        response = service.users().messages().list(userId='me', q='label:BCP', pageToken=next_page_token).execute()
        messages = response.get('messages', [])

        for msg_meta in messages:
            msg = service.users().messages().get(userId='me', id=msg_meta['id'], format='full').execute()
            payload = msg['payload']
            headers = payload.get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            date_header = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            fecha_envio = parsedate_to_datetime(date_header) if date_header else None

            def procesar(data):
                decoded = base64.urlsafe_b64decode(data).decode('utf-8')
                info = parse_email_body(decoded, subject)

                if not info["Fecha y hora"] and fecha_envio:
                    info["Fecha y hora"] = fecha_envio.strftime('%d de %B de %Y - %I:%M %p')

                if info["Fecha y hora"] and info["Total consumo (S/)"] and info["Empresa"]:
                    try:
                        fecha_normalizada = normalizar_fecha(info["Fecha y hora"])
                        fecha_obj = datetime.strptime(fecha_normalizada, "%d de %B de %Y - %I:%M %p")
                        info["Periodo"] = fecha_obj.strftime("%m%Y")
                    except Exception:
                        return

                    registros.append({
                        "fecha": fecha_obj,
                        "empresa": info["Empresa"],
                        "monto": info["Total consumo (S/)"],
                        "numero_operacion": info["Número de operación"],
                        "tipo": info["Tipo"],
                        "categoria": obtener_categoria(info["Empresa"], info["Tipo"]),
                        "periodo": info["Periodo"]
                    })

            if 'parts' in payload:
                for part in payload['parts']:
                    data = part.get('body', {}).get('data')
                    if data:
                        procesar(data)
            else:
                data = payload.get('body', {}).get('data')
                if data:
                    procesar(data)

        next_page_token = response.get('nextPageToken')
        if not next_page_token:
            break

    return registros
