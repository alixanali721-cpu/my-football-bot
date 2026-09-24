import os
import requests
from flask import Flask
from threading import Thread
import sqlite3

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot status: ACTIVE (Adaptive AI & Odds Tracker)"

def init_db():
    conn = sqlite3.connect('bot_memory.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_name TEXT,
            predicted_pick TEXT,
            initial_odds REAL,
            current_odds REAL,
            status TEXT DEFAULT 'PENDING'
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def analyze_odds_movement(initial_odds, current_odds):
    if initial_odds <= 0:
        return "STABLE", 0.0
    
    change_percent = ((current_odds - initial_odds) / initial_odds) * 100
    
    if change_percent <= -5.0:
        return "DROPPING_ODDS (Katta bosim/Value)", change_percent
    elif change_percent >= 5.0:
        return "RISING_ODDS (Xavf yuqori)", change_percent
    else:
        return "STABLE", change_percent

def generate_ai_signal(match, team1_score, team2_score, init_g1_odds, curr_g1_odds, xg1, xg2):
    trend, percent = analyze_odds_movement(init_g1_odds, curr_g1_odds)
    base_prob = (xg1 / (xg1 + xg2 + 0.01)) * 100
    
    if "DROPPING" in trend:
        adjusted_prob = min(base_prob + 8, 95)
    elif "RISING" in trend:
        adjusted_prob = max(base_prob - 8, 5)
    else:
        adjusted_prob = base_prob

    risk = "PAST RISK 🟢" if adjusted_prob > 65 else ("O'RTA RISK ⚠️" if adjusted_prob > 45 else "YUQORI RISK 🔴")
    
    text = (
        f"🧠 **AI ADAPTIV & KOEFFITSIENT TAHLILI**\n\n"
        f"⚽ **O'yin:** {match}\n"
        f"📊 **Hisob:** ({team1_score}) vs ({team2_score})\n"
        f"📉 **Koeffitsient dinamikasi:** {trend} ({percent:.1f}%)\n"
        f"📈 **Moslashtirilgan g'alaba ehtimoli:** {adjusted_prob:.1f}%\n"
        f"🔥 **Holat:** {risk}\n\n"
        f"💎 **1xBET UCHUN OPTIMAL TAVSIYA:**\n"
        f"• Asosiy tikish: G'1 yoki 1X\n"
        f"• Total: Total 1.5 Ko'p\n"
    )
    return text

BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
CHAT_ID = "YOUR_CHAT_ID_HERE"

def send_telegram_msg(message):
    if BOT_TOKEN != "YOUR_BOT_TOKEN_HERE":
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload)
        except Exception as e:
            print("Xatolik:", e)

def run_flask():
    app.run(host='0.0.0.0', port=8080)

if __name__ == '__main__':
    Thread(target=run_flask).start()
    print("Flask Server Yuritildi!")
    
