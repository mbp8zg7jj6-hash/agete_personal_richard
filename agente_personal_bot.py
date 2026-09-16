import os
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import anthropic

MEMORY = {"conversations": []}

def get_client():
    return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Soy tu agente personal.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.chat.send_action("typing")
        
        user_msg = update.message.text
        msgs = []
        for conv in MEMORY["conversations"][-10:]:
            msgs.append({"role": "user", "content": conv["user"]})
            msgs.append({"role": "assistant", "content": conv["agent"]})
        msgs.append({"role": "user", "content": user_msg})
        
        client = get_client()
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=1024,
            system="Eres amigable y recuerdas lo que el usuario te dice.",
            messages=msgs
        )
        
       answer = ""
for block in response.content:
    if block.type == "text":
        answer += block.text

if not answer:
    answer = "No pude responder."
        MEMORY["conversations"].append({"user": user_msg, "agent": answer})
        await update.message.reply_text(answer)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")

def main():
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == "__main__":
    main()
