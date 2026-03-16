import os
import random
from collections import defaultdict

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = os.getenv("BOT_TOKEN")

games = {}
leader_queue = defaultdict(list)
ranking = defaultdict(lambda: defaultdict(int))


def load_words():
    with open("words.txt") as f:
        return [w.strip().lower() for w in f.readlines()]


words = load_words()


# START

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    name = update.effective_user.first_name
    bot = context.bot.username

    keyboard = [[
        InlineKeyboardButton(
            "➕ Add me to group",
            url=f"https://t.me/{bot}?startgroup=true"
        )
    ]]

    text = f"""
👋🏻 Hey {name}!

🦈🇮🇳 Shark Game Bot offers an exciting game for your group chats:

🔤 Word Guess — One player explains the secret word, others guess it.

👉🏻 Add me to your group and start playing now with your friends!

Press /help to see the list of all commands.
"""

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


# HELP

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("""
🦈❔ Shark Game commands:

🎮 /game - start new game
🛑 /stop - stop current game
🪧 /rules - know game rules
❔ /help - show this message
📊 /ranking - top 25 players
""")


# RULES

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("""
🪧🦈 Game Rules:

🔤 Word Guess

There are two roles: leader and participants.

The leader gets a random secret word and describes it without saying the word.

Participants must guess the word and type it in the group chat.

🏆 The first correct guess becomes the next leader.
""")


# GAME START

async def game(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat = update.effective_chat.id

    if chat in games:
        await update.message.reply_text("Game already running!")
        return

    user = update.effective_user
    word = random.choice(words)

    games[chat] = {
        "leader": user.id,
        "leader_name": user.first_name,
        "word": word,
        "msg": None
    }

    keyboard = [
        [
            InlineKeyboardButton("👁 See word", callback_data="see"),
            InlineKeyboardButton("🔄 Change word", callback_data="change")
        ],
        [
            InlineKeyboardButton("🎮 I want to be a leader", callback_data="join"),
            InlineKeyboardButton("❌ Drop lead", callback_data="drop")
        ]
    ]

    msg = await update.message.reply_text(
        f"🦈 Shark Game\n\n🎤 {user.first_name} is explaining the word!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    games[chat]["msg"] = msg.message_id


# BUTTONS

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    chat = query.message.chat.id
    user = query.from_user

    if chat not in games:
        return

    game = games[chat]

    if query.data == "join":

        if user.id not in leader_queue[chat]:
            leader_queue[chat].append(user.id)
            await query.message.reply_text(f"{user.first_name} joined leader queue!")

        return

    if user.id != game["leader"]:
        await query.answer("Only leader can use this", show_alert=True)
        return

    if query.data == "see":

        await context.bot.edit_message_text(
            chat_id=chat,
            message_id=game["msg"],
            text=f"🦈 Shark Game\n\n🎤 {game['leader_name']} is explaining the word!\n\n🧠 Word: {game['word']}",
            reply_markup=query.message.reply_markup
        )

    elif query.data == "change":
        game["word"] = random.choice(words)

    elif query.data == "drop":
        await next_leader(context, chat)


async def next_leader(context, chat):

    if not leader_queue[chat]:
        await context.bot.send_message(chat, "No leader in queue.")
        return

    new = leader_queue[chat].pop(0)

    member = await context.bot.get_chat_member(chat, new)

    games[chat]["leader"] = new
    games[chat]["leader_name"] = member.user.first_name
    games[chat]["word"] = random.choice(words)

    await context.bot.edit_message_text(
        chat_id=chat,
        message_id=games[chat]["msg"],
        text=f"🦈 Shark Game\n\n🎤 {member.user.first_name} is explaining the word!"
    )


# GUESS

async def guess(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat = update.effective_chat.id

    if chat not in games:
        return

    game = games[chat]
    user = update.effective_user

    if user.id == game["leader"]:
        return

    text = update.message.text.lower().strip()

    if text == game["word"]:

        ranking[chat][user.first_name] += 1

        await update.message.reply_text(
            f"🎉 Correct!\n\n🏆 {user.first_name} guessed the word!"
        )

        leader_queue[chat].insert(0, user.id)

        await next_leader(context, chat)


# RANKING

async def ranking_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat = update.effective_chat.id

    if chat not in ranking:
        await update.message.reply_text("No ranking yet.")
        return

    top = sorted(ranking[chat].items(), key=lambda x: x[1], reverse=True)[:25]

    text = "📊 Top 25 players:\n\n"

    for i, (name, score) in enumerate(top, 1):
        text += f"{i}. {name} — {score}\n"

    await update.message.reply_text(text)


# STOP

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):

    chat = update.effective_chat.id

    if chat in games:
        del games[chat]

    await update.message.reply_text("🛑 Game stopped.")


def start_bot():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("rules", rules))
    app.add_handler(CommandHandler("game", game))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("ranking", ranking_cmd))

    app.add_handler(CallbackQueryHandler(buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, guess))

    app.run_polling(stop_signals=None)
