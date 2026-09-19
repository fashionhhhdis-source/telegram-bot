import os
import subprocess
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# قراءة توكن البوت بطريقة آمنة من متغيرات البيئة
TOKEN = os.getenv("8688301918:AAES4fwVLwauScWBAyIUZZ7A-behpuMp0QU")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "أهلاً بك!\n"
        "أنا بوت لتحميل الملفات والفيديوهات.\n"
        "📌 أُذكرك دائماً بتقوى الله، وألّا يُستخدم هذا البوت إلا فيما يرضي الله وفيما هو نافع ومباح."
    )
    await update.message.reply_text(welcome_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"):
        await update.message.reply_text("الرجاء إرسال رابط صالح يبدأ بـ http أو https.")
        return

    await update.message.reply_text("جاري معالجة وتحميل الملف... انتظر قليلاً 📥")
    
    try:
        output_dir = "/tmp"
        cmd = f"yt-dlp -P {output_dir} '{url}'"
        subprocess.run(cmd, shell=True, check=True)
        await update.message.reply_text("تم التحميل بنجاح!")
    except Exception as e:
        await update.message.reply_text(f"حدث خطأ أثناء التحميل: {str(e)}")

def main():
    if not TOKEN:
        raise ValueError("BOT_TOKEN environment variable is missing!")
    
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return application

app_instance = main()
