import os
import json
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import anthropic
import dropbox
from dropbox.exceptions import ApiError

DROPBOX_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
MEMORY_FILE = "memory.json"

def get_anthropic_client():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY no configurada")
    return anthropic.Anthropic(api_key=api_key)

def get_dropbox_client():
    if not DROPBOX_TOKEN:
        raise ValueError("DROPBOX_ACCESS_TOKEN no configurado")
    return dropbox.Dropbox(DROPBOX_TOKEN)

def load_memory():
    try:
        dbx = get_dropbox_client()
        _, response = dbx.files_download(f"/{MEMORY_FILE}")
        data = json.loads(response.content.decode('utf-8'))
        return data
    except ApiError:
        return {"conversations": [], "user_details": {}}

def save_memory(memory):
    try:
        dbx = get_dropbox_client()
        dbx.files_upload(
            json.dumps(memory, ensure_ascii=False, indent=2).encode('utf-8'),
            f"/{MEMORY_FILE}",
            mode=dropbox.files.WriteMode('overwrite')
        )
    except Exception as e:
        print(f"Error guardando en Dropbox: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Soy tu agente personal. Platiquemos, conóceme y déjame conocerte.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    memory = load_memory()
    
    try:
        context_text = "Eres un agente personal amigable, casual y honesto. Escucha, recuerda y da consejos sinceros."
        
        await update.message.chat.send_action("typing")
        
        messages_list = []
        for conv in memory["conversations"][-5:]:
            messages_list.append({"role": "user", "content": conv["user"]})
            messages_list.append({"role": "assistant", "content": conv["agent"]})
        
        messages_list.append({"role": "user", "content": user_message})
        
        client = get_anthropic_client()
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=1024,
            system=context_text,
            messages=messages_list
        )
        
        agent_response = ""
        for block in response.content:
            if hasattr(block, "text") and block.type == "text":
                agent_response += block.text
        
        if not agent_response:
            agent_response = "No pude generar una respuesta."
        
        memory["conversations"].append({
            "timestamp": datetime.now().isoformat(),
            "user": user_message,
            "agent": agent_response
        })
        
        if len(memory["conversations"]) > 50:
            memory["conversations"] = memory["conversations"][-50:]
        
        save_memory(memory)
        await update.message.reply_text(agent_response)
        
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("ERROR: No TELEGRAM_BOT_TOKEN")
        return
    
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot iniciado...")
    application.run_polling()

if __name__ == "__main__":
    main()
