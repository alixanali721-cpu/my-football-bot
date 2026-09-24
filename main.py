import os
import requests
import sqlite3
from datetime import datetime
import pytz
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

def predict_exact_score(xg1, xg2):
    score1 = round(xg1)
    score2 = round(xg2)
    return f"{score1}:{score2}"

def get_current_time_str():
    tz = pytz.timezone('Asia/Tashkent')
    now = datetime.now(tz)
    return now.strftime("%d.%m.%Y | %H:%M")

def generate_ai_signal(match="10 de Noviembre vs Real Cotagaita", team1_score=0, team2_score=0, init_g1_odds=1.85, curr_g1_odds=1.67, xg1=1.4, xg2=0.6, match_time=None):
    trend, percent = analyze_odds_movement(init_g1_odds, curr_g1_odds)
    base_prob = (xg1 / (xg1 + xg2 + 0.01)) * 100
    
    if "DROPPING" in trend:
        adjusted_prob = min(base_prob + 8, 95)
    elif "RISING" in trend:
        adjusted_prob = max(base_prob - 8, 5)
    else:
        adjusted_prob = base_prob

    risk = "PAST RISK 🟢" if adjusted_prob > 65 else ("O'RTA RISK ⚠️" if adjusted_prob > 45 else "YUQORI RISK 🔴")
    
    total_goals = xg1 + xg2
    total_recommendation = "Total 2.5 Ko'p" if total_goals > 2.2 else "Total 2.5 Kam"
    fora_recommendation = "Fora 1 (0)" if adjusted_prob > 60 else "Fora 1 (+1)"
    exact_score = predict_exact_score(xg1, xg2)
    
    time_display = match_time if match_time else get_current_time_str()

    text = (
        f"🎯 <b>AI LIVE & FULL MATCH TAHLILI</b>\n\n"
        f"⚽ <b>O'yin:</b> {match}\n"
        f"📅 <b>Sana/Vaqt:</b> {time_display} (GMT+5)\n"
        f"📊 <b>Hisob:</b> ({team1_score}) vs ({team2_score})\n"
        f"📉 <b>Koeffitsient dinamikasi:</b> {trend} ({percent:.1f}%)\n"
        f"📈 <b>G'alaba ehtimoli:</b> {adjusted_prob:.1f}%\n"
        f"🔥 <b>Holat:</b> {risk}\n\n"
        f"💎 <b>1xBET UCHUN TO'LIQ TAVSIYA:</b>\n"
        f"• <b>G'alaba (1X2):</b> G'1 yoki 1X\n"
        f"• <b>Total:</b> {total_recommendation}\n"
        f"• <b>Fora:</b> {fora_recommendation}\n"
        f"🎲 <b>Ehtimoliy aniq hisob:</b> {exact_score}\n"
    )
    return text

# --- TELEGRAM BOT QISMI ---
TOKEN = "8844618317:AAHIf8YAuHNl3IBl-hPnDJP0h1Jx-Fzy1LA"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'live'])
def send_analysis(message):
    analysis_text = generate_ai_signal()
    bot.reply_to(message, analysis_text, parse_mode="HTML")

@bot.message_handler(commands=['help'])
def send_help(message):
    help_text = (
        "🤖 <b>AI Football Bot Yordam Menyusi</b>\n\n"
        "<b>Buyruqlar:</b>\n"
        "• /live - Hozirgi jonli AI tahlilini olish\n"
        "• /stat - Tizim statistikasi va saqlangan ma'lumotlar\n"
        "• /help - Botdan foydalanish bo'yicha yo'riqnoma\n\n"
        "💡 <b>O'zingiz tahlil qilish uchun kiritish formati:</b>\n"
        "<code>Jamoalar bosh_kef joriy_kef xg1 xg2</code>\n"
        "<i>Misol: RealMadrid-Barcelona 2.10 1.80 1.8 0.7</i>"
    )
    bot.reply_to(message, help_text, parse_mode="HTML")

@bot.message_handler(commands=['stat'])
def send_stat(message):
    conn = sqlite3.connect('bot_memory.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM predictions")
    count = cursor.fetchone()[0]
    conn.close()
    
    stat_text = (
        "📊 <b>BOT MEMORY STATISTIKASI</b>\n\n"
        f"• Saqlangan bashoratlar soni: <b>{count}</b>\n"
        "• AI Modeli: <b>Adaptive Odds Engine v2</b>\n"
        "• Vaqt zonasi: <b>Asia/Tashkent (GMT+5)</b>\n"
        "• Server holati: <b>Aktiv 🟢</b>"
    )
    bot.reply_to(message, stat_text, parse_mode="HTML")

@bot.message_handler(func=lambda message: True)
def custom_analysis(message):
    try:
        parts = message.text.split()
        if len(parts) >= 5:
            match_name = parts[0]
            init_odds = float(parts[1])
            curr_odds = float(parts[2])
            xg1 = float(parts[3])
            xg2 = float(parts[4])
            
            res = generate_ai_signal(
                match=match_name, 
                init_g1_odds=init_odds, 
                curr_g1_odds=curr_odds, 
                xg1=xg1, 
                xg2=xg2
            )
            bot.reply_to(message, res, parse_mode="HTML")
        else:
            bot.reply_to(message, "Yordam uchun /help buyrug'ini yuboring.")
    except Exception:
        bot.reply_to(message, "Format noto'g'ri kiritildi. /help orqali namunani ko'ring.")

if __name__ == '__main__':
    Thread(target=run_flask).start()
    print("Flask Server yuritildi!")
    bot.infinity_polling()
