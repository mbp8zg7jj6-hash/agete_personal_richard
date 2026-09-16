import os
import json
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import anthropic

MEMORY_FILE = "/tmp/memory.json"

def get_anthropic_client():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY no configurada")
    return anthropic.Anthropic(api_key=api_key)

def load_memory():
    try:
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"conversations": []}

def save_memory(memory):
    try:
        with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)
    except:
        pass

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Soy tu agente personal.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    memory = load_memory()
    
    try:
        await update.message.chat.send_action("typing")
        
        messages_list = []
        for conv in memory.get("conversations", [])[-5:]:
            messages_list.append({"role": "user", "content": conv["user"]})
            messages_list.append({"role": "assistant", "content": conv["agent"]})
        
        messages_list.append({"role": "user", "content": user_message})
        
        client = get_anthropic_client()
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=1024,
            system="Eres un agente personal amigable y honesto.",
            messages=messages_list
        )
        
        agent_response = ""
        for block in response.content:
            if hasattr(block, "text") and block.type == "text":
                agent_response += block.text
        
        if not agent_response:
            agent_response = "No pude responder."
        
        memory["conversations"].append({
            "user": user_message,
            "agent": agent_response
        })
        
        if len(memory.get("conversations", [])) > 50:
            memory["conversations"] = memory["conversations"][-50:]
        
        save_memory(memory)
        await update.message.reply_text(agent_response)
        
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        return
    
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == "__main__":
    main()
