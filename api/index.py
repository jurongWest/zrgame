import os
import random
import asyncio
from fastapi import FastAPI, Request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes
)

DISHES = [
    "Pizza", "Burger", "Sushi", "Pasta",
    "Tacos", "Steak", "Salad", "Ramen",
    "Curry", "Sandwich", "Dumplings", "BBQ",
    "Ice Cream", "Cake", "Fries", "Waffles"
]

# ✅ Vercel-friendly: expose as "app"
app = FastAPI()

# We create PTB app lazily so missing env vars don't crash at import time
ptb_app = None
_init_lock = asyncio.Lock()
_initialized = False

# ---------- Bot handlers ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dishes = DISHES.copy()
    random.shuffle(dishes)

    context.user_data.clear()
    context.user_data["current_round"] = dishes
    context.user_data["next_round"] = []

    await update.effective_chat.send_message("🍽 Tournament started!")
    await send_next_round(update, context)

async def send_next_round(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_round = context.user_data.get("current_round", [])

    if len(current_round) == 1:
        await update.effective_chat.send_message(f"🏆 The winner is: {current_round[0]} 🎉")
        return

    if len(current_round) < 2:
        await update.effective_chat.send_message("Not enough dishes left. Send /start to restart.")
        return

    pair = current_round[:2]
    context.user_data["current_round"] = current_round[2:]

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(pair[0], callback_data=f"pick|{pair[0]}")],
        [InlineKeyboardButton(pair[1], callback_data=f"pick|{pair[1]}")]
    ])

    await update.effective_chat.send_message("Choose your favourite:", reply_markup=keyboard)

async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data or ""
    if not data.startswith("pick|"):
        return

    chosen = data.split("|", 1)[1]
    context.user_data.setdefault("next_round", []).append(chosen)

    if not context.user_data.get("current_round"):
        context.user_data["current_round"] = context.user_data.get("next_round", [])
        context.user_data["next_round"] = []
        await query.message.reply_text("➡️ Next round!")

    await send_next_round(update, context)

# ---------- Init glue ----------

async def ensure_initialized():
    global ptb_app, _initialized

    if _initialized:
        return

    async with _init_lock:
        if _initialized:
            return

        token = os.getenv("TOKEN")
        if not token:
            # Clear message to debug env var issues on Vercel
            raise RuntimeError("TOKEN env var is missing. Set it in Vercel → Settings → Environment Variables.")

        ptb_app = Application.builder().token(token).build()
        ptb_app.add_handler(CommandHandler("start", start))
        ptb_app.add_handler(CallbackQueryHandler(handle_choice))

        await ptb_app.initialize()
        _initialized = True

# ---------- Routes ----------

@app.get("/")
async def health():
    return {"ok": True, "message": "Telegram bot endpoint is up"}

@app.post("/webhook")
async def webhook(req: Request):
    print("🔥 Webhook HIT")   # <--- add this
    await ensure_initialized()
    data = await req.json()
    update = Update.de_json(data, ptb_app.bot)
    await ptb_app.process_update(update)
    return {"ok": True}

