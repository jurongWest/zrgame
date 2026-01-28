import os
import random
import asyncio
from typing import Final

from fastapi import FastAPI, Request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes
)

TOKEN: Final = os.environ["TOKEN"]  # set in Vercel env vars

DISHES = [
    "Pizza", "Burger", "Sushi", "Pasta",
    "Tacos", "Steak", "Salad", "Ramen",
    "Curry", "Sandwich", "Dumplings", "BBQ",
    "Ice Cream", "Cake", "Fries", "Waffles"
]

# ---------- Your handlers (same idea as your VS Code version) ----------

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

# ---------- FastAPI + Telegram webhook glue ----------

fastapi_app = FastAPI()

ptb_app = Application.builder().token(TOKEN).build()
ptb_app.add_handler(CommandHandler("start", start))
ptb_app.add_handler(CallbackQueryHandler(handle_choice))

_init_lock = asyncio.Lock()
_initialized = False

async def ensure_initialized():
    global _initialized
    if _initialized:
        return
    async with _init_lock:
        if _initialized:
            return
        await ptb_app.initialize()
        _initialized = True

@fastapi_app.get("/")
async def health():
    return {"ok": True, "message": "Telegram bot is running"}

@fastapi_app.post("/webhook")
async def webhook(req: Request):
    await ensure_initialized()
    data = await req.json()

    update = Update.de_json(data, ptb_app.bot)
    await ptb_app.process_update(update)

    return {"ok": True}
