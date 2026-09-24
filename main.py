import os
import requests
import sqlite3
from flask import Flask
from threading import Thread
import telebot

# --- FLASK SERVER (Render doimiy ishlashi uchun) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot status: ACTIVE (Adaptive AI & Odds Tracker)"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# --- BAZANI SOZLASH ---
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

# --- AI ALGORITMI VA TAHLIL ---
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

def generate_ai_signal(match="10 de Noviembre Wilstermann Cooperativas vs Real Cotagaita", team1_score=0, team2_score=0, init_g1_odds=1.85, curr_g1_odds=1.67, xg1=1.4, xg2=0.6):
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
        f"🎯 **AI LIVE & KOEFFITSIENT TAHLILI**\n\n"
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

# --- TELEGRAM BOT QISMI ---
TOKEN = "8844618317:AAHIf8YAuHNl3IBl-hPnDJP0h1Jx-Fzy1LA"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'live'])
def send_analysis(message):
    analysis_text = generate_ai_signal()
    bot.reply_to(message, analysis_text, parse_mode="Markdown")

if __name__ == '__main__':
    Thread(target=run_flask).start()
    print("Flask Server yuritildi!")
    bot.infinity_polling()
    
