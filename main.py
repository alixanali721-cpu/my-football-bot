import urllib.request
import json
import time
import math
import threading
from datetime import datetime
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot 24/7 faol!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

TELEGRAM_BOT_TOKEN = "8844618317:AAFIIsOaV8y07lUSilh9g_hlJPQVIWqldfE"
TELEGRAM_CHAT_ID = "6137041154"
RAPIDAPI_KEY = "488d9e228amshfa1a16902d4b80fp149eaejsn2c2db788041c"
RAPIDAPI_HOST = "sportapi7.p.rapidapi.com"

def send_telegram_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    req = urllib.request.Request(
        url, 
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req) as response:
            return True
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        return False

def get_menu_keyboard():
    return {
        "keyboard": [
            [{"text": "⚽ LIVE Tahlil & Odds"}, {"text": "📊 Statistika"}],
            [{"text": "ℹ️ Yordam"}]
        ],
        "resize_keyboard": True
    }

def analyze_live_events_with_odds(manual_request=False, chat_id=None):
    target_chat = chat_id if chat_id else TELEGRAM_CHAT_ID
    url = f"https://{RAPIDAPI_HOST}/api/v1/sport/football/events/live"
    req = urllib.request.Request(url, headers={
        'x-rapidapi-host': RAPIDAPI_HOST,
        'x-rapidapi-key': RAPIDAPI_KEY
    })
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            events = data.get('events', [])
            if not events:
                send_telegram_message(target_chat, "⚠️ LIVE o'yinlar topilmadi.")
                return

            sent_count = 0
            for event in events:
                home_team = event.get('homeTeam', {}).get('name', '1-Jamoa')
                away_team = event.get('awayTeam', {}).get('name', '2-Jamoa')
                home_score = event.get('homeScore', {}).get('current', 0)
                away_score = event.get('awayScore', {}).get('current', 0)
                
                home_exp_xg = round(1.2 + (home_score * 0.4), 2)
                away_exp_xg = round(0.8 + (away_score * 0.3), 2)
                win_prob = round((home_exp_xg / (home_exp_xg + away_exp_xg)) * 100)
                total_goals = round(home_exp_xg + away_exp_xg, 1)
                
                est_odds_1 = round(100 / win_prob, 2) if win_prob > 0 else 2.0
                value_bet_status = "💎 YUQORI (Value Bet)" if win_prob >= 65 else "⚠️ O'RTA RISK"

                if win_prob >= 55 or manual_request:
                    msg = (
                        f"🎯 <b>AI LIVE & KOEFFITSIENT TAHLILI</b>\n\n"
                        f"⚽ <b>O'yin:</b> {home_team} ({home_score}) vs ({away_score}) {away_team}\n\n"
                        f"📈 <b>G'alaba ehtimoli:</b> <b>{win_prob}%</b>\n"
                        f"📊 <b>Min. Koeffitsient:</b> <b>{est_odds_1}</b>\n"
                        f"🔥 <b>Holat:</b> <b>{value_bet_status}</b>\n\n"
                        f"💎 <b>1XBET UCHUN TAVSIYA:</b>\n"
                        f"• <b>Asosiy tikish:</b> G'1 ({home_team}) yoki 1X\n"
                        f"• <b>Total:</b> Total {1.5 if total_goals > 1.8 else 2.5} Ko'p\n"
                        f"• <b>Taxminiy hisob:</b> {math.floor(home_exp_xg)} : {math.floor(away_exp_xg)}"
                    )
                    send_telegram_message(target_chat, msg)
                    sent_count += 1
                    time.sleep(2)
                    if sent_count >= 3:
                        break
    except Exception as e:
        print(f"❌ Xatolik: {e}")

def check_telegram_updates():
    last_update_id = 0
    while True:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=10"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                for update in data.get('result', []):
                    last_update_id = update['update_id']
                    message = update.get('message', {})
                    text = message.get('text', '')
                    chat_id = message.get('chat', {}).get('id')

                    if not text or not chat_id:
                        continue

                    if text in ['/start', 'start']:
                        welcome_msg = "👋 Hush kelibsiz! Quyidagi tugmalardan birini tanlang:"
                        send_telegram_message(chat_id, welcome_msg, get_menu_keyboard())

                    elif text in ['⚽ LIVE Tahlil & Odds', '/live']:
                        send_telegram_message(chat_id, "🔍 Tahlil qilinmoqda...")
                        analyze_live_events_with_odds(manual_request=True, chat_id=chat_id)

                    elif text in ['📊 Statistika', '/stat']:
                        stat_msg = "📊 Bot va Flask Server 24/7 faol."
                        send_telegram_message(chat_id, stat_msg, get_menu_keyboard())

                    elif text in ['ℹ️ Yordam', '/help']:
                        help_msg = "ℹ️ Bot avtomatik va qo'lda LIVE tahlil beradi."
                        send_telegram_message(chat_id, help_msg, get_menu_keyboard())
        except Exception as e:
            time.sleep(3)

if __name__ == "__main__":
    server_thread = threading.Thread(target=run_flask)
    server_thread.daemon = True
    server_thread.start()
    
    print("🚀 Bot ishga tushdi...")
    check_telegram_updates()
                  
