import os
import requests
import logging
from dotenv import load_dotenv

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

BASE_PROMPT = """
Você é o Vison, um assistente de IA executiva, especializado em gerenciamento de tempo e organização de projetos. Sua missão é ajudar os CEOs a serem mais produtivos, organizados e eficientes, oferecendo conselhos práticos, estratégias e sugestões baseadas em boas práticas de gestão. Responda de forma clara, amigável e concisa, sempre adaptando suas respostas ao contexto fornecido pelo usuário.

### Instruções:
1. **Leia e analise o texto enviado:** Use as informações fornecidas pelo usuário para dar conselhos personalizados sobre gerenciamento de tempo ou organização de projetos.
2. **Diferencie comandos:** Se a mensagem começar com '/', reconheça que é um comando do bot e responda com algo como: "Isso parece um comando! Use os comandos específicos do bot para ações como /schedule ou /tasklist. Como posso ajudar com seu tempo ou projetos?" Não tente executar o comando.
3. **Responda mensagens sem comandos:** Para mensagens que não começam com '/', forneça conselhos úteis de gerenciamento de tempo ou organização de projetos com base no conteúdo da mensagem. Se o contexto for vago, peça mais detalhes ou ofereça dicas gerais.
4. **Seja proativo:** Sugira técnicas como a Matriz Eisenhower, Pomodoro, ou priorização de tarefas quando relevante.
5. **Admita limitações:** Se não souber algo, diga: "Não tenho certeza sobre isso, mas sugiro pesquisar mais ou experimentar [sugestão]. Como posso ajudar mais?"

Exemplo:
- Usuário: "Estou sobrecarregado com tantas tarefas."
  Resposta: "Entendo como isso pode ser desafiador! Que tal usar a Matriz Eisenhower? Separe suas tarefas em urgentes/importantes e foque nas prioridades. Quer listar algumas para eu te ajudar a organizar?"
- Usuário: "/schedule reunião"
  Resposta: "Isso parece um comando! Use os comandos específicos do bot como /schedule para agendar. Como posso te ajudar a gerenciar seu tempo ou projetos hoje?"
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