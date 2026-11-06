import requests
import time
import threading
import json
import logging
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

# ================= الإعدادات =================
BOT_TOKEN = "5768514554:AAGqY3bn42dACDnAyanqsiTylDl3S4_IWMU" # توكن بوت الجحش
TARGET_ID = "632621666" # الآيدي الخاص بالنجس
ADMIN_ID = "8574178583" # الآيدي الخاص بك
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ================= 1. الخادم الوهمي (للبقاء نشطاً) =================
def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    class SimpleHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"BOT IS ALIVE AND HUNTING")
        def do_HEAD(self):
            self.send_response(200)
            self.end_headers()
        def log_message(self, format, *args):
            pass
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_web_server, daemon=True).start()

# ================= 2. دوال التحكم =================
def delete_message(chat_id, message_id):
    """حذف رسالة محددة فوراً"""
    url = f"{BASE_URL}/deleteMessage"
    payload = {"chat_id": chat_id, "message_id": message_id}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"⚠️ فشل حذف الرسالة: {e}")

def send_admin_alert(text):
    """إرسال تنبيه لك"""
    try:
        requests.post(f"{BASE_URL}/sendMessage", data={"chat_id": ADMIN_ID, "text": text})
    except:
        pass

def block_and_clear():
    """حظر المستخدم (إذا أردت)"""
    print(f"🚫 جاري التحقق من الحظر للآيدي: {TARGET_ID}")

# ================= 3. المراقبة والتدمير =================
def monitor_and_destroy():
    print("🚀 بدء نظام الحذف الفوري (Anti-Forensics)...")
    
    # إرسال رسالة تأكيد لك
    send_admin_alert(f"🚀 تم تفعيل نظام الحذف الفوري للنجس ({TARGET_ID}).")
    
    offset = 0
    while True:
        try:
            url = f"{BASE_URL}/getUpdates?offset={offset}&timeout=10"
            response = requests.get(url, timeout=15)
            data = response.json()
            
            if data.get("ok"):
                for update in data["result"]:
                    offset = update["update_id"] + 1
                    
                    # --- معالجة الرسائل الواردة (من النجس) ---
                    if "message" in update:
                        msg = update["message"]
                        chat_id = msg["chat"]["id"]
                        msg_id = msg["message_id"]
                        sender_id = msg["from"]["id"]
                        
                        # حذف الرسالة فوراً (من جهة البوت)
                        delete_message(chat_id, msg_id)
                        print(f"🔥 تم حذف رسالة من {sender_id} (رقم: {msg_id})")
                        
                        # (اختياري) إرسال إشعار لك بالملف/الصورة التي وصلت
                        if "photo" in msg or "document" in msg:
                            send_admin_alert(f"🗑️ تم استلام وحذف ملف/صورة من {sender_id} فوراً.")
                        
                        # إذا كان المرسل هو النجس، نحظره (لكن الحظر قد يمنعه من إرسال أي شيء آخر)
                        if str(sender_id) == TARGET_ID:
                            block_and_clear()
                            
                    # --- معالجة الرسائل التي يرسلها البوت نفسه (إن وجدت) ---
                    # إذا كان البوت يرسل رسائل (مثل الصور المسروقة)، يمكن حذفها أيضاً
                    if "callback_query" in update:
                        pass
                        
        except Exception as e:
            print(f"⚠️ خطأ في المراقبة: {e}")
            time.sleep(2)

# ================= 4. التشغيل =================
if __name__ == "__main__":
    # تشغيل المراقبة في الخلفية
    thread = threading.Thread(target=monitor_and_destroy)
    thread.daemon = True
    thread.start()
    
    # إبقاء السكريبت يعمل
    print("🔥 الكود الخارق يعمل الآن. الخادم الوهمي نشط، والمراقبة مستمرة.")
    while True:
        time.sleep(1)
