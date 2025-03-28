import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
)
import logging
from schedule_calendar import schedule_event, get_event
from assistant import get_gemini_response

# Configura logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Estados do ConversationHandler para o fluxo de agendamento
EMAIL, SUMMARY, START_TIME, END_TIME = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Olá! Eu sou um bot com IA. Use:\n"
        "/ask - para falar com a assistente\n"
        "/schedule - para agendar um evento\n"
        "/getevent - para buscar um evento"
    )

async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Uso: /ask 'sua pergunta'\nExemplo: /ask 'Qual é o sentido da vida?'")
        return
    message = " ".join(args)
    logger.info(f"Recebida pergunta para a assistente: {message}")
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    reply = await get_gemini_response(message, temperature=0.7)
    await update.message.reply_text(reply)

# Início do fluxo de agendamento
async def schedule_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Por favor, digite o e-mail do calendário onde o evento será agendado (ex.: 'brenamarq@gmail.com').")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['calendar_id'] = update.message.text
    await update.message.reply_text("Digite o nome da reunião (ex.: 'Reunião com equipe').")
    return SUMMARY

async def get_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['summary'] = update.message.text
    await update.message.reply_text("Digite o horário de início no formato 'YYYY-MM-DDTHH:MM:SS-03:00' (ex.: '2025-03-21T10:00:00-03:00').")
    return START_TIME

async def get_start_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['start_time'] = update.message.text
    await update.message.reply_text("Digite o horário de término no formato 'YYYY-MM-DDTHH:MM:SS-03:00' (ex.: '2025-03-21T11:00:00-03:00').")
    return END_TIME

async def get_end_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    calendar_id = context.user_data['calendar_id']
    summary = context.user_data['summary']
    start_time = context.user_data['start_time']
    end_time = update.message.text

    event_start = {"dateTime": start_time, "timeZone": "America/Sao_Paulo"}
    event_end = {"dateTime": end_time, "timeZone": "America/Sao_Paulo"}

    logger.info(f"Tentando agendar evento: {summary}, início: {event_start}, fim: {event_end}, email: {calendar_id}")
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    result = await schedule_event(summary, event_start, event_end, calendar_id)
    
    if "error" in result:
        await update.message.reply_text(f"Erro ao agendar: {result['error']}")
    else:
        await update.message.reply_text(f"{result['message']} ID do evento: {result['eventId']}")
    
    # Limpa os dados do usuário após o agendamento
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Agendamento cancelado.")
    context.user_data.clear()
    return ConversationHandler.END

async def get_event_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Uso: /getevent 'ID do evento' 'email'\nExemplo: /getevent 'as9tv21ocg7r91v7enaina3c3o' 'brenamarq@gmail.com'")
        return
    event_id = args[0]
    calendar_id = args[1]
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    result = await get_event(event_id, calendar_id)
    if "error" in result:
        await update.message.reply_text(f"Erro: {result['error']}")
    else:
        event = result["event"]
        response = f"Evento: {event['summary']}\nInício: {event['start']['dateTime']}\nFim: {event['end']['dateTime']}"
        await update.message.reply_text(response)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Use /ask, /schedule ou /getevent!")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Erro: {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text("Ocorreu um erro inesperado. Por favor, tente novamente.")

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # Configura o ConversationHandler para o fluxo de agendamento
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("schedule", schedule_start)],
        states={
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            SUMMARY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_summary)],
            START_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_start_time)],
            END_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_end_time)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    # Adiciona handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ask", ask))
    application.add_handler(conv_handler)  # Handler do fluxo de agendamento
    application.add_handler(CommandHandler("getevent", get_event_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)

    logger.info("Bot iniciado com sucesso")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()