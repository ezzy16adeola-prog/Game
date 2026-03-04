import os
import sqlite3
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =============================
# CONFIG
# =============================

BOT_TOKEN = os.getenv("8708921630:AAHRcD16E0jmskVkjrAu8Wj-Uo256T-Hj2A")
ADMIN_ID = 8317899373

# =============================
# DATABASE SETUP
# =============================

conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    is_pro INTEGER DEFAULT 0,
    pro_expiry TEXT
)
""")
conn.commit()

# =============================
# FUNCTIONS
# =============================

def add_user(user_id):
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()

def activate_pro(user_id):
    expiry = datetime.now() + timedelta(days=30)
    cursor.execute(
        "UPDATE users SET is_pro=1, pro_expiry=? WHERE user_id=?",
        (expiry.isoformat(), user_id),
    )
    conn.commit()

def check_pro(user_id):
    cursor.execute("SELECT is_pro, pro_expiry FROM users WHERE user_id=?", (user_id,))
    data = cursor.fetchone()

    if not data:
        return False

    is_pro, expiry = data

    if is_pro == 1 and expiry:
        if datetime.fromisoformat(expiry) > datetime.now():
            return True
        else:
            cursor.execute("UPDATE users SET is_pro=0 WHERE user_id=?", (user_id,))
            conn.commit()
            return False

    return False

# =============================
# COMMANDS
# =============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)

    await update.message.reply_text(
        "👋 Welcome to CV Bot!\n\n"
        "Use /pro to upgrade to PRO.\n"
        "Send payment proof (screenshot) after payment."
    )

async def pro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💎 PRO PLAN - ₦1500\n\n"
        "Send payment to:\n"
        "Bank: Your Bank\n"
        "Account: 0000000000\n\n"
        "After payment, send screenshot here."
    )

# =============================
# PAYMENT PROOF HANDLER
# =============================

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    await update.message.reply_text(
        "✅ Payment proof received.\nWaiting for admin approval..."
    )

    # Forward to admin
    await context.bot.forward_message(
        chat_id=ADMIN_ID,
        from_chat_id=update.effective_chat.id,
        message_id=update.message.message_id
    )

# =============================
# ADMIN APPROVAL
# =============================

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Usage: /approve user_id")
        return

    user_id = int(context.args[0])
    activate_pro(user_id)

    await update.message.reply_text(f"✅ User {user_id} upgraded to PRO.")

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text="🎉 Your PRO has been activated for 30 days!"
        )
    except:
        pass

# =============================
# MAIN
# =============================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pro", pro))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()