import os
import telebot
from flask import Flask
from threading import Thread
import sqlite3
from datetime import datetime

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID', 0))
bot = telebot.TeleBot(TOKEN)
app = Flask('')

def setup_db():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS messages (sender_id INTEGER, receiver_id INTEGER, text TEXT, time TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS banned (user_id INTEGER PRIMARY KEY)''')
    conn.commit()
    conn.close()

setup_db()

users = {}
active_chats = {}

@app.route('/alive')
def alive():
    return "alive", 200

def run():
    app.run(host='0.0.0.0', port=8080)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "👋 Anonim chat. /search yaz.")

@bot.message_handler(commands=['search'])
def search(message):
    if message.chat.id in active_chats: return bot.send_message(message.chat.id, "Artıq söhbətdəsiniz.")
    users[message.chat.id] = True
    bot.send_message(message.chat.id, "🔍 Axtarılır...")
    for uid in list(users.keys()):
        if uid != message.chat.id:
            active_chats[message.chat.id] = uid
            active_chats[uid] = message.chat.id
            del users[message.chat.id]
            del users[uid]
            bot.send_message(message.chat.id, "✅ Tapıldı! /stop ilə çıx.")
            bot.send_message(uid, "✅ Tapıldı! /stop ilə çıx.")
            return

@bot.message_handler(commands=['stop'])
def stop(message):
    if message.chat.id in active_chats:
        p = active_chats[message.chat.id]
        del active_chats[message.chat.id]
        del active_chats[p]
        bot.send_message(message.chat.id, "Bitdi.")
        bot.send_message(p, "Tərəf çıxdı.")

@bot.message_handler(commands=['stats', 'active', 'logs'])
def admin(message):
    if message.chat.id != ADMIN_ID: return
    if message.text.startswith('/stats'):
        bot.send_message(ADMIN_ID, f"Aktiv: {len(active_chats)//2} | Növbə: {len(users)}")
    elif message.text.startswith('/active'):
        bot.send_message(ADMIN_ID, "Aktivlər:\n" + "\n".join([f"{k} ↔ {v}" for k,v in active_chats.items() if k < v]))
    elif message.text.startswith('/logs'):
        conn = sqlite3.connect('bot_data.db')
        logs = conn.execute("SELECT * FROM messages ORDER BY time DESC").fetchall()
        res = "Bütün mesajlar:\n" + "\n".join([f"{l[0]}→{l[1]}: {l[2]}" for l in logs[:50]])
        bot.send_message(ADMIN_ID, res or "Boşdur")

@bot.message_handler(func=lambda m: True)
def relay(message):
    if message.chat.id in active_chats:
        p = active_chats[message.chat.id]
        bot.send_message(p, message.text)
        # Adminə də göndər
        try:
            bot.send_message(ADMIN_ID, f"💬 {message.chat.id} → {p}: {message.text}")
        except: pass

Thread(target=run).start()
bot.infinity_polling()
