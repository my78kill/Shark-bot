import sys
import types

# Fix for Python 3.13+ (imghdr removed)
imghdr = types.ModuleType("imghdr")
sys.modules["imghdr"] = imghdr


import random
import os
from collections import defaultdict
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

TOKEN = os.getenv("BOT_TOKEN")

games = {}
leader_queue = defaultdict(list)
ranking = defaultdict(lambda: defaultdict(int))

def load_words():
    with open("words.txt") as f:
        return [w.strip().lower() for w in f.readlines()]

words = load_words()

def start(update, context):

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

    update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

def help_cmd(update, context):

    update.message.reply_text("""
🦈❔ Shark Game commands:

🎮 /game - start new game
🛑 /stop - stop current game
🪧 /rules - know game rules
❔ /help - show this message
📊 /ranking - top 25 players
""")

def rules(update, context):

    update.message.reply_text("""
🪧🦈 Game Rules:

🔤 Word Guess

There are two roles: leader and participants.

The leader gets a random secret word and describes it without saying the word.

Participants must guess the word and type it in the group chat.

🏆 The first correct guess becomes the next leader.
""")

def game(update, context):

    chat = update.message.chat_id

    if chat in games:
        update.message.reply_text("Game already running!")
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

    msg = update.message.reply_text(
        f"🦈 Shark Game\n\n🎤 {user.first_name} is explaining the word!",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    games[chat]["msg"] = msg.message_id

def buttons(update, context):

    query = update.callback_query
    query.answer()

    chat = query.message.chat_id
    user = query.from_user

    if chat not in games:
        return

    game = games[chat]

    if query.data == "join":

        if user.id not in leader_queue[chat]:
            leader_queue[chat].append(user.id)
            query.message.reply_text(f"{user.first_name} joined leader queue!")

        return

    if user.id != game["leader"]:
        query.answer("Only leader can use this", show_alert=True)
        return

    if query.data == "see":

        context.bot.edit_message_text(
            chat_id=chat,
            message_id=game["msg"],
            text=f"🦈 Shark Game\n\n🎤 {game['leader_name']} is explaining the word!\n\n🧠 Word: {game['word']}",
            reply_markup=query.message.reply_markup
        )

    elif query.data == "change":

        game["word"] = random.choice(words)

    elif query.data == "drop":

        next_leader(context, chat)

def next_leader(context, chat):

    if not leader_queue[chat]:

        context.bot.send_message(
            chat,
            "No leader in queue. Press 'I want to be a leader'."
        )
        return

    new = leader_queue[chat].pop(0)

    member = context.bot.get_chat_member(chat, new)

    games[chat]["leader"] = new
    games[chat]["leader_name"] = member.user.first_name
    games[chat]["word"] = random.choice(words)

    context.bot.edit_message_text(
        chat_id=chat,
        message_id=games[chat]["msg"],
        text=f"🦈 Shark Game\n\n🎤 {member.user.first_name} is explaining the word!",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("👁 See word", callback_data="see"),
                InlineKeyboardButton("🔄 Change word", callback_data="change")
            ],
            [
                InlineKeyboardButton("🎮 I want to be a leader", callback_data="join"),
                InlineKeyboardButton("❌ Drop lead", callback_data="drop")
            ]
        ])
    )

def guess(update, context):

    chat = update.message.chat_id

    if chat not in games:
        return

    game = games[chat]
    user = update.effective_user

    if user.id == game["leader"]:
        return

    text = update.message.text.lower().strip()

    if text == game["word"]:

        ranking[chat][user.first_name] += 1

        update.message.reply_text(
            f"🎉 Correct!\n\n🏆 {user.first_name} guessed the word!"
        )

        leader_queue[chat].insert(0, user.id)

        next_leader(context, chat)

def ranking_cmd(update, context):

    chat = update.message.chat_id

    if chat not in ranking:
        update.message.reply_text("No ranking yet.")
        return

    top = sorted(ranking[chat].items(), key=lambda x: x[1], reverse=True)[:25]

    text = "📊 Top 25 players:\n\n"

    for i, (name, score) in enumerate(top, 1):
        text += f"{i}. {name} — {score}\n"

    update.message.reply_text(text)

def stop(update, context):

    chat = update.message.chat_id

    if chat in games:
        del games[chat]

    update.message.reply_text("🛑 Game stopped.")

def start_bot():

    updater = Updater(TOKEN)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help_cmd))
    dp.add_handler(CommandHandler("rules", rules))
    dp.add_handler(CommandHandler("game", game))
    dp.add_handler(CommandHandler("stop", stop))
    dp.add_handler(CommandHandler("ranking", ranking_cmd))

    dp.add_handler(CallbackQueryHandler(buttons))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, guess))

    updater.start_polling()
    updater.idle()
