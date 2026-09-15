import os
import json
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import anthropic

def get_anthropic_client():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY no configurada")
    return anthropic.Anthropic(api_key=api_key)

MEMORY_FILE = "memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"conversations": [], "user_details": {}}

def save_memory(memory):
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Soy tu agente personal. Platiquemos, conóceme y déjame conocerte.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    memory = load_memory()
    
    try:
        context_text = "Eres un agente personal amigable, casual y honesto. Escucha, recuerda y da consejos sinceros."
        
        await update.message.chat.send_action("typing")
        
        client = get_anthropic_client()
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=1024,
            system=context_text,
            messages=[{"role": "user", "content": user_message}]
        )
        
        agent_response = response.content[0].text
        
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
        print("ERROR: No se encontró TELEGRAM_BOT_TOKEN")
        return
    
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot iniciado...")
    application.run_polling()

if __name__ == "__main__":
    main()
