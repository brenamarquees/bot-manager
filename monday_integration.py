import os
import requests
import json
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)
MONDAY_API_KEY = os.getenv("MONDAY_API_KEY")
MONDAY_API_URL = "https://api.monday.com/v2"

async def get_monday_summary() -> dict:
    if not MONDAY_API_KEY:
        raise ValueError("MONDAY_API_KEY não está configurado no .env")

    headers = {
        "Authorization": MONDAY_API_KEY,
        "Content-Type": "application/json"
    }

    query = """
    {
        boards(limit: 10) {
            name
            columns {
                id
                title
            }
            items_page(limit: 50) {
                items {
                    name
                    column_values {
                        id
                        text
                        value
                    }
                }
            }
        }
    }
    """
    
    payload = {"query": query}

    try:
        response = requests.post(MONDAY_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        if "data" not in data or "boards" not in data["data"]:
            raise ValueError("Resposta inválida da API do Monday.com")

        boards = data["data"]["boards"]
        summary = "Oi! Aqui está um resumo dos seus projetos no Monday.com:\n\n"
        
        for board in boards:
            board_name = board['name']
            summary += f"📋 *{board_name}*:\n"
            items_page = board.get("items_page", {})
            items = items_page.get("items", [])
            columns = {col["id"]: col["title"] for col in board.get("columns", [])}

            if not items:
                summary += "   - Nada por aqui ainda!\n"
                continue

            for item in items:
                column_values = {col["id"]: col for col in item["column_values"]}
                
                if board_name == "Sprints":
                    timeline = next((col["text"] for col in column_values.values() if columns.get(col["id"]) == "Timeline"), "Sem cronograma")
                    goal = next((col["text"] for col in column_values.values() if columns.get(col["id"]) == "Goal" or columns.get(col["id"]) == "Meta"), "Sem meta")
                    summary += f"   - {item['name']} (Cronograma: {timeline}, Meta: {goal})\n"
                
                elif board_name == "Épicos":
                    owners = next((col["text"] for col in column_values.values() if columns.get(col["id"]) == "Person" or columns.get(col["id"]) == "Owner"), "Sem proprietário")
                    phase = next((col["text"] for col in column_values.values() if columns.get(col["id"]) == "Phase" or columns.get(col["id"]) == "Fase"), "Sem fase")
                    summary += f"   - {item['name']} (Responsável: {owners}, Fase: {phase})\n"
                
                elif board_name == "Retrospectivas":
                    recurring = next((col["text"] for col in column_values.values() if columns.get(col["id"]) == "Recurring" or columns.get(col["id"]) == "Recorrente"), "Não especificado")
                    type_ = next((col["text"] for col in column_values.values() if columns.get(col["id"]) == "Type" or columns.get(col["id"]) == "Tipo"), "Sem tipo")
                    summary += f"   - {item['name']} (Recorrente: {recurring}, Tipo: {type_})\n"
                
                elif board_name != "Introdução":  # Ignora o board "Introdução"
                    status = next((col["text"] for col in column_values.values() if columns.get(col["id"]) == "Status"), "Sem status")
                    summary += f"   - {item['name']} (Status: {status})\n"
            
            summary += "\n"

        logger.info("Resumo do Monday.com gerado com sucesso")
        return {"message": summary}
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na API do Monday.com: {e}")
        logger.error(f"Resposta da API: {e.response.text}")
        return {"error": f"Oops! Algo deu errado ao consultar o Monday.com: {str(e)}"}
    except Exception as e:
        logger.error(f"Erro ao processar dados do Monday.com: {e}")
        return {"error": f"Eita! Falha ao gerar o resumo: {str(e)}"}