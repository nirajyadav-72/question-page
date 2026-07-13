import os
import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ChatMemberHandler, filters, ContextTypes

# .env फाइल से डेटा लोड करना
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID")) if os.getenv("OWNER_ID") else None

# लॉगिंग सेटअप
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

DB_FILE = "bot_database.db"

def init_db():
    """डेटाबेस और सभी ज़रूरी टेबल्स बनाना"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS members (
            chat_id INTEGER,
            user_id INTEGER,
            first_name TEXT,
            PRIMARY KEY (chat_id, user_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bot_admin_groups (
            chat_id INTEGER PRIMARY KEY,
            chat_title TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_member(chat_id, user_id, first_name):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO members (chat_id, user_id, first_name) VALUES (?, ?, ?)', (chat_id, user_id, first_name))
    conn.commit()
    conn.close()

def get_members(chat_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, first_name FROM members WHERE chat_id = ?', (chat_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def add_admin_group(chat_id, chat_title):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO bot_admin_groups (chat_id, chat_title) VALUES (?, ?)', (chat_id, chat_title))
    conn.commit()
    conn.close()

def remove_admin_group(chat_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM bot_admin_groups WHERE chat_id = ?', (chat_id,))
    conn.commit()
    conn.close()

def get_admin_groups():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT chat_id, chat_title FROM bot_admin_groups')
    rows = cursor.fetchall()
    conn.close()
    return rows
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start - वेलकम मैसेज बटन के साथ"""
    user = update.effective_user
    chat_type = update.effective_chat.type
    bot_user = await context.bot.get_me()
    add_url = f"https://t.me{bot_user.username}?startgroup=true"

    if chat_type == "private":
        if user.id == OWNER_ID:
            owner_welcome = (
                f"👋 **नमस्ते बॉस, आपका स्वागत है!**\n\n"
                f"⚙️ **ओनर पैनल्स एक्टिवेटेड:**\n"
                f"• ग्रुप लिस्ट देखने के लिए `/mygroups` लिखें।\n"
                f"• सभी ग्रुप्स में मैसेज भेजने के लिए `/broadcast [मैसेज]` लिखें।\n"
                f"• सभी कमांड्स जानने के लिए `/help` टाइप करें।"
            )
            keyboard = [[InlineKeyboardButton("➕ Add Me To Your Group ➕", url=add_url)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(owner_welcome, reply_markup=reply_markup, parse_mode="Markdown")
        else:
            user_welcome = (
                f"👋 **हेलो {user.first_name}!**\n\n"
                f"🤖 मैं एक शक्तिशाली **मेंशन बॉट (Mention Bot)** हूँ।\n\n"
                f"📌 **मैं आपकी क्या मदद कर सकता हूँ?**\n"
                f"• मुझे अपने टेलीग्राम ग्रुप में जोड़ें और एडमिन बनाएं।\n"
                f"• ग्रुप में सभी को टैग करने के लिए सीधे `@all` या `@tagall` लिखें।\n"
                f"• पूरी जानकारी के लिए `/help` टाइप करें।"
            )
            keyboard = [[InlineKeyboardButton("➕ Add Me To Your Group ➕", url=add_url)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(user_welcome, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(f"🤖 **बॉट एक्टिव है!**", parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/help - हेल्प मेनू और ओनर बटन"""
    user = update.effective_user
    bot_user = await context.bot.get_me()
    
    help_text = (
        f"📖 **बॉट हेल्प गाइड (Help Menu)**\n\n"
        f"👥 **ग्रुप टैगिंग शब्द:**\n"
        f"• `@all` या `@tagall` - ग्रुप के सभी सदस्यों को टैग करने के लिए। (केवल एडमिन्स के लिए)\n"
        f"• `@admin` या `@admins` - ग्रुप के सभी एडमिन्स को अलर्ट भेजने के लिए।\n\n"
        f"🤖 **सामान्य कमांड्स:**\n"
        f"• `/start` - बॉट शुरू करने के लिए।\n"
        f"• `/help` - हेल्प मैनुअल देखने के लिए।"
    )

    if user.id == OWNER_ID:
        help_text += (
            f"\n\n👑 **ओनर स्पेशल कमांड्स:**\n"
            f"• `/mygroups` - एडमिन ग्रुप्स की लिस्ट देखें।\n"
            f"• `/broadcast [मैसेज]` - सभी ग्रुप्स में मैसेज भेजें।"
        )

    buttons = []
    add_url = f"https://t.me{bot_user.username}?startgroup=true"
    buttons.append([InlineKeyboardButton("➕ Add Me To Your Group ➕", url=add_url)])
    
    if OWNER_ID:
        owner_chat_url = f"tg://user?id={OWNER_ID}"
        buttons.append([InlineKeyboardButton("👨‍💻 Contact Owner", url=owner_chat_url)])
        
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text(help_text, reply_markup=reply_markup, parse_mode="Markdown")
  async def handle_group_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """टेक्स्ट मैसेज स्कैन करना, प्राइवेट चैट वार्निंग देना और ग्रुप्स में टैगिंग संभालना"""
    if not update.message or not update.message.text:
        return

    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    user = update.effective_user
    message_text = update.message.text.strip().lower()

    is_tagall_trigger = message_text.startswith("@all") or message_text.startswith("@tagall")
    is_admin_trigger = message_text.startswith("@admin") or message_text.startswith("@admins")

    if is_tagall_trigger or is_admin_trigger:
        # प्राइवेट चैट वार्निंग सुरक्षा चेक
        if chat_type == "private":
            await update.message.reply_text("❌ **कृपया इस कमांड का उपयोग केवल टेलीग्राम ग्रुप में करें!** Private चैट में टैगिंग काम नहीं करती है।")
            return

        # 1. @all या @tagall प्रोसेसिंग (ग्रुप में)
        if is_tagall_trigger:
            try:
                chat_admins = await context.bot.get_chat_administrators(chat_id)
                admin_ids = [admin.user.id for admin in chat_admins]
            except Exception:
                await update.message.reply_text("⚠️ मुझे ग्रुप एडमिन परमिशन दें ताकि मैं मेंबर्स की लिस्ट निकाल सकूँ।")
                return
            
            if user.id not in admin_ids:
                await update.message.reply_text("❌ सिर्फ ग्रुप एडमिन्स ही सबको टैग कर सकते हैं!")
                return

            saved_members = get_members(chat_id)
            if not saved_members:
                await update.message.reply_text("⚠️ डेटाबेस में अभी कोई मेंबर सेव नहीं है।")
                return

            orig_text = update.message.text.strip()
            user_msg = orig_text.replace("@all", "").replace("@TAGALL", "").replace("@tagall", "").replace("@ALL", "").strip()
            base_text = f"📢 **अटेंशन प्लीज!**\n{user_msg}\n\n" if user_msg else "📢 **अटेंशन प्लीज!**\n\n"
            
            current_text = base_text
            count = 0
            for u_id, f_name in saved_members:
                safe_name = f_name.replace('[', '').replace(']', '').replace('(', '').replace(')', '')
                current_text += f"[{safe_name}](tg://user?id={u_id}) "
                count += 1
                if count >= 40:
                    await context.bot.send_message(chat_id=chat_id, text=current_text, parse_mode="Markdown")
                    current_text = ""
                    count = 0
            if current_text:
                await context.bot.send_message(chat_id=chat_id, text=current_text, parse_mode="Markdown")

        # 2. @admin या @admins प्रोसेसिंग (ग्रुप में)
        elif is_admin_trigger:
            try:
                chat_admins = await context.bot.get_chat_administrators(chat_id)
                orig_text = update.message.text.strip()
                user_msg = orig_text
                for kw in ["@admin", "@admins", "@ADMIN", "@ADMINS"]:
                    user_msg = user_msg.replace(kw, "")
                user_msg = user_msg.strip()

                text = f"⚠️ **एडमिन अलर्ट!**\n{user_msg}\n\n" if user_msg else "⚠️ **ग्रुप एडमिन्स ध्यान दें:**\n\n"
                for admin in chat_admins:
                    if not admin.user.is_bot:
                        safe_name = admin.user.first_name.replace('[', '').replace(']', '').replace('(', '').replace(')', '')
                        text += f"[{safe_name}](tg://user?id={admin.user.id}) "
                await update.message.reply_text(text, parse_mode="Markdown")
            except Exception as e:
                logger.error(f"Error in tag_admins: {e}")
                
    elif chat_type in ["group", "supergroup"] and user and not user.is_bot:
        save_member(chat_id, user.id, user.first_name)

      async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ग्रुप में नए मेंबर के आने पर वेलकम मैसेज या थैंक्स बटन"""
    chat_id = update.effective_chat.id
    bot_user = await context.bot.get_me()
    
    for new_member in update.message.new_chat_members:
        if new_member.id == bot_user.id:
            thanks_text = (
                f"💖 **थैंक्यू मुझे इस ग्रुप में ऐड करने के लिए!**\n\n"
                f"🤖 मैं इस ग्रुप के सभी मेंबर्स को टैग करने में आपकी मदद करूँगा।\n\n"
                f"⚙️ **महत्वपूर्ण:** कृपया मुझे ग्रुप में **Admin** बनाएं ताकि टैगिंग फीचर्स काम कर सकें!"
            )
            add_url = f"https://t.me{bot_user.username}?startgroup=true"
            keyboard = [[InlineKeyboardButton("➕ Add Me To Your Group ➕", url=add_url)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(thanks_text, reply_markup=reply_markup, parse_mode="Markdown")
            return

        if not new_member.is_bot:
            save_member(chat_id, new_member.id, new_member.first_name)
            welcome_text = (
                f"🎉 **ग्रुप में आपका स्वागत है, [{new_member.first_name}](tg://user?id={new_member.id})!**\n\n"
                f"🤖 *मदद के लिए ग्रुप में `/help` टाइप करें या सीधे `@all` लिखकर सबको टैग करें।*"
            )
            await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def track_bot_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ट्रैक करना कि बॉट कहाँ एडमिन बना या हटा"""
    status_update = update.my_chat_member
    if not status_update:
        return
    chat_id = status_update.chat.id
    chat_title = status_update.chat.title
    new_status = status_update.new_chat_member.status

    if new_status in ["administrator", "creator"]:
        add_admin_group(chat_id, chat_title)
    else:
        remove_admin_group(chat_id)

async def list_my_groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/mygroups - ओनर ग्रुप लिस्ट"""
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ आप ओनर नहीं हैं।")
        return
    admin_groups = get_admin_groups()
    if not admin_groups:
        await update.message.reply_text("📁 बॉट अभी कहीं भी एडमिन नहीं है।")
        return
    response = "📋 **बॉस, मैं इन सभी ग्रुप्स में एडमिन हूँ:**\n\n"
    for c_id, title in admin_groups:
        response += f"🔹 **{title}** (ID: `{c_id}`)\n"
    await update.message.reply_text(response, parse_mode="Markdown")

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/broadcast - ओनर ब्रॉडकास्ट"""
    if update.effective_user.id != OWNER_ID:
        return
    broadcast_msg = " ".join(context.args)
    if not broadcast_msg:
        await update.message.reply_text("⚠️ कृपया मैसेज लिखें।")
        return
    admin_groups = get_admin_groups()
    success_count = 0
    for chat_id, title in admin_groups:
        try:
            await context.bot.send_message(chat_id=chat_id, text=f"📢 **बॉट ओनर की सूचना:**\n\n{broadcast_msg}")
            success_count += 1
        except Exception:
            pass
    await update.message.reply_text(f"✅ ब्रॉडकास्ट पूरा हुआ! सफल: {success_count} ग्रुप्स।")

def main():
    init_db()
    if not BOT_TOKEN:
        print("❌ एरर: .env फाइल में BOT_TOKEN नहीं मिला!")
        return

    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("mygroups", list_my_groups))
    application.add_handler(CommandHandler("broadcast", broadcast_command))

    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    application.add_handler(ChatMemberHandler(track_bot_status, ChatMemberHandler.MY_CHAT_MEMBER))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_group_messages))

    print("🤖 बॉट सफलतापूर्वक चालू हो गया है...")
    application.run_polling()

if __name__ == '__main__':
    main()
          
