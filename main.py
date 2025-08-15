import json
import time
from telegram import (
    InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton, Update
)
from telegram.ext import (
    ApplicationBuilder, InlineQueryHandler, CallbackQueryHandler, CommandHandler, ContextTypes
)
from uuid import uuid4

TOKEN = "8341947370:AAHN0Yo4shU8QIKmW9JgR7TDTK9-ToHLsKI"
AUTHOR_USERNAME = "@jvmvr"
UPDATE_CHANNEL = "@jvmvr"
BALANCES_FILE = "balances.json"

START_BALANCE_NEW = 250
DAILY_BONUS = 150
DAILY_COOLDOWN = 86400  # 24 hours

# Load balances
try:
    with open(BALANCES_FILE, "r") as f:
        balances = json.load(f)
except FileNotFoundError:
    balances = {}

# Bets in memory
active_bets = {}

def save_balances():
    with open(BALANCES_FILE, "w") as f:
        json.dump(balances, f)

def get_balance(user_id):
    if str(user_id) not in balances:
        balances[str(user_id)] = {"balance": START_BALANCE_NEW, "last_collect": 0, "name": ""}
        save_balances()
    return balances[str(user_id)]["balance"]

def set_balance(user_id, amount):
    balances[str(user_id)]["balance"] = amount
    save_balances()

def update_name(user_id, name):
    if str(user_id) in balances:
        balances[str(user_id)]["name"] = name
    else:
        balances[str(user_id)] = {"balance": START_BALANCE_NEW, "last_collect": 0, "name": name}
    save_balances()

def collect_daily(user_id):
    user = balances.get(str(user_id), {"balance": START_BALANCE_NEW, "last_collect": 0})
    now = time.time()
    if now - user["last_collect"] >= DAILY_COOLDOWN:
        bonus = DAILY_BONUS if user["last_collect"] != 0 else START_BALANCE_NEW
        user["balance"] += bonus
        user["last_collect"] = now
        balances[str(user_id)] = user
        save_balances()
        return f"You collected ${bonus}! Your new balance is ${user['balance']}."
    else:
        remaining = DAILY_COOLDOWN - (now - user["last_collect"])
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        return f"⏳ You can collect again in {hours}h {minutes}m."

async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()
    user_id = update.inline_query.from_user.id
    name = update.inline_query.from_user.first_name
    update_name(user_id, name)

    results = []

    if query == "":
        # Menu
        results.append(InlineQueryResultArticle(
            id=str(uuid4()),
            title="🎁 Collect Daily",
            input_message_content=InputTextMessageContent(collect_daily(user_id))
        ))
        results.append(InlineQueryResultArticle(
            id=str(uuid4()),
            title="💰 Check Balance",
            input_message_content=InputTextMessageContent(f"Your balance: ${get_balance(user_id)}")
        ))
        results.append(InlineQueryResultArticle(
            id=str(uuid4()),
            title="📊 Leaderboard",
            input_message_content=InputTextMessageContent(get_leaderboard(0)),
            reply_markup=leaderboard_keyboard(0)
        ))
        for amt in [50, 100, 200]:
            results.append(InlineQueryResultArticle(
                id=str(uuid4()),
                title=f"🎲 Bet ${amt}",
                input_message_content=InputTextMessageContent(place_bet(user_id, name, amt)),
                reply_markup=bet_keyboard(user_id, amt)
            ))
    else:
        # Custom bet
        try:
            amt = int(query)
            results.append(InlineQueryResultArticle(
                id=str(uuid4()),
                title=f"🎲 Bet ${amt}",
                input_message_content=InputTextMessageContent(place_bet(user_id, name, amt)),
                reply_markup=bet_keyboard(user_id, amt)
            ))
        except:
            pass

    await update.inline_query.answer(results, cache_time=0)

def place_bet(user_id, name, amount):
    balance = get_balance(user_id)
    if balance < amount:
        return f"❌ {name}, you don't have enough balance to bet ${amount}."
    set_balance(user_id, balance - amount)
    bet_id = str(uuid4())
    active_bets[bet_id] = {"amount": amount, "user_id": user_id, "name": name}
    return f"{name} placed a ${amount} bet"

def bet_keyboard(user_id, amount):
    bet_id = str(uuid4())
    active_bets[bet_id] = {"amount": amount, "user_id": user_id}
    return InlineKeyboardMarkup([[InlineKeyboardButton("Raise", callback_data=f"raise|{bet_id}")]])

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    name = query.from_user.first_name
    data = query.data.split("|")

    if data[0] == "raise":
        bet_id = data[1]
        if bet_id not in active_bets:
            await query.answer("Bet not found", show_alert=True)
            return
        bet = active_bets[bet_id]
        amt = bet["amount"]
        balance = get_balance(user_id)
        if balance < amt:
            await query.answer("You don't have enough balance to raise!", show_alert=True)
        else:
            set_balance(user_id, balance - amt)
            await query.answer(f"You raised ${amt}!", show_alert=True)

def get_leaderboard(page):
    sorted_players = sorted(balances.items(), key=lambda x: x[1]["balance"], reverse=True)
    start = page * 15
    end = start + 15
    text = "🏆 Leaderboard 🏆\n\n"
    for i, (uid, data) in enumerate(sorted_players[start:end], start=start + 1):
        text += f"{i}. {data['name']} — ${data['balance']}\n"
    return text

def leaderboard_keyboard(page):
    return InlineKeyboardMarkup([[InlineKeyboardButton("Next ▶", callback_data=f"lb|{page+1}")]])

async def leaderboard_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data.split("|")
    page = int(data[1])
    await query.edit_message_text(get_leaderboard(page), reply_markup=leaderboard_keyboard(page))

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(InlineQueryHandler(inline_query))
    app.add_handler(CallbackQueryHandler(button_click, pattern="^raise"))
    app.add_handler(CallbackQueryHandler(leaderboard_page, pattern="^lb"))
    print("Bot is running...")
    app.run_polling()
