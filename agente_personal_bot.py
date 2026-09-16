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
            try:
                if block.type == "text":
                    answer += block.text
            except:
                continue
        
        if not answer:
            answer = "No pude responder."
        
        MEMORY["conversations"].append({"user": user_msg, "agent": answer})
        await update.message.reply_text(answer)
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")
