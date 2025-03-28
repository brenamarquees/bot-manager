import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
)
import logging
from schedule_calendar import (
    schedule_event, get_event, add_participant, remove_participant, 
    cancel_meeting, edit_meeting, get_free_time, get_busy_days, clear_calendar
)
from assistant import get_gemini_response
from monday_integration import get_monday_summary  
from datetime import datetime

# Configura logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Carrega variáveis de ambiente
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Lista de tarefas em memória
tasks = []

# Estados do ConversationHandler para o fluxo de agendamento
EMAIL, SUMMARY, START_TIME, END_TIME = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Olá! Eu sou Vision, sua IA executiva para gestão de tempo e projetos.\n\n"
        "Organize sua rotina com comandos simples (ex.: \"/schedule\", \"/tasklist\") e receba conselhos personalizados "
        "enviando mensagens sem \"/\". Estou aqui para otimizar seu dia!\n\n"
        "Comandos disponíveis:\n"
        "• Para falar comigo diretamente me mande mensagem a qualquer momento, é só escrever que te respondo.\n"
        "• \"/schedule\" - Agende eventos\n"
        "• \"/getevent\" - Veja sua agenda do dia\n"
        "• \"/monday\" - Resumo do Monday.com\n"
        "• \"/addparticipant\" - Adicione participantes a reuniões\n"
        "• \"/removeparticipant\" - Remova participantes\n"
        "• \"/cancelmeeting\" - Cancele uma reunião\n"
        "• \"/editmeeting\" - Edite data/hora de reuniões\n"
        "• \"/tasklist\" - Liste tarefas pendentes\n"
        "• \"/addtask\" - Adicione uma tarefa\n"
        "• \"/removetask\" - Remova uma tarefa\n"
        "• \"/prioritizetask\" - Defina prioridades\n"
        "• \"/freetime\" - Veja horários livres\n"
        "• \"/busydays\" - Dias mais ocupados do mês\n"
        "• \"/clearcalendar\" - Liste reuniões para cancelar\n\n"
        "Experimente agora! Como posso ajudar você hoje?"
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

async def schedule_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Por favor, digite o e-mail do calendário onde o evento será agendado (ex.: 'brenamarq@gmail.com').")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['calendar_id'] = update.message.text
    await update.message.reply_text("Digite o nome da reunião (ex.: 'Reunião com equipe').")
    return SUMMARY

async def get_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['summary'] = update.message.text
    await update.message.reply_text("Digite o horário de início no formato 'DD/MM/YYYY HH:MM' (ex.: '21/03/2025 10:00').")
    return START_TIME

async def get_start_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_time_str = update.message.text
    try:
        start_dt = datetime.strptime(start_time_str, "%d/%m/%Y %H:%M")
        context.user_data['start_time_iso'] = start_dt.isoformat() + "-03:00"
        await update.message.reply_text("Digite o horário de término no formato 'DD/MM/YYYY HH:MM' (ex.: '21/03/2025 11:00').")
        return END_TIME
    except ValueError:
        await update.message.reply_text("Formato inválido! Use 'DD/MM/YYYY HH:MM' (ex.: '21/03/2025 10:00'). Tente novamente.")
        return START_TIME

async def get_end_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    calendar_id = context.user_data['calendar_id']
    summary = context.user_data['summary']
    end_time_str = update.message.text

    try:
        end_dt = datetime.strptime(end_time_str, "%d/%m/%Y %H:%M")
        start_time_iso = context.user_data['start_time_iso']
        
        event_start = {"dateTime": start_time_iso, "timeZone": "America/Sao_Paulo"}
        event_end = {"dateTime": end_dt.isoformat() + "-03:00", "timeZone": "America/Sao_Paulo"}

        logger.info(f"Tentando agendar evento: {summary}, início: {event_start}, fim: {event_end}, email: {calendar_id}")
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        await update.message.reply_text("Agendando reunião…")
        
        result = await schedule_event(summary, event_start, event_end, calendar_id)
        
        if "error" in result:
            await update.message.reply_text(f"Erro ao agendar: {result['error']}")
        else:
            await update.message.reply_text(result["message"])
        
        context.user_data.clear()
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Formato inválido! Use 'DD/MM/YYYY HH:MM' (ex.: '21/03/2025 11:00'). Tente novamente.")
        return END_TIME

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Agendamento cancelado.")
    context.user_data.clear()
    return ConversationHandler.END

async def get_event_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        calendar_id = "primary"
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        result = await get_event(calendar_id)
    elif len(args) == 1:
        calendar_id = args[0]
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        result = await get_event(calendar_id)
    elif len(args) == 2:
        calendar_id = args[0]
        date_str = args[1]
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        try:
            datetime.strptime(date_str, "%d/%m/%Y")
            result = await get_event(calendar_id, date_str)
        except ValueError:
            await update.message.reply_text("Formato de data inválido! Use 'DD/MM/YYYY' (ex.: '28/03/2025').")
            return
    else:
        await update.message.reply_text("Uso: /getevent [email] [data]\nExemplo: /getevent 'brenamarq@gmail.com' '28/03/2025'\nOu apenas /getevent para o dia atual.")
        return

    if "error" in result:
        await update.message.reply_text(f"Erro: {result['error']}")
    else:
        await update.message.reply_text(result["message"])

async def add_participant_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Uso: /addparticipant 'título' 'participante'\nExemplo: /addparticipant 'Reunião com equipe' 'joao@gmail.com'")
        return
    summary = args[0]
    participant = args[1]
    calendar_id = "primary"
    result = await add_participant(calendar_id, summary, participant)
    await update.message.reply_text(result["message"] if "message" in result else f"Erro: {result['error']}")

async def remove_participant_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Uso: /removeparticipant 'título' 'participante'\nExemplo: /removeparticipant 'Reunião com equipe' 'joao@gmail.com'")
        return
    summary = args[0]
    participant = args[1]
    calendar_id = "primary"
    result = await remove_participant(calendar_id, summary, participant)
    await update.message.reply_text(result["message"] if "message" in result else f"Erro: {result['error']}")

async def cancel_meeting_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Uso: /cancelmeeting 'título'\nExemplo: /cancelmeeting 'Reunião com equipe'")
        return
    summary = args[0]
    calendar_id = "primary"
    result = await cancel_meeting(calendar_id, summary)
    await update.message.reply_text(result["message"] if "message" in result else f"Erro: {result['error']}")

async def edit_meeting_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("Uso: /editmeeting 'título' 'nova_data' 'novo_horário'\nExemplo: /editmeeting 'Reunião com equipe' '28/03/2025' '14:00'")
        return
    summary = args[0]
    new_date = args[1]
    new_time = args[2]
    calendar_id = "primary"
    try:
        datetime.strptime(new_date, "%d/%m/%Y")
        datetime.strptime(new_time, "%H:%M")
        result = await edit_meeting(calendar_id, summary, new_date, new_time)
        await update.message.reply_text(result["message"] if "message" in result else f"Erro: {result['error']}")
    except ValueError:
        await update.message.reply_text("Formato inválido! Use 'DD/MM/YYYY' para data e 'HH:MM' para horário.")

async def task_list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not tasks:
        await update.message.reply_text("Aqui estão suas tarefas pendentes:\nNenhuma tarefa por enquanto!")
    else:
        response = "Aqui estão suas tarefas pendentes:\n"
        for task in tasks:
            response += f"- {task['description']} (Prazo: {task['deadline']}, Responsável: {task['responsible']}, Prioridade: {task['priority']})\n"
        await update.message.reply_text(response)

async def add_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 3:
        await update.message.reply_text("Uso: /addtask 'descrição' 'prazo' 'responsável'\nExemplo: /addtask 'Revisar código' '28/03/2025' 'joao'")
        return
    description = args[0]
    deadline = args[1]
    responsible = args[2]
    try:
        datetime.strptime(deadline, "%d/%m/%Y")
        tasks.append({"description": description, "deadline": deadline, "responsible": responsible, "priority": "Normal"})
        await update.message.reply_text(f"Tarefa adicionada: \"{description}\" com prazo até {deadline}.")
    except ValueError:
        await update.message.reply_text("Formato de prazo inválido! Use 'DD/MM/YYYY' (ex.: '28/03/2025').")

async def remove_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Uso: /removetask 'descrição'\nExemplo: /removetask 'Revisar código'")
        return
    description = args[0]
    global tasks
    tasks = [t for t in tasks if t["description"] != description]
    await update.message.reply_text(f"A tarefa \"{description}\" foi removida da sua lista.")

async def prioritize_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Uso: /prioritizetask 'descrição' 'prioridade'\nExemplo: /prioritizetask 'Revisar código' 'alta'")
        return
    description = args[0]
    priority = args[1].capitalize()
    for task in tasks:
        if task["description"] == description:
            task["priority"] = priority
            await update.message.reply_text(f"A tarefa \"{description}\" foi marcada como prioridade {priority}.")
            return
    await update.message.reply_text(f"Tarefa \"{description}\" não encontrada.")

async def free_time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    calendar_id = "primary"
    if args:
        date_str = args[0]
        try:
            datetime.strptime(date_str, "%d/%m/%Y")
            result = await get_free_time(calendar_id, date_str)
        except ValueError:
            await update.message.reply_text("Formato inválido! Use 'DD/MM/YYYY' (ex.: '28/03/2025').")
            return
    else:
        result = await get_free_time(calendar_id)  # Amanhã por padrão
    await update.message.reply_text(result["message"] if "message" in result else f"Erro: {result['error']}")

async def busy_days_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    calendar_id = "primary"
    if args:
        month = args[0]
        try:
            datetime.strptime(month, "%m/%Y")
            result = await get_busy_days(calendar_id, month)
        except ValueError:
            await update.message.reply_text("Formato inválido! Use 'MM/YYYY' (ex.: '06/2025').")
            return
    else:
        result = await get_busy_days(calendar_id)  # Mês atual por padrão
    await update.message.reply_text(result["message"] if "message" in result else f"Erro: {result['error']}")

async def clear_calendar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    calendar_id = "primary"
    if args:
        date_str = args[0]
        try:
            datetime.strptime(date_str, "%d/%m/%Y")
            result = await clear_calendar(calendar_id, date_str)
        except ValueError:
            await update.message.reply_text("Formato inválido! Use 'DD/MM/YYYY' (ex.: '28/03/2025').")
            return
    else:
        result = await clear_calendar(calendar_id)  # Hoje por padrão
    await update.message.reply_text(result["message"] if "message" in result else f"Erro: {result['error']}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    if message.startswith('/'):
        await update.message.reply_text("Isso parece um comando! Use os comandos disponíveis como /schedule ou /tasklist.")
    else:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        reply = await get_gemini_response(message)
        await update.message.reply_text(reply)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Erro: {context.error}")
    if update and update.effective_chat:
        await update.effective_chat.send_message("Ocorreu um erro inesperado. Por favor, tente novamente.")

async def monday_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    result = await get_monday_summary()
    if "error" in result:
        await update.message.reply_text(result["error"])
    else:
        await update.message.reply_text(result["message"])

def main():
    application = Application.builder().token(BOT_TOKEN).build()

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

    # Handlers específicos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ask", ask))
    application.add_handler(conv_handler)  # Inclui /schedule
    application.add_handler(CommandHandler("getevent", get_event_command))
    application.add_handler(CommandHandler("addparticipant", add_participant_command))
    application.add_handler(CommandHandler("removeparticipant", remove_participant_command))
    application.add_handler(CommandHandler("cancelmeeting", cancel_meeting_command))
    application.add_handler(CommandHandler("editmeeting", edit_meeting_command))
    application.add_handler(CommandHandler("tasklist", task_list_command))
    application.add_handler(CommandHandler("addtask", add_task_command))
    application.add_handler(CommandHandler("removetask", remove_task_command))
    application.add_handler(CommandHandler("prioritizetask", prioritize_task_command))
    application.add_handler(CommandHandler("freetime", free_time_command))
    application.add_handler(CommandHandler("busydays", busy_days_command))
    application.add_handler(CommandHandler("clearcalendar", clear_calendar_command))
    application.add_handler(CommandHandler("monday", monday_summary))

    # Handlers genéricos
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))  # Mensagens sem comandos
    application.add_handler(MessageHandler(filters.COMMAND, handle_message))  # Comandos não reconhecidos

    # Handler de erros
    application.add_error_handler(error_handler)  # Correção aqui

    logger.info("Bot iniciado com sucesso")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()