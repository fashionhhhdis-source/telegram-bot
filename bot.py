import os
import logging
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import yt_dlp

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "مرحباً بك في بوت تحميل الوسائط الشامل 🌟\n\n"
        "أرسل أي رابط فيديو أو صور (تيك توك، إنستغرام، وغيرها) وسأقوم بتحميله لك فوراً!\n\n"
        "⚠️ **تنبيه هام:**\n"
        "هذه الأداة مخصصة للاستخدام الشخصي والمباح فقط، وأنا بريء من استخدامها فيما لا يرضي الله."
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not url.startswith("http"):
        await update.message.reply_text("الرجاء إرسال رابط صالح يبدأ بـ http أو https.")
        return

    status_msg = await update.message.reply_text("⚡ جاري التحميل...")

    output_dir = os.path.abspath("downloads")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    success = False

    # فحص شامل وصريح: إذا كان الرابط يحتوي على photo أو gallery أو image
    is_photo = "photo" in url or "gallery" in url or "image" in url

    # إذا لم يكن رابط صور صريح، نحاول تحميله كفيديو أولاً
    if not is_photo:
        ydl_opts = {
            'format': 'best/bestvideo+bestaudio',
            'outtmpl': os.path.join(output_dir, '%(id)s.%(ext)s'),
            'ignoreerrors': True,
            'no_warnings': True,
            'socket_timeout': 30,
            'retries': 3,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info:
                    if 'entries' in info:
                        info = info['entries'][0]
                    filename = ydl.prepare_filename(info)
                    if filename and os.path.exists(filename):
                        success = True
        except Exception:
            pass

    # إذا كان رابط صور، أو فشل محرك الفيديو، ننتقل فوراً لـ gallery-dl
    if not success:
        try:
            cmd = f'python -m gallery_dl --dest "{output_dir}" --no-mtime "{url}"'
            result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                success = True
        except Exception as e:
            logging.error(f"Gallery-dl error: {e}")

    if success:
        files = [os.path.join(output_dir, f) for f in os.listdir(output_dir)]
        if files:
            files.sort(key=os.path.getmtime, reverse=True)
            target_file = files[0]
            file_lower = target_file.lower()

            try:
                await status_msg.delete()
            except:
                pass

            if file_lower.endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
                with open(target_file, 'rb') as p_file:
                    await update.message.reply_photo(photo=p_file)
                try:
                    os.remove(target_file)
                except:
                    pass
            elif file_lower.endswith(('.mp4', '.mkv', '.webm', '.mov', '.avi')):
                keyboard = [[InlineKeyboardButton("🎵 تحويل إلى MP3", callback_data=f"audio|{target_file}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                with open(target_file, 'rb') as v_file:
                    await update.message.reply_video(video=v_file, reply_markup=reply_markup)
            else:
                # إرسال عدة صور إذا تم تحميل ألبوم كامل
                sent = 0
                for f in files[:10]:
                    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
                        with open(f, 'rb') as pf:
                            await update.message.reply_photo(photo=pf)
                        sent += 1
                        try:
                            os.remove(f)
                        except:
                            pass
                if sent == 0:
                    await update.message.reply_text("❌ تم التحميل ولكن تعذر تحديد صيغة الملف.")
        else:
            await status_msg.edit_text("❌ لم يتم العثور على ملفات بعد التحميل.")
    else:
        await status_msg.edit_text("❌ عذراً، فشل تحميل المحتوى. تأكد أن الرابط عام وصحيح.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("audio|"):
        video_path = data.split("|", 1)[1]
        if not os.path.exists(video_path):
            await query.edit_message_caption(caption="عذراً، الملف غير موجود.")
            return

        await query.edit_message_caption(caption="🔄 جاري استخراج الصوت...")

        try:
            mp3_path = video_path.rsplit('.', 1)[0] + '.mp3'
            cmd = f'ffmpeg -i "{video_path}" -q:a 0 -map a "{mp3_path}" -y'
            subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            if os.path.exists(mp3_path):
                with open(mp3_path, 'rb') as audio_file:
                    await query.message.reply_audio(audio=audio_file)
                await query.edit_message_caption(caption="✅ تم إرسال الصوت بنجاح!")
                
                for p in [mp3_path, video_path]:
                    if os.path.exists(p):
                        os.remove(p)
            else:
                await query.edit_message_caption(caption="❌ فشل استخراج الصوت.")
        except Exception as e:
            await query.edit_message_caption(caption=f"حدث خطأ: {e}")

def main():
    TOKEN = "8688301918:AAES4fwVLwauScWBAyIUZZ7A-behpuMp0QU"
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))

    print("البوت يعمل الآن بكفاءة عالية...")
    application.run_polling()

if __name__ == "__main__":
    main()