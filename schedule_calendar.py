import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
import json
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

async def schedule_event(summary: str, start: dict, end: dict, calendar_id: str) -> dict:
    try:
        google_credentials = os.getenv("GOOGLE_CREDENTIALS")
        if not google_credentials:
            raise ValueError("GOOGLE_CREDENTIALS não está configurado no .env")

        credentials_dict = json.loads(google_credentials)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=["https://www.googleapis.com/auth/calendar"]
        )
        service = build("calendar", "v3", credentials=credentials)

        event = {
            "summary": summary,
            "start": start,
            "end": end
        }
        logger.info(f"Dados do evento a serem enviados para {calendar_id}: {json.dumps(event, indent=2)}")

        event_result = service.events().insert(calendarId=calendar_id, body=event).execute()
        logger.info(f"Evento criado com sucesso: {event_result.get('id')}")
        return {
            "message": "Evento agendado!",
            "eventId": event_result.get("id")
        }
    except HttpError as http_error:
        logger.error(f"Erro HTTP ao criar evento: {http_error}")
        return {"error": f"Erro na API do Google Calendar: {http_error}"}
    except Exception as e:
        logger.error(f"Erro ao agendar evento no Google Calendar: {e}")
        return {"error": str(e) or "Falha ao agendar evento"}

async def get_event(event_id: str, calendar_id: str) -> dict:
    try:
        google_credentials = os.getenv("GOOGLE_CREDENTIALS")
        if not google_credentials:
            raise ValueError("GOOGLE_CREDENTIALS não está configurado no .env")

        credentials_dict = json.loads(google_credentials)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=["https://www.googleapis.com/auth/calendar"]
        )
        service = build("calendar", "v3", credentials=credentials)

        event = service.events().get(calendarId=calendar_id, eventId=event_id).execute()
        logger.info(f"Evento encontrado: {event}")
        return {
            "message": "Evento encontrado!",
            "event": event
        }
    except Exception as e:
        logger.error(f"Erro ao buscar evento: {e}")
        return {"error": str(e)}