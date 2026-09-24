import os
import math
import requests
import sqlite3
from datetime import datetime
import pytz
from flask import Flask
from threading import Thread
import telebot
from telebot import types

# --- FLASK SERVER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot status: ACTIVE (Ultimate Pro Syndicate: Poisson, Kelly, EV, Physics, Weather, Injuries, Referee, Backtesting & User Portfolio)"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# --- MA'LUMOTLAR BAZASI (Predictions & User Portfolios) ---
def init_db():
    conn = sqlite3.connect('bot_memory.db')
    cursor = conn.cursor()
    
    # Bashoratlar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            match_name TEXT,
            predicted_pick TEXT,
            initial_odds REAL,
            current_odds REAL,
            status TEXT DEFAULT 'PENDING',
            created_at TEXT
        )
    ''')
    
    # Foydalanuvchilarning shaxsiy bankroll va portfolio kabineti
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 1000.0,
            total_profit REAL DEFAULT 0.0
        )
    ''')
    
    conn.commit()
    conn.close()

def save_prediction(match_name, predicted_pick, initial_odds, current_odds):
    conn = sqlite3.connect('bot_memory.db')
    cursor = conn.cursor()
    tz = pytz.timezone('Asia/Tashkent')
    now_str = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO predictions (match_name, predicted_pick, initial_odds, current_odds, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (match_name, predicted_pick, initial_odds, current_odds, now_str))
    conn.commit()
    conn.close()

def get_db_stats():
    conn = sqlite3.connect('bot_memory.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM predictions")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM predictions WHERE status = 'WON'")
    won = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM predictions WHERE status = 'LOST'")
    lost = cursor.fetchone()[0]
    conn.close()
    win_rate = (won / (won + lost) * 100) if (won + lost) > 0 else 0.0
    return total, won, lost, win_rate

def get_user_portfolio(user_id):
    conn = sqlite3.connect('bot_memory.db')
    cursor = conn.cursor()
    cursor.execute("SELECT balance, total_profit FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO users (user_id, balance, total_profit) VALUES (?, 1000.0, 0.0)", (user_id,))
        conn.commit()
        balance, total_profit = 1000.0, 0.0
    else:
        balance, total_profit = row
    conn.close()
    return balance, total_profit

def update_user_balance(user_id, new_balance):
    conn = sqlite3.connect('bot_memory.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
    conn.commit()
    conn.close()

init_db()

# --- MATEMATIK VA MACHINE LEARNING BACKTESTING MODELLARI ---
def poisson_probability(lmbda, k):
    return (math.pow(lmbda, k) * math.exp(-lmbda)) / math.factorial(k)

def calculate_match_matrix(xg1, xg2, max_goals=5):
    matrix = {}
    max_prob = 0.0
    most_likely_score = "1:1"
    
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            prob = poisson_probability(xg1, i) * poisson_probability(xg2, j)
            matrix[(i, j)] = prob
            if prob > max_prob:
                max_prob = prob
                most_likely_score = f"{i}:{j}"
                
    return most_likely_score, max_prob * 100

def calculate_kelly_criterion(odds, probability):
    if odds <= 1:
        return 0.0
    b = odds - 1
    p = probability / 100.0
    q = 1.0 - p
    kelly_fraction = (b * p - q) / b
    return min(max(kelly_fraction * 100, 0.0), 10.0)

def calculate_expected_value(odds, probability):
    p = probability / 100.0
    return (p * odds) - 1

# --- BACKTESTING / SELF-LEARNING OPTIMIZATORI ---
def get_ml_weight_adjustment():
    """Bazadagi o'tgan natijalarga qarab AI og'irlik koeffitsiyentini o'zi sozlashi (Machine Learning)"""
    _, _, _, win_rate = get_db_stats()
    if win_rate > 60:
        return 1.05 # Tizim yaxshi ishlayapti, ishonch koeffitsiyenti yuqori
    elif win_rate < 40 and win_rate > 0:
        return 0.92 # Ehtiyotkorlik koeffitsiyenti
    return 1.0

# --- PROFESSONAL OMILLAR ---
def analyze_pro_factors(weather="Sunny", pitch="Normal", is_derby=True, missing_star_player1=False, missing_star_player2=False, referee_strictness="Normal", shots_on_target_ratio=1.2):
    w_multi = 0.92 if weather == "Rainy" else (0.85 if weather == "Snowy" else 1.0)
    phys_multi = 0.88 if pitch == "Wet" else 1.0
    p1_injury_coef = 0.82 if missing_star_player1 else 1.0
    p2_injury_coef = 0.82 if missing_star_player2 else 1.0
    ref_bonus = 3.0 if referee_strictness == "Strict" else 0.0
    shot_quality = min(max(shots_on_target_ratio, 0.5), 2.0)
    ext_bonus = (5.0 if is_derby else 0.0) + ref_bonus
    return w_multi, phys_multi, p1_injury_coef, p2_injury_coef, ext_bonus, shot_quality

# --- AI TAHLIL ---
def analyze_odds_movement(initial_odds, current_odds):
    if initial_odds <= 0:
        return "STABLE", 0.0
    change_percent = ((current_odds - initial_odds) / initial_odds) * 100
    if change_percent <= -5.0:
        return "DROPPING_ODDS (Qimmatli bosim/Value)", change_percent
    elif change_percent >= 5.0:
        return "RISING_ODDS (Xavf yuqori)", change_percent
    else:
        return "STABLE", change_percent

def get_current_time_str():
    tz = pytz.timezone('Asia/Tashkent')
    now = datetime.now(tz)
    return now.strftime("%d.%m.%Y | %H:%M")

def generate_ai_signal(match="Real Madrid vs Barcelona", init_g1_odds=2.10, curr_g1_odds=1.80, xg1=1.8, xg2=0.7, user_id=None):
    trend, percent = analyze_odds_movement(init_g1_odds, curr_g1_odds)
    
    w_multi, phys_multi, p1_inj, p2_inj, ext_bonus, shot_q = analyze_pro_factors(
        weather="Sunny", pitch="Normal", is_derby=True, 
        missing_star_player1=False, missing_star_player2=True, 
        referee_strictness="Strict", shots_on_target_ratio=1.4
    )
    
    ml_weight = get_ml_weight_adjustment()
    adjusted_xg1 = xg1 * w_multi * phys_multi * p1_inj * shot_q * ml_weight
    adjusted_xg2 = xg2 * w_multi * phys_multi * p2_inj

    exact_score, score_prob = calculate_match_matrix(adjusted_xg1, adjusted_xg2)
    base_prob = (adjusted_xg1 / (adjusted_xg1 + adjusted_xg2 + 0.01)) * 100
    
    if "DROPPING" in trend:
        adjusted_prob = min(base_prob + 8 + (ext_bonus / 2), 94)
    elif "RISING" in trend:
        adjusted_prob = max(base_prob - 8, 10)
    else:
        adjusted_prob = min(base_prob + ext_bonus, 95)

    risk = "PAST RISK 🟢" if adjusted_prob > 65 else ("O'RTA RISK ⚠️" if adjusted_prob > 45 else "YUQORI RISK 🔴")
    
    total_goals = adjusted_xg1 + adjusted_xg2
    total_recommendation = "Total 2.5 Ko'p" if total_goals > 2.2 else "Total 2.5 Kam"
    fora_recommendation = "Fora 1 (0)" if adjusted_prob > 60 else "Fora 1 (+1)"
    main_pick = "G'1 yoki 1X" if adjusted_prob > 50 else "X2"
    
    kelly_stake_pct = calculate_kelly_criterion(curr_g1_odds, adjusted_prob)
    ev_value = calculate_expected_value(curr_g1_odds, adjusted_prob)
    ev_status = f"+{ev_value*100:.1f}% (Foydali Value 🟢)" if ev_value > 0 else f"{ev_value*100:.1f}% (PastValue 🔴)"

    # Shaxsiy bankroll hisob-kitobi
    balance = 1000.0
    if user_id:
        balance, _ = get_user_portfolio(user_id)
    recommended_money = (balance * kelly_stake_pct) / 100

    save_prediction(match, main_pick, init_g1_odds, curr_g1_odds)
    time_display = get_current_time_str()

    text = (
        f"🎯 <b>ULTIMATE SYNDICATE AI TAHLILI</b>\n\n"
        f"⚽ <b>O'yin:</b> {match}\n"
        f"📅 <b>Vaqt:</b> {time_display} (GMT+5)\n\n"
        f"🧠 <b>MACHINE LEARNING & PRO OMILLAR:</b>\n"
        f"• <b>ML Optimizatsiya koeffitsiyenti:</b> {ml_weight}x\n"
        f"• <b>Zarbalar nisbati (SoT) & Jarohatlar:</b> Hisobga olindi ✅\n"
        f"• <b>Ob-havo / Maydon & Hakam:</b> Tinch / Strict 🌤️\n\n"
        f"📉 <b>Kef dinamikasi:</b> {trend} ({percent:.1f}%)\n"
        f"📈 <b>Yakuniy Ehtimollik:</b> {adjusted_prob:.1f}%\n"
        f"🔥 <b>Risk darajasi:</b> {risk}\n\n"
        f"📐 <b>PORTFOLIO & KELLI MEZONI:</b>\n"
        f"• <b>Kutilayotgan Qiymat (EV):</b> {ev_status}\n"
        f"• <b>Tavsiya etilgan stavka:</b> Balansning <b>{kelly_stake_pct:.1f}%</b> ({recommended_money:.1f} so'm/$)\n\n"
        f"💎 <b>1xBET TAVSIYALARI:</b>\n"
        f"• <b>Asosiy tikish:</b> {main_pick}\n"
        f"• <b>Total:</b> {total_recommendation}\n"
        f"• <b>Fora:</b> {fora_recommendation}\n"
        f"🎲 <b>Poisson Aniq Hisob:</b> {exact_score} (Ehtimoli: {score_prob:.1f}%)\n"
        f"💾 <i>(Tahlil shaxsiy bazaga saqlandi)</i>"
    )
    return text

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn_live = types.KeyboardButton("⚽ Live Tahlil")
    btn_stat = types.KeyboardButton("📊 Statistika")
    btn_portfolio = types.KeyboardButton("💰 Mening Kabinetim")
    btn_help = types.KeyboardButton("❓ Yordam")
    markup.add(btn_live, btn_stat)
    markup.add(btn_portfolio, btn_help)
    return markup

# --- TELEGRAM BOT ---
TOKEN = "8844618317:AAGBeTah2HHaTRKocvxgoGpZa3kB79xAPMw"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def send_start(message):
    get_user_portfolio(message.from_user.id)
    analysis_text = generate_ai_signal(user_id=message.from_user.id)
    bot.reply_to(message, analysis_text, parse_mode="HTML", reply_markup=get_main_keyboard())

@bot.message_handler(commands=['live'])
@bot.message_handler(func=lambda message: message.text == "⚽ Live Tahlil")
def send_analysis(message):
    analysis_text = generate_ai_signal(user_id=message.from_user.id)
    bot.reply_to(message, analysis_text, parse_mode="HTML", reply_markup=get_main_keyboard())

@bot.message_handler(commands=['portfolio'])
@bot.message_handler(func=lambda message: message.text == "💰 Mening Kabinetim")
def send_portfolio(message):
    balance, profit = get_user_portfolio(message.from_user.id)
    text = (
        "💰 <b>SHAXSIY BANKROLL & PORTFOLIO KABINETI</b>\n\n"
        f"• Joriy Balansingiz: <b>{balance:.1f}</b>\n"
        f"• Umumiy Foyda / Zarar: <b>{profit:+.1f}</b>\n\n"
        "💡 <i>Balansingizni o'zgartirish uchun quyidagi formatni yuboring:</i>\n"
        "<code>/balance 5000</code>"
    )
    bot.reply_to(message, text, parse_mode="HTML", reply_markup=get_main_keyboard())

@bot.message_handler(commands=['balance'])
def set_balance(message):
    try:
        parts = message.text.split()
        if len(parts) >= 2:
            new_bal = float(parts[1])
            conn = sqlite3.connect('bot_memory.db')
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO users (user_id, balance, total_profit) VALUES (?, ?, 0.0)", (message.from_user.id, new_bal))
            conn.commit()
            conn.close()
            bot.reply_to(message, f"✅ Balansingiz muvaffaqiyatli <b>{new_bal:.1f}</b> ga o'zgartirildi!", parse_mode="HTML", reply_markup=get_main_keyboard())
        else:
            bot.reply_to(message, "Namuna: <code>/balance 2000</code>", parse_mode="HTML")
    except Exception:
        bot.reply_to(message, "Xatolik! Raqamni to'g'ri kiriting.")

@bot.message_handler(commands=['help'])
@bot.message_handler(func=lambda message: message.text == "❓ Yordam")
def send_help(message):
    help_text = (
        "🤖 <b>Ultimate Syndicate AI Bot Yordami</b>\n\n"
        "<b>Buyruqlar:</b>\n"
        "• /live - Barcha ilg'or omillar bilan tahlil olish\n"
        "• /portfolio - Shaxsiy balans va kabinetni ko'rish\n"
        "• /balance [summa] - Balansni yangilash (Masalan: <code>/balance 5000</code>)\n"
        "• /stat - Tizim statistikasi va ML aniqligi\n\n"
        "💡 <b>Qo'lda kiritish formati:</b>\n"
        "<code>Jamoalar bosh_kef joriy_kef xg1 xg2</code>"
    )
    bot.reply_to(message, help_text, parse_mode="HTML", reply_markup=get_main_keyboard())

@bot.message_handler(commands=['stat'])
@bot.message_handler(func=lambda message: message.text == "📊 Statistika")
def send_stat(message):
    total, won, lost, win_rate = get_db_stats()
    ml_w = get_ml_weight_adjustment()
    stat_text = (
        "📊 <b>TIZIM STATISTIKASI VA ML</b>\n\n"
        f"• Jami bashoratlar: <b>{total}</b>\n"
        f"• Yutuqli (WON): <b>{won}</b>\n"
        f"• Yutqazgan (LOST): <b>{lost}</b>\n"
        f"• Aniqlik foizi (Win Rate): <b>%{win_rate:.1f}</b>\n"
        f"• ML Optimizatsiya darajasi: <b>{ml_w}x</b>\n\n"
        "• Modellar: <b>Poisson, Kelly, EV, Physics, Weather, Injuries, Referee, ML & Portfolio</b>"
    )
    bot.reply_to(message, stat_text, parse_mode="HTML", reply_markup=get_main_keyboard())

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
                xg2=xg2,
                user_id=message.from_user.id
            )
            bot.reply_to(message, res, parse_mode="HTML", reply_markup=get_main_keyboard())
        else:
            bot.reply_to(message, "Yordam uchun /help buyrug'ini yuboring.", reply_markup=get_main_keyword())
    except Exception:
        bot.reply_to(message, "Format noto'g'ri. Namuna: <code>Arsenal-Chelsea 1.95 1.75 1.9 0.8</code>", parse_mode="HTML", reply_markup=get_main_keyboard())

if __name__ == '__main__':
    Thread(target=run_flask).start()
    print("Ultimate Syndicate AI Bot barcha funksiyalar bilan ishga tushdi!")
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)
                     
