import os
import json
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import anthropic

# Configurar cliente de Anthropic
def get_anthropic_client():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY no configurada")
    return anthropic.Anthropic(
        api_key=api_key,
        timeout=30.0
    )

# Ruta del archivo de memoria
MEMORY_FILE = "memory.json"

def load_memory():
    """Carga la memoria del archivo JSON"""
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"conversations": [], "user_details": {}}

def save_memory(memory):
    """Guarda la memoria en el archivo JSON"""
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

def extract_user_details(message_text, current_details):
    """Intenta extraer detalles sobre el usuario del mensaje"""
    keywords = {
        "trabajo": ["trabajo", "empresa", "puesto", "laboro", "ocupación"],
        "hobbies": ["me gusta", "hobby", "disfruto", "pasatiempo", "me encanta"],
        "proyectos": ["proyecto", "estoy trabajando", "planeo", "voy a"],
        "familia": ["familia", "esposa", "hijo", "hermano", "papá", "mamá"],
        "ubicación": ["vivo en", "estoy en", "ciudad"],
    }
    
    details = current_details.copy()
    
    for category, words in keywords.items():
        if any(word in message_text.lower() for word in words):
            if category not in details:
                details[category] = []
            if message_text not in details[category]:
                details[category].append(message_text)
    
    return details

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    await update.message.reply_text(
        "¡Hola! Soy tu agente personal. Platiquemos, conóceme y déjame conocerte. "
        "Estoy aquí para escucharte, recordar detalles sobre ti y darte recomendaciones honestas.\n\n"
        "¿Cómo estás?"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los mensajes del usuario"""
    user_message = update.message.text
    user_id = update.message.from_user.id
    
    try:
        # Cargar memoria
        memory = load_memory()
        
        # Extraer detalles del usuario si hay
        memory["user_details"] = extract_user_details(user_message, memory["user_details"])
        
        # Construir contexto para Claude
        context_text = "Eres un agente personal amigable, casual y honesto. Tu objetivo es:\n"
        context_text += "1. Ser un compañero de conversación genuino\n"
        context_text += "2. Recordar detalles sobre la persona y usarlos en la conversación\n"
        context_text += "3. Dar recomendaciones honestas (sin fabricar cosas)\n"
        context_text += "4. Nunca mentir\n\n"
        
        # Agregar detalles conocidos del usuario si los hay
        if memory["user_details"]:
            context_text += "Detalles que sé sobre el usuario:\n"
            for category, items in memory["user_details"].items():
                context_text += f"- {category}: {', '.join(set(items[:3]))}\n"
            context_text += "\n"
        
        # Agregar últimas conversaciones para contexto
        if memory["conversations"]:
            context_text += "Conversaciones recientes:\n"
            for conv in memory["conversations"][-5:]:
                context_text += f"Usuario: {conv['user']}\nAgente: {conv['agent']}\n\n"
        
        # Llamar a Claude
        await update.message.chat.send_action("typing")
        
        client = get_anthropic_client()
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=1024,
            system=context_text,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        
        agent_response = ""
for block in response.content:
    if hasattr(block, 'text'):
        agent_response += block.text
        
        # Guardar conversación en memoria
        memory["conversations"].append({
            "timestamp": datetime.now().isoformat(),
            "user": user_message,
            "agent": agent_response
        })
        
        # Mantener solo las últimas 50 conversaciones
        if len(memory["conversations"]) > 50:
            memory["conversations"] = memory["conversations"][-50:]
        
        # Guardar memoria
        save_memory(memory)
        
        # Enviar respuesta
        await update.message.reply_text(agent_response)
        
    except Exception as e:
        await update.message.reply_text(
            f"Hubo un error: {str(e)}"
        )

def main():
    """Función principal para iniciar el bot"""
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
