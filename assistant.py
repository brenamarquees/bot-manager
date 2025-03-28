import os
import requests
import logging
from dotenv import load_dotenv

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

BASE_PROMPT = """
Você é um assistente de IA útil e amigável chamado Grok, criado pela xAI. 
Responda de forma clara, concisa e educada. Se não souber algo, admita e sugira onde o usuário pode buscar a informação.
"""

TEMPERATURE = 0.7

async def get_gemini_response(message: str, custom_prompt: str = BASE_PROMPT, temperature: float = TEMPERATURE) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    full_prompt = f"{custom_prompt}\n\nPergunta do usuário: {message}"
    
    data = {
        "contents": [{"parts": [{"text": full_prompt}]}],
        "generationConfig": {
            "temperature": temperature
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 429:
            return "Limite de requisições excedido, tente novamente mais tarde"
        
        response.raise_for_status()
        
        result = response.json()
        return result["candidates"][0]["content"]["parts"][0]["text"]
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Erro na API Gemini: {e}")
        return "Desculpe, ocorreu um erro ao processar sua mensagem"