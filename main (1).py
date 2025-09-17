import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler,
    ContextTypes, 
    filters
)
import os
import json

# إعدادات التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# تخزين البيانات
owner_id = None
owner_username = None
user_sessions = {}

# ملف لتخزين البيانات
DATA_FILE = "bot_data.json"

def save_data():
    data = {
        'owner_id': owner_id,
        'owner_username': owner_username,
        'user_sessions': user_sessions
    }
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def load_data():
    global owner_id, owner_username, user_sessions
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            owner_id = data.get('owner_id')
            owner_username = data.get('owner_username')
            user_sessions = data.get('user_sessions', {})
    except FileNotFoundError:
        owner_id = None
        owner_username = None
        user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global owner_id, owner_username
    
    user = update.effective_user
    
    if owner_id is None:
        owner_id = user.id
        owner_username = user.username or user.first_name
        
        await update.message.reply_text(
            f"👑 مرحباً يا المالك! {user.mention_markdown()}\n\n"
            f"✅ أنت الآن المالك الرسمي لهذا البوت\n"
            f"📩 سيتم إرسال جميع رسائل المستخدمين إليك",
            parse_mode='Markdown'
        )
        save_data()
    
    else:
        if user.id == owner_id:
            await update.message.reply_text("مرحباً kembali يا المالك! 👑")
        else:
            keyboard = [
                [InlineKeyboardButton("📩 إرسال رسالة", callback_data='send_message')],
                [InlineKeyboardButton("ℹ️ معلومات", callback_data='info')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"مرحباً {user.mention_markdown()}! 👋\n\n"
                f"أنا بوت تواصل يمكنك من خلاله إرسال رسائل إلى المالك",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message
    
    if user.id == owner_id:
        if message.reply_to_message:
            replied_message = message.reply_to_message
            if hasattr(replied_message, 'forward_from') and replied_message.forward_from:
                target_user_id = replied_message.forward_from.id
                try:
                    await context.bot.send_message(
                        chat_id=target_user_id,
                        text=f"📩 رد من المالك:\n\n{message.text}"
                    )
                    await message.reply_text("✅ تم إرسال الرد إلى المستخدم")
                except Exception as e:
                    await message.reply_text("❌ لا يمكن إرسال الرسالة")
        return
    
    if owner_id:
        try:
            sent_message = await context.bot.send_message(
                chat_id=owner_id,
                text=f"📨 رسالة جديدة من {user.mention_markdown()}\n"
                     f"🆔 ID: `{user.id}`\n"
                     f"📛 الاسم: {user.full_name}\n\n"
                     f"💬 الرسالة:\n{message.text}",
                parse_mode='Markdown'
            )
            
            user_sessions[user.id] = {
                'message_id': message.message_id,
                'owner_message_id': sent_message.message_id
            }
            save_data()
            
            await message.reply_text("✅ تم إرسال رسالتك إلى المالك")
            
        except Exception as e:
            await message.reply_text("❌ حدث خطأ في إرسال الرسالة")
    else:
        await message.reply_text("⚠️ لم يتم تعيين مالك بعد!")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'send_message':
        await query.edit_message_text("💬 أرسل رسالتك الآن")
    elif query.data == 'info':
        if owner_id:
            await query.edit_message_text(f"👑 المالك: @{owner_username}")
        else:
            await query.edit_message_text("⚠️ لم يتم تعيين مالك بعد!")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id == owner_id:
        return
    
    if owner_id:
        try:
            await context.bot.send_photo(
                chat_id=owner_id,
                photo=update.message.photo[-1].file_id,
                caption=f"📸 صورة من {user.mention_markdown()}",
                parse_mode='Markdown'
            )
            await update.message.reply_text("✅ تم إرسال الصورة إلى المالك")
        except Exception as e:
            await update.message.reply_text("❌ حدث خطأ في إرسال الصورة")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id == owner_id:
        return
    
    if owner_id:
        try:
            await context.bot.send_document(
                chat_id=owner_id,
                document=update.message.document.file_id,
                caption=f"📄 ملف من {user.mention_markdown()}",
                parse_mode='Markdown'
            )
            await update.message.reply_text("✅ تم إرسال الملف إلى المالك")
        except Exception as e:
            await update.message.reply_text("❌ حدث خطأ في إرسال الملف")

def run_bot():
    """تشغيل البوت في event loop منفصل"""
    load_data()
    
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', "8097867469:AAFaAjWAOh_LgGHamjh5uUoKWLmYhNEgXpc")
    
    # إنشاء event loop جديد
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        application = Application.builder().token(TOKEN).build()
        
        # إضافة handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button_handler))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        application.add_handler(MessageHandler(filters.DOCUMENT, handle_document))
        
        print("🤖 بوت التواصل يعمل...")
        if owner_id:
            print(f"👑 المالك الحالي: {owner_username} (ID: {owner_id})")
        else:
            print("⚠️ لم يتم تعيين مالك بعد")
        
        application.run_polling()
        
    except Exception as e:
        print(f"❌ خطأ في تشغيل البوت: {e}")
    finally:
        loop.close()

if __name__ == '__main__':
    # هذا سيعمل فقط إذا تم تشغيل الملف مباشرة وليس عبر Streamlit
    run_bot()
