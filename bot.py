"""
Simple Starter Telegram Bot
============================

Setup:
1. Install the library:
   pip install python-telegram-bot --break-system-packages

2. Create a bot on Telegram:
   - Telegram app kholo, search karo "BotFather"
   - Usse /newbot command bhejo
   - Bot ka naam aur username set karo
   - BotFather aapko ek API TOKEN dega — usse copy karke neeche BOT_TOKEN mein daalo

3. Run karo:
   python telegram_bot.py
"""

import os
import json
import logging
from datetime import datetime, time as dtime
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ---- Bot ka username (group welcome button ke liye) ----
BOT_USERNAME = "One_gotask_bot"

# ---- Permanent (persistent) keyboard buttons ----
MAIN_MENU = [
    ["📩 SMS Task", "💬 WhatsApp Task"],
    ["🎁 Referral", "🆘 Help Center"],
    ["📢 Channel", "🎧 Customer Service"],
    ["📝 Report Problem"],
]
MAIN_MENU_MARKUP = ReplyKeyboardMarkup(
    MAIN_MENU,
    resize_keyboard=True,   # buttons ko screen ke hisaab se chhota rakhta hai
    is_persistent=True,     # keyboard hamesha screen par dikhta rahega
)

# ---- Admin settings ----
# Apni Telegram User ID yahan daalo (bot ko /myid bhej kar pata karo)
ADMIN_ID = 7330058637

# Task videos ke file_id yahan save honge (khud-ba-khud, Telegram se)
SMS_VIDEO_ID_FILE = "sms_video_id.txt"
WHATSAPP_VIDEO_ID_FILE = "whatsapp_video_id.txt"


def get_video_id(file_path):
    """Saved file_id ko file se padhta hai"""
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            return f.read().strip()
    return None


def save_video_id(file_path, file_id: str):
    """file_id ko file mein save karta hai (permanent rehta hai, bot restart hone par bhi)"""
    with open(file_path, "w") as f:
        f.write(file_id)

# ---- Yahan apna BotFather se mila hua token daalo ----
BOT_TOKEN = "8743073709:AAHEPgulzz0kFRk0mHrGcYxRVBTBTimL9eI"

# Logging setup (taaki errors/console mein activity dikhe)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ---- Command Handlers ----

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Jab group mein koi naya member add ho, use welcome karta hai"""
    for new_member in update.message.new_chat_members:
        # Agar bot khud add hua hai, to use skip karo
        if new_member.id == context.bot.id:
            continue

        display_name = f"@{new_member.username}" if new_member.username else new_member.first_name
        await update.message.reply_text(f"{display_name} welcome to 1go.task 🙏🏻")



# ---- User tracking (kitne unique users ne bot use kiya) ----
USERS_FILE = "bot_users.json"


def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_user(user_id: int):
    users = load_users()
    if user_id not in users:
        users.add(user_id)
        with open(USERS_FILE, "w") as f:
            json.dump(list(users), f)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Jab user /start command bhejta hai"""
    save_user(update.effective_user.id)
    await update.message.reply_text(
        "🌟 Hey! Welcome to 1Gotask\n\n"
        "Want to earn ₹200–₹300 daily without any investment? 💰\n\n"
        "📲 Get started:\n"
        "✅ Create your account\n"
        "✅ Complete SMS & WhatsApp tasks\n"
        "💸 Earn ₹13 per 100 SMS\n"
        "🚀 Stay active for more earning opportunities\n\n"
        "⚠️ Note: Registration alone doesn't earn money. You must complete tasks.\n\n"
        "🔗 Register Now:\n"
        "https://1gotask.com/login?mode=register&i=VNAXmPk8\n\n"
        "📢 Join the Official Group:\n"
        "https://t.me/onegotaskcommunicationgroup\n\n"
        "✨ Register & start completing tasks today!",
        reply_markup=MAIN_MENU_MARKUP,
    )


async def userscount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command: total kitne unique users ne bot start kiya hai"""
    if update.effective_user.id != ADMIN_ID:
        return
    users = load_users()
    await update.message.reply_text(f"👥 Total users jinhone bot use kiya: {len(users)}")


async def broadcastvideo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin isse bhejega, uske baad agli video (caption ke saath) sabhi
    users ko broadcast ho jayegi jinhone bot start kiya hai"""
    if update.effective_user.id != ADMIN_ID:
        return
    context.user_data["awaiting_broadcast_video"] = True
    await update.message.reply_text(
        "📹 Ab ek video bhejein (caption ke saath) — wo sabhi users ko broadcast ho jayegi."
    )


async def receive_broadcast_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Jab admin awaiting_broadcast_video state mein video bhejta hai, sabko bhej deta hai"""
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.user_data.get("awaiting_broadcast_video"):
        return  # is state mein nahi hai, receive_video handler isse handle karega

    context.user_data["awaiting_broadcast_video"] = False
    video_file_id = update.message.video.file_id
    caption = update.message.caption or ""

    users = load_users()
    if not users:
        await update.message.reply_text("⚠️ Abhi koi users nahi hain broadcast karne ke liye.")
        return

    await update.message.reply_text(f"🚀 Broadcast shuru ho raha hai... ({len(users)} users)")

    sent = 0
    failed = 0
    for user_id in users:
        try:
            await context.bot.send_video(chat_id=user_id, video=video_file_id, caption=caption)
            sent += 1
        except Exception as e:
            logger.error(f"Broadcast fail user {user_id}: {e}")
            failed += 1

    await update.message.reply_text(
        f"✅ Broadcast complete!\nSuccessfully bheja: {sent}\nFail hua: {failed}"
    )


async def getemojipack(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin command: /getemojipack <pack_shortname>
    Emoji pack ke saare emojis aur unke custom_emoji_id ki list deta hai."""
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: /getemojipack <pack_shortname>\n\n"
            "Example: /getemojipack sti_eebea_by_TgEmojis_bot\n"
            "(Ye naam aapke diye link ke aakhri part se milta hai: "
            "t.me/addemoji/<yahi_naam>)"
        )
        return

    pack_name = context.args[0]
    try:
        sticker_set = await context.bot.get_sticker_set(pack_name)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Pack fetch nahi hua: {e}")
        return

    lines = [f"📦 Pack: {sticker_set.name} ({len(sticker_set.stickers)} emojis)\n"]
    for sticker in sticker_set.stickers:
        emoji_id = sticker.custom_emoji_id
        lines.append(f"{sticker.emoji}  →  {emoji_id}")

    # Telegram message length limit ke hisaab se chunks mein bhejo
    text = "\n".join(lines)
    for i in range(0, len(text), 3500):
        await update.message.reply_text(text[i:i + 3500])


ANNOUNCE_GROUP_FILE = "announce_group_id.txt"


async def groupid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Is command ko group mein bhejein — group ki chat ID save ho jayegi.
    Sirf admin ki request par kaam karega."""
    if update.effective_user.id != ADMIN_ID:
        return
    chat_id = update.effective_chat.id
    with open(ANNOUNCE_GROUP_FILE, "w") as f:
        f.write(str(chat_id))
    await update.message.reply_text(
        f"✅ Is group ki ID save ho gayi: {chat_id}\n"
        f"Ab yahan /announce se message bhej sakte hain."
    )


async def announce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin isse bhejega (kahin se bhi, DM se bhi) — message announcement
    group mein 'Start Bot' button ke saath chala jayega."""
    if update.effective_user.id != ADMIN_ID:
        return

    if not os.path.exists(ANNOUNCE_GROUP_FILE):
        await update.message.reply_text(
            "⚠️ Pehle announcement group set karein: us group mein /groupid bhejein."
        )
        return

    if not context.args:
        await update.message.reply_text("Usage: /announce <message>")
        return

    with open(ANNOUNCE_GROUP_FILE, "r") as f:
        group_id = int(f.read().strip())

    message_text = " ".join(context.args)
    button = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Start Bot", url=f"https://t.me/{BOT_USERNAME}?start=announce")]
    ])

    try:
        await context.bot.send_message(chat_id=group_id, text=message_text, reply_markup=button)
        await update.message.reply_text("✅ Announcement group mein bhej diya gaya!")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Bhejne mein error: {e}")


# ---- Auto-Announcement System ----
ANNOUNCEMENTS_FILE = "announcements.json"
ANNOUNCE_INDEX_FILE = "announcement_index.txt"

# Time windows jinke andar announcements bheji jayengi (24-hour format)
ANNOUNCE_WINDOWS = [
    (dtime(10, 40), dtime(15, 20)),
    (dtime(17, 10), dtime(21, 20)),
]
ANNOUNCE_INTERVAL_SECONDS = 15 * 60  # 15 minute


def load_announcements():
    if os.path.exists(ANNOUNCEMENTS_FILE):
        with open(ANNOUNCEMENTS_FILE, "r") as f:
            return json.load(f)
    return []


def save_announcements(items):
    with open(ANNOUNCEMENTS_FILE, "w") as f:
        json.dump(items, f)


def load_announce_index():
    if os.path.exists(ANNOUNCE_INDEX_FILE):
        with open(ANNOUNCE_INDEX_FILE, "r") as f:
            return int(f.read().strip() or 0)
    return 0


def save_announce_index(i):
    with open(ANNOUNCE_INDEX_FILE, "w") as f:
        f.write(str(i))


async def addannouncement(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin isse bhejega, uske baad agli photo (caption ke saath) announcement list mein add ho jayegi"""
    if update.effective_user.id != ADMIN_ID:
        return
    context.user_data["awaiting_announcement_photo"] = True
    await update.message.reply_text(
        "📸 Ab ek photo bhejein (caption ke saath) — wo announcement list mein add ho jayegi.\n"
        "Jitni chahen utni photos ek-ek karke bhej sakte hain."
    )


async def receive_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Jab admin awaiting_announcement_photo state mein photo bhejta hai, use list mein save karta hai"""
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.user_data.get("awaiting_announcement_photo"):
        return  # is state mein nahi hai, ignore karo

    photo_file_id = update.message.photo[-1].file_id  # sabse badi size wali
    caption = update.message.caption or ""

    items = load_announcements()
    items.append({"photo": photo_file_id, "caption": caption})
    save_announcements(items)

    await update.message.reply_text(
        f"✅ Announcement add ho gaya! Total announcements: {len(items)}\n\n"
        f"Aur add karni hai to photo bhejte rahein, ya /stopadding likhein."
    )


async def stopadding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    context.user_data["awaiting_announcement_photo"] = False
    await update.message.reply_text("✅ Photo add karna band kar diya.")


async def listannouncements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    items = load_announcements()
    if not items:
        await update.message.reply_text("📭 Abhi koi announcement saved nahi hai.")
        return
    lines = [f"📋 Total announcements: {len(items)}\n"]
    for i, item in enumerate(items, 1):
        preview = item["caption"][:40] + ("..." if len(item["caption"]) > 40 else "")
        lines.append(f"{i}. {preview or '(no caption)'}")
    await update.message.reply_text("\n".join(lines))


async def clearannouncements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    save_announcements([])
    save_announce_index(0)
    await update.message.reply_text("🗑️ Saari announcements clear kar di gayi.")


async def send_scheduled_announcement(context: ContextTypes.DEFAULT_TYPE):
    """Har 15 minute mein chalta hai — sirf set time-windows ke andar announcement bhejta hai"""
    now = datetime.now().time()
    in_window = any(start <= now <= end for start, end in ANNOUNCE_WINDOWS)
    if not in_window:
        return

    if not os.path.exists(ANNOUNCE_GROUP_FILE):
        return

    items = load_announcements()
    if not items:
        return

    with open(ANNOUNCE_GROUP_FILE, "r") as f:
        group_id = int(f.read().strip())

    idx = load_announce_index() % len(items)
    item = items[idx]

    button = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Start Bot", url=f"https://t.me/{BOT_USERNAME}?start=announce")]
    ])

    try:
        await context.bot.send_photo(
            chat_id=group_id,
            photo=item["photo"],
            caption=item["caption"],
            reply_markup=button,
        )
    except Exception as e:
        logger.error(f"Announcement bhejne mein error: {e}")

    save_announce_index(idx + 1)


# ---- 30-minute Welcome Reminder (poore din, koi time-window restriction nahi) ----
WELCOME_REMINDER_TEXT = (
    "Welcome everyone! Start using the bot provided to you and begin earning daily. "
    "You can earn around 200–300 every day"
)
WELCOME_REMINDER_INTERVAL_SECONDS = 30 * 60  # 30 minute


async def send_welcome_reminder(context: ContextTypes.DEFAULT_TYPE):
    """Har 30 minute mein group ko ye reminder bhejta hai, sirf set time-windows ke andar"""
    now = datetime.now().time()
    in_window = any(start <= now <= end for start, end in ANNOUNCE_WINDOWS)
    if not in_window:
        return

    if not os.path.exists(ANNOUNCE_GROUP_FILE):
        return

    with open(ANNOUNCE_GROUP_FILE, "r") as f:
        group_id = int(f.read().strip())

    button = InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Start Bot", url=f"https://t.me/{BOT_USERNAME}?start=announce")]
    ])

    try:
        await context.bot.send_message(
            chat_id=group_id,
            text=WELCOME_REMINDER_TEXT,
            reply_markup=button,
        )
    except Exception as e:
        logger.error(f"Welcome reminder bhejne mein error: {e}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Jab user /help command bhejta hai"""
    await update.message.reply_text(
        "📋 Available commands:\n"
        "/start - Bot ko start karo (menu dikhega)\n"
        "/help - Ye help message dekho\n\n"
        "Ya neeche diye buttons use karo.",
        reply_markup=MAIN_MENU_MARKUP,
    )


# ---- Menu button handlers ----

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User ki Telegram ID batata hai"""
    user = update.effective_user
    await update.message.reply_text(f"🆔 Aapki Telegram User ID: {user.id}")


async def setsmsvideo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin isse bhejega, uske baad agli video SMS Task ke liye set hogi"""
    if update.effective_user.id != ADMIN_ID:
        return
    context.user_data["awaiting_video"] = "sms"
    await update.message.reply_text("📩 Ab agli jo video bhejenge, wo SMS Task ke liye set ho jayegi.")


async def setwhatsappvideo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin isse bhejega, uske baad agli video WhatsApp Task ke liye set hogi"""
    if update.effective_user.id != ADMIN_ID:
        return
    context.user_data["awaiting_video"] = "whatsapp"
    await update.message.reply_text("💬 Ab agli jo video bhejenge, wo WhatsApp Task ke liye set ho jayegi.")


async def receive_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Jab admin bot ko video bhejta hai, uska file_id save karta hai (ya broadcast karta hai)"""
    user = update.effective_user
    if user.id != ADMIN_ID:
        return  # sirf admin ki video accept karo

    # Agar broadcast video ka wait ho raha hai, to usी ko handle karo
    if context.user_data.get("awaiting_broadcast_video"):
        await receive_broadcast_video(update, context)
        return

    target = context.user_data.get("awaiting_video")
    file_id = update.message.video.file_id

    if target == "sms":
        save_video_id(SMS_VIDEO_ID_FILE, file_id)
        await update.message.reply_text("✅ SMS Task video set ho gayi!")
    elif target == "whatsapp":
        save_video_id(WHATSAPP_VIDEO_ID_FILE, file_id)
        await update.message.reply_text("✅ WhatsApp Task video set ho gayi!")
    else:
        await update.message.reply_text(
            "⚠️ Pehle batayein ye video kiske liye hai:\n"
            "/setsmsvideo — SMS Task ke liye\n"
            "/setwhatsappvideo — WhatsApp Task ke liye\n"
            "/broadcastvideo — Sabhi users ko bhejne ke liye\n\n"
            "Command bhejne ke baad ye video dobara bhej dein."
        )
        return

    context.user_data["awaiting_video"] = None


async def sms_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption = (
        "📩 SMS Task\n\n"
        "✅ The complete SMS task is explained in the video. "
        "Please watch it carefully before getting started.\n\n"
        "Steps:\n"
        "1️⃣ Download and install the SMS App\n"
        "2️⃣ Copy the invitation code and paste/bind it in the app\n"
        "3️⃣ Click \"I understand\" and wait for a while"
    )
    video_id = get_video_id(SMS_VIDEO_ID_FILE)
    if video_id:
        await update.message.reply_video(video=video_id, caption=caption)
    else:
        await update.message.reply_text(
            caption + "\n\n⚠️ (Abhi tak koi video set nahi hui hai)"
        )


async def whatsapp_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    caption = (
        "💬 WhatsApp Task\n\n"
        "✅ The complete WhatsApp task is explained in the video. "
        "Please watch it carefully before getting started.\n\n"
        "Steps:\n"
        "1️⃣ Download and install the WhatsApp App/tool\n"
        "2️⃣ Copy the invitation code and bind it\n"
        "3️⃣ Log in to WhatsApp and confirm — after that a message will be sent, "
        "wait until the timer ends"
    )
    video_id = get_video_id(WHATSAPP_VIDEO_ID_FILE)
    if video_id:
        await update.message.reply_video(video=video_id, caption=caption)
    else:
        await update.message.reply_text(
            caption + "\n\n⚠️ (Abhi tak koi video set nahi hui hai)"
        )


REFERRAL_LINK = "https://1gotask.com/login?mode=register&i=VNAXmPk8"

REFERRAL_PROMO_TEXT = (
    "☄ Invite Friends to 1GO.TASK and Earn Rewards!\n\n"
    "Invite your friends to 1GO.TASK, have them register using your referral link, "
    "and earn commissions + rewards when they complete tasks. 💝💰\n\n"
    "🩶 REWARD STRUCTURE\n\n"
    "✅ 1st Level Direct Commission – 10%\n"
    "Earn 10% commission on the task earnings of your directly invited users.\n\n"
    "✅ 2nd Level Commission – 10%\n"
    "Earn 10% commission on the task earnings of users invited by your first-level members.\n\n"
    "🎁 TREASURE CHEST REWARDS\n"
    "500 | 600 | 1,000 | 1,500 | 2,000 | 3,000 | 5,000 | 10,000 Points\n\n"
    "📲 HOW TO INVITE?\n\n"
    "1️⃣ Copy your referral link\n"
    "2️⃣ Share it with your friends\n"
    "3️⃣ Help them register and complete tasks\n"
    "4️⃣ Earn Rewards & Commission! 💰\n\n"
    "🔥 MORE INVITES = MORE REWARDS = MORE EARNINGS!\n\n"
    "👉 Join 1GO.TASK today and start your earning journey!\n\n"
    f"🔗 Your Referral Link:\n{REFERRAL_LINK}"
)


async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(REFERRAL_PROMO_TEXT)


async def help_center(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🆘 1Go.Task Support Center 💬\n\n"
        "Facing any problem or need help? Contact our official admin. 🤝\n\n"
        "📩 Support: @G_one_77\n\n"
        "🛠️ Account • Tasks • Rewards • Withdrawals\n\n"
        "⚡ Any issue? Just contact us — we're here to help! ❤️"
    )


async def channel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📢 Official Group Link 🔗\n"
        "https://t.me/onegotaskcommunicationgroup\n\n"
        "📢 Official Channel Link 🔗\n"
        "https://t.me/onegotask"
    )


async def customer_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✅Official Customer Service Contacts\n\n"
        "Username @banana04270327\n\n"
        "Thank u 🙏🏻"
    )


async def report_problem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["awaiting_problem_report"] = True
    await update.message.reply_text(
        "📝 Apni problem yahan likh kar bhej dein — hum jaldi hi contact karenge."
    )


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Baaki normal text messages ka reply deta hai"""
    if context.user_data.get("awaiting_problem_report"):
        user = update.effective_user
        username = f"@{user.username}" if user.username else "(no username)"
        problem_text = update.message.text

        # Admin ko forward karo
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"📩 Naya Problem Report\n\n"
                    f"👤 User: {user.first_name} {username}\n"
                    f"🆔 ID: {user.id}\n\n"
                    f"💬 Problem:\n{problem_text}"
                ),
            )
        except Exception as e:
            logger.error(f"Problem report admin ko bhejne mein error: {e}")

        context.user_data["awaiting_problem_report"] = False
        await update.message.reply_text(
            "✅ Aapki problem admin ko bhej di gayi hai. Jaldi hi contact kiya jayega."
        )
        return

    await update.message.reply_text(
        "⚠️ Please neeche diye menu/tools se koi option choose karein.",
        reply_markup=MAIN_MENU_MARKUP,
    )


async def setup_commands(application):
    """Bot start hote hi ye commands list set kar deta hai — isse chat mein
    'tools' menu icon (4 boxes) show hone lagta hai"""
    await application.bot.set_my_commands([
        ("start", "Bot shuru karein"),
        ("help", "Help dekhein"),
    ])


def main():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("⚠️  Pehle BOT_TOKEN daalo file mein (BotFather se lo)!")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).post_init(setup_commands).build()

    # Handlers register karo
    app.add_handler(CommandHandler("start", start, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("help", help_command, filters=filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("userscount", userscount))
    app.add_handler(CommandHandler("broadcastvideo", broadcastvideo))
    app.add_handler(CommandHandler("setsmsvideo", setsmsvideo))
    app.add_handler(CommandHandler("setwhatsappvideo", setwhatsappvideo))
    app.add_handler(CommandHandler("getemojipack", getemojipack))
    app.add_handler(CommandHandler("groupid", groupid))
    app.add_handler(CommandHandler("announce", announce))
    app.add_handler(CommandHandler("addannouncement", addannouncement))
    app.add_handler(CommandHandler("stopadding", stopadding))
    app.add_handler(CommandHandler("listannouncements", listannouncements))
    app.add_handler(CommandHandler("clearannouncements", clearannouncements))

    # Admin photo bhejega (announcement ke liye) to yahan capture hoga
    app.add_handler(MessageHandler(filters.PHOTO, receive_photo))

    # Har 15 minute mein auto-announcement check/send karo
    app.job_queue.run_repeating(send_scheduled_announcement, interval=ANNOUNCE_INTERVAL_SECONDS, first=10)

    # Har 30 minute mein welcome reminder bhejo (poore din)
    app.job_queue.run_repeating(send_welcome_reminder, interval=WELCOME_REMINDER_INTERVAL_SECONDS, first=20)

    # Admin video bhejega to file_id yahan capture hoga
    app.add_handler(MessageHandler(filters.VIDEO, receive_video))

    # Group mein naya member add hone par welcome message
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))

    # Menu button handlers (exact text match, command ke pehle register karo)
    # Sirf private chat mein kaam karenge — group mein nahi dikhenge
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.Regex("^📩 SMS Task$"), sms_task))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.Regex("^💬 WhatsApp Task$"), whatsapp_task))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.Regex("^🎁 Referral$"), referral))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.Regex("^🆘 Help Center$"), help_center))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.Regex("^📢 Channel$"), channel))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.Regex("^🎧 Customer Service$"), customer_service))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.Regex("^📝 Report Problem$"), report_problem))

    # Baaki sab text ke liye generic echo (sabse aakhir mein) — sirf private chat mein
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, echo))

    print("🤖 Bot start ho raha hai... (Ctrl+C se rokein)")
    app.run_polling()


if __name__ == "__main__":
    import sys
    try:
        main()
    except KeyboardInterrupt:
        pass  # Ctrl+C se normal band hua
    except Exception as e:
        print(f"⚠️ Bot crash ho gaya: {e}")
        print("🔄 Bot process dobara (fresh) start ho raha hai...")
        import time
        time.sleep(5)
        # Poora process restart karo (fresh event loop ke saath) — isse
        # "Event loop is closed" jaisi errors nahi aati
        os.execv(sys.executable, [sys.executable] + sys.argv)
