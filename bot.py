import os
import telebot
import sqlite3
from flask import Flask, request

BOT_TOKEN = os.environ.get("8254192215:AAH4XEccldCQ49VyJh_Wzg0q7M1bf4AmKrc")
DB_PATH = "data.db"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
server = Flask(__name__)

def search_in_db(value):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    results = []
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cur.fetchall()]
    for table in tables:
        try:
            cur.execute(f"PRAGMA table_info({table})")
            cols = [c[1] for c in cur.fetchall()]
            for col in cols:
                query = f"SELECT * FROM {table} WHERE {col} LIKE ? LIMIT 5"
                cur.execute(query, (f"%{value}%",))
                rows = cur.fetchall()
                if rows:
                    results.append((table, cols, col, rows))
        except:
            continue
    conn.close()
    return results

def format_result(table, cols, search_col, rows):
    text = f"🗄 <b>{table}</b> — поиск по полю <b>{search_col}</b>\n\n"
    for row in rows:
        block = []
        for i, val in enumerate(row):
            if not val:
                continue
            col_name = cols[i] if i < len(cols) else f"col{i+1}"
            block.append(f"<b>{col_name}:</b> {val}")
        text += " • " + "<br>   ".join(block) + "\n\n"
    return text

@bot.message_handler(commands=["start"])
def start(msg):
    bot.reply_to(msg, "🔎 Отправь мне ФИО, номер или почту — я поищу в базе данных.")

@bot.message_handler(func=lambda m: True)
def search(msg):
    text = msg.text.strip()
    results = search_in_db(text)
    if not results:
        bot.reply_to(msg, "❌ Ничего не найдено.")
        return
    reply = "📂 <b>Найдено:</b>\n\n"
    for table, cols, col, rows in results:
        reply += format_result(table, cols, col, rows)
    bot.reply_to(msg, reply, parse_mode="HTML")

# --- Flask webhook ---
@server.route("/" + BOT_TOKEN, methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@server.route("/")
def index():
    return "Bot is running!"

if __name__ == "__main__":
    url = os.environ.get("RAILWAY_URL")
    bot.remove_webhook()
    bot.set_webhook(url=url + "/" + BOT_TOKEN)
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

