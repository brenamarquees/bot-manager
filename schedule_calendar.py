import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
import json
import logging
from datetime import datetime, timedelta

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

async def schedule_event(summary: str, start: dict, end: dict, calendar_id: str, attendees: list = None) -> dict:
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
        if attendees:
            event["attendees"] = [{"email": attendee} for attendee in attendees]

        logger.info(f"Dados do evento a serem enviados para {calendar_id}: {json.dumps(event, indent=2)}")
        event_result = service.events().insert(calendarId=calendar_id, body=event).execute()
        logger.info(f"Evento criado com sucesso: {event_result.get('id')}")
        return {
            "message": f"A reunião \"{summary}\" foi marcada para às {start['dateTime'].split('T')[1][:5]}. Indique os participantes.",
            "eventId": event_result.get("id")
        }
    except HttpError as http_error:
        logger.error(f"Erro HTTP ao criar evento: {http_error}")
        return {"error": f"Erro na API do Google Calendar: {http_error}"}
    except Exception as e:
        logger.error(f"Erro ao agendar evento no Google Calendar: {e}")
        return {"error": str(e) or "Falha ao agendar evento"}

async def get_event(calendar_id: str, date_str: str = None) -> dict:
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

        if date_str:
            target_date = datetime.strptime(date_str, "%d/%m/%Y")
        else:
            target_date = datetime.now()

        time_min = target_date.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "-03:00"
        time_max = (target_date + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "-03:00"

        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = events_result.get("items", [])
        if not events:
            return {"message": f"Nenhum evento planejado para {target_date.strftime('%d/%m/%Y')}!"}

        response = f"Eventos planejados para {target_date.strftime('%d/%m/%Y')}:\n\n"
        for event in events:
            start_time = datetime.fromisoformat(event['start']['dateTime'].replace("Z", "+00:00")).strftime("%H:%M")
            end_time = datetime.fromisoformat(event['end']['dateTime'].replace("Z", "+00:00")).strftime("%H:%M")
            response += f"- {event['summary']} ({start_time} - {end_time})\n"

        logger.info(f"Eventos encontrados para {calendar_id} em {target_date.strftime('%d/%m/%Y')}")
        return {"message": response}
    except HttpError as http_error:
        logger.error(f"Erro HTTP ao buscar eventos: {http_error}")
        return {"error": f"Erro na API do Google Calendar: {http_error}"}
    except Exception as e:
        logger.error(f"Erro ao buscar eventos: {e}")
        return {"error": str(e)}

async def add_participant(calendar_id: str, summary: str, participant: str) -> dict:
    try:
        credentials_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=["https://www.googleapis.com/auth/calendar"]
        )
        service = build("calendar", "v3", credentials=credentials)

        events_result = service.events().list(calendarId=calendar_id, q=summary).execute()
        event = next((e for e in events_result.get("items", []) if e["summary"] == summary), None)
        if not event:
            return {"error": f"Reunião \"{summary}\" não encontrada."}

        event_id = event["id"]
        attendees = event.get("attendees", [])
        attendees.append({"email": participant})
        updated_event = {"attendees": attendees}

        service.events().patch(calendarId=calendar_id, eventId=event_id, body=updated_event).execute()
        return {"message": f"Os participantes foram adicionados à reunião \"{summary}\"."}
    except Exception as e:
        logger.error(f"Erro ao adicionar participante: {e}")
        return {"error": str(e)}

async def remove_participant(calendar_id: str, summary: str, participant: str) -> dict:
    try:
        credentials_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=["https://www.googleapis.com/auth/calendar"]
        )
        service = build("calendar", "v3", credentials=credentials)

        events_result = service.events().list(calendarId=calendar_id, q=summary).execute()
        event = next((e for e in events_result.get("items", []) if e["summary"] == summary), None)
        if not event:
            return {"error": f"Reunião \"{summary}\" não encontrada."}

        event_id = event["id"]
        attendees = event.get("attendees", [])
        updated_attendees = [a for a in attendees if a["email"] != participant]
        updated_event = {"attendees": updated_attendees}

        service.events().patch(calendarId=calendar_id, eventId=event_id, body=updated_event).execute()
        return {"message": f"O participante foi removido da reunião \"{summary}\"."}
    except Exception as e:
        logger.error(f"Erro ao remover participante: {e}")
        return {"error": str(e)}

async def cancel_meeting(calendar_id: str, summary: str) -> dict:
    try:
        credentials_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=["https://www.googleapis.com/auth/calendar"]
        )
        service = build("calendar", "v3", credentials=credentials)

        events_result = service.events().list(calendarId=calendar_id, q=summary).execute()
        event = next((e for e in events_result.get("items", []) if e["summary"] == summary), None)
        if not event:
            return {"error": f"Reunião \"{summary}\" não encontrada."}

        event_id = event["id"]
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        return {"message": f"A reunião \"{summary}\" foi cancelada com sucesso."}
    except Exception as e:
        logger.error(f"Erro ao cancelar reunião: {e}")
        return {"error": str(e)}

async def edit_meeting(calendar_id: str, summary: str, new_date: str, new_time: str) -> dict:
    try:
        credentials_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=["https://www.googleapis.com/auth/calendar"]
        )
        service = build("calendar", "v3", credentials=credentials)

        events_result = service.events().list(calendarId=calendar_id, q=summary).execute()
        event = next((e for e in events_result.get("items", []) if e["summary"] == summary), None)
        if not event:
            return {"error": f"Reunião \"{summary}\" não encontrada."}

        event_id = event["id"]
        new_dt = datetime.strptime(f"{new_date} {new_time}", "%d/%m/%Y %H:%M")
        duration = datetime.fromisoformat(event['end']['dateTime'].replace("Z", "+00:00")) - datetime.fromisoformat(event['start']['dateTime'].replace("Z", "+00:00"))
        new_end_dt = new_dt + duration

        updated_event = {
            "start": {"dateTime": new_dt.isoformat() + "-03:00", "timeZone": "America/Sao_Paulo"},
            "end": {"dateTime": new_end_dt.isoformat() + "-03:00", "timeZone": "America/Sao_Paulo"}
        }

        service.events().patch(calendarId=calendar_id, eventId=event_id, body=updated_event).execute()
        return {"message": f"A reunião \"{summary}\" foi reagendada para {new_date} às {new_time}."}
    except Exception as e:
        logger.error(f"Erro ao editar reunião: {e}")
        return {"error": str(e)}

async def get_free_time(calendar_id: str, date_str: str = None) -> dict:
    try:
        credentials_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=["https://www.googleapis.com/auth/calendar"]
        )
        service = build("calendar", "v3", credentials=credentials)

        target_date = datetime.strptime(date_str, "%d/%m/%Y") if date_str else datetime.now() + timedelta(days=1)  # Amanhã por padrão
        time_min = target_date.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "-03:00"
        time_max = (target_date + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "-03:00"

        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = events_result.get("items", [])
        busy_times = []
        for event in events:
            start = datetime.fromisoformat(event['start']['dateTime'].replace("Z", "+00:00"))
            end = datetime.fromisoformat(event['end']['dateTime'].replace("Z", "+00:00"))
            busy_times.append((start, end))

        # Horário de trabalho padrão: 08:00 às 18:00
        day_start = target_date.replace(hour=8, minute=0)
        day_end = target_date.replace(hour=18, minute=0)
        free_times = []
        current_time = day_start

        for start, end in sorted(busy_times, key=lambda x: x[0]):
            if current_time < start:
                free_times.append((current_time, start))
            current_time = max(current_time, end)

        if current_time < day_end:
            free_times.append((current_time, day_end))

        if not free_times:
            return {"message": f"Nenhum horário livre em {target_date.strftime('%d/%m/%Y')} entre 08:00 e 18:00!"}

        response = f"Horários Livres em {target_date.strftime('%d/%m/%Y')}:\n"
        for start, end in free_times:
            response += f"{start.strftime('%H:%M')} às {end.strftime('%H:%M')}\n"
        return {"message": response}
    except Exception as e:
        logger.error(f"Erro ao buscar horários livres: {e}")
        return {"error": str(e)}

async def get_busy_days(calendar_id: str, month: str = None) -> dict:
    try:
        credentials_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=["https://www.googleapis.com/auth/calendar"]
        )
        service = build("calendar", "v3", credentials=credentials)

        now = datetime.now()
        target_month = datetime.strptime(month, "%m/%Y") if month else now.replace(day=1)
        time_min = target_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat() + "-03:00"
        time_max = (target_month.replace(day=1) + timedelta(days=31)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "-03:00"

        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True
        ).execute()

        events = events_result.get("items", [])
        day_counts = {}
        for event in events:
            start = datetime.fromisoformat(event['start']['dateTime'].replace("Z", "+00:00"))
            day_key = start.strftime("%d/%m")
            day_counts[day_key] = day_counts.get(day_key, 0) + 1

        sorted_days = sorted(day_counts.items(), key=lambda x: x[1], reverse=True)[:3]  # Top 3 dias mais ocupados
        if not sorted_days:
            return {"message": f"Nenhum evento em {target_month.strftime('%B')}!"}

        month_name = target_month.strftime("%B")
        response = f"Dias Mais Ocupados ({month_name}):\n"
        for day, count in sorted_days:
            response += f"{day}: {count} reuniões\n"
        return {"message": response}
    except Exception as e:
        logger.error(f"Erro ao buscar dias ocupados: {e}")
        return {"error": str(e)}

async def clear_calendar(calendar_id: str, date_str: str = None) -> dict:
    try:
        credentials_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))
        credentials = service_account.Credentials.from_service_account_info(
            credentials_dict,
            scopes=["https://www.googleapis.com/auth/calendar"]
        )
        service = build("calendar", "v3", credentials=credentials)

        target_date = datetime.strptime(date_str, "%d/%m/%Y") if date_str else datetime.now()
        time_min = target_date.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "-03:00"
        time_max = (target_date + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "-03:00"

        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = events_result.get("items", [])
        if not events:
            return {"message": f"Nenhum evento para cancelar em {target_date.strftime('%d/%m/%Y')}!"}

        response = f"🗑️ Cancelar Todas as Reuniões de {target_date.strftime('%d/%m/%Y')}:\n"
        for event in events:
            start_time = datetime.fromisoformat(event['start']['dateTime'].replace("Z", "+00:00")).strftime("%H:%M")
            response += f"{event['summary']} ({start_time})\n"
        response += "Use /cancelmeeting <título> para confirmar."
        return {"message": response}
    except Exception as e:
        logger.error(f"Erro ao listar eventos para cancelamento: {e}")
        return {"error": str(e)}