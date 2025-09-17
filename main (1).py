import logging
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
user_sessions = {}  # {user_id: {'message_id': message_id, 'owner_message_id': owner_message_id}}

# ملف لتخزين البيانات
DATA_FILE = "bot_data.json"

def save_data():
    """حفظ البيانات في ملف"""
    data = {
        'owner_id': owner_id,
        'owner_username': owner_username,
        'user_sessions': user_sessions
    }
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

def load_data():
    """تحميل البيانات من ملف"""
    global owner_id, owner_username, user_sessions
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            owner_id = data.get('owner_id')
            owner_username = data.get('owner_username')
            user_sessions = data.get('user_sessions', {})
    except FileNotFoundError:
        # إذا لم يوجد ملف، نبدأ بقيم افتراضية
        owner_id = None
        owner_username = None
        user_sessions = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global owner_id, owner_username
    
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # إذا لم يتم تعيين مالك بعد، جعل هذا المستخدم المالك
    if owner_id is None:
        owner_id = user.id
        owner_username = user.username or user.first_name
        
        await update.message.reply_text(
            f"👑 مرحباً يا المالك! {user.mention_markdown()}\n\n"
            f"✅ أنت الآن المالك الرسمي لهذا البوت\n"
            f"📩 سيتم إرسال جميع رسائل المستخدمين إليك\n"
            f"💬 يمكنك الرد على أي رسالة بالرد عليها مباشرة",
            parse_mode='Markdown'
        )
        logger.info(f"تم تعيين المالك: {owner_username} (ID: {owner_id})")
        save_data()
    
    else:
        # إذا كان المستخدم هو المالك
        if user.id == owner_id:
            await update.message.reply_text(
                f"مرحباً kembali يا المالك! 👑\n\n"
                f"أنت مالك هذا البوت التواصلي\n"
                f"يمكنك استقبال رسائل المستخدمين والرد عليها",
                parse_mode='Markdown'
            )
        else:
            # إذا كان مستخدم عادي
            keyboard = [
                [InlineKeyboardButton("📩 إرسال رسالة", callback_data='send_message')],
                [InlineKeyboardButton("ℹ️ معلومات", callback_data='info')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"مرحباً {user.mention_markdown()}! 👋\n\n"
                f"أنا بوت تواصل يمكنك من خلاله إرسال رسائل إلى المالك\n\n"
                f"📨 فقط أرسل رسالتك وسأقوم بإرسالها إلى المالك\n"
                f"🔄 يمكنك التواصل مع المالك عبر هذا البوت",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message
    
    # تجاهل الرسائل من المالك
    if user.id == owner_id:
        # إذا كان الرد على رسالة محولة
        if message.reply_to_message:
            replied_message = message.reply_to_message
            if hasattr(replied_message, 'forward_from') and replied_message.forward_from:
                # الرد على مستخدم مباشرة
                target_user_id = replied_message.forward_from.id
                try:
                    await context.bot.send_message(
                        chat_id=target_user_id,
                        text=f"📩 رد من المالك:\n\n{message.text}"
                    )
                    await message.reply_text("✅ تم إرسال الرد إلى المستخدم")
                except Exception as e:
                    await message.reply_text("❌ لا يمكن إرسال الرسالة، قد يكون المستخدم حظر البوت")
        return
    
    # إذا كان المستخدم العادي يرسل رسالة
    if owner_id:
        try:
            # إرسال الرسالة إلى المالك مع معلومات المستخدم
            sent_message = await context.bot.send_message(
                chat_id=owner_id,
                text=f"📨 رسالة جديدة من {user.mention_markdown()}\n"
                     f"🆔 ID: `{user.id}`\n"
                     f"📛 الاسم: {user.full_name}\n"
                     f"👤 المعرف: @{user.username if user.username else 'لا يوجد'}\n\n"
                     f"💬 الرسالة:\n{message.text}",
                parse_mode='Markdown'
            )
            
            # حفظ معلومات الجلسة
            user_sessions[user.id] = {
                'message_id': message.message_id,
                'owner_message_id': sent_message.message_id
            }
            save_data()
            
            await message.reply_text("✅ تم إرسال رسالتك إلى المالك")
            
        except Exception as e:
            await message.reply_text("❌ حدث خطأ في إرسال الرسالة")
            logger.error(f"Error sending message to owner: {e}")
    else:
        await message.reply_text("⚠️ لم يتم تعيين مالك بعد!")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    
    if query.data == 'send_message':
        await query.edit_message_text(
            f"💬 أرسل رسالتك الآن وسأقوم بإرسالها إلى المالك\n\n"
            f"يمكنك كتابة أي رسالة تريد إرسالها"
        )
    elif query.data == 'info':
        if owner_id:
            await query.edit_message_text(
                f"ℹ️ معلومات البوت:\n\n"
                f"🤖 هذا بوت تواصل\n"
                f"👑 المالك: @{owner_username}\n"
                f"📨 أرسل أي رسالة وسيتم تحويلها للمالك\n"
                f"↩️ المالك يمكنه الرد على رسائلك"
            )
        else:
            await query.edit_message_text("⚠️ لم يتم تعيين مالك بعد!")

async def handle_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.message
    
    # تجاهل الوسائط من المالك
    if user.id == owner_id:
        return
    
    # إرسال الوسائط إلى المالك
    if owner_id:
        try:
            caption = f"📎 وسائط من {user.mention_markdown()}\n\n{message.caption or ''}"
            
            if message.photo:
                await context.bot.send_photo(
                    chat_id=owner_id,
                    photo=message.photo[-1].file_id,
                    caption=caption,
                    parse_mode='Markdown'
                )
            elif message.video:
                await context.bot.send_video(
                    chat_id=owner_id,
                    video=message.video.file_id,
                    caption=caption,
                    parse_mode='Markdown'
                )
            elif message.document:
                await context.bot.send_document(
                    chat_id=owner_id,
                    document=message.document.file_id,
                    caption=caption,
                    parse_mode='Markdown'
                )
            elif message.audio:
                await context.bot.send_audio(
                    chat_id=owner_id,
                    audio=message.audio.file_id,
                    caption=caption,
                    parse_mode='Markdown'
                )
            
            await message.reply_text("✅ تم إرسال الوسائط إلى المالك")
            
        except Exception as e:
            await message.reply_text("❌ حدث خطأ في إرسال الوسائط")
            logger.error(f"Error sending media to owner: {e}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر للبث الجماعي (للمالك فقط)"""
    user = update.effective_user
    
    if user.id != owner_id:
        await update.message.reply_text("⛔ ليس لديك صلاحية استخدام هذا الأمر!")
        return
    
    if not context.args:
        await update.message.reply_text("📢 usage: /broadcast <message>")
        return
    
    message_text = ' '.join(context.args)
    success_count = 0
    fail_count = 0
    
    # الحصول على جميع المستخدمين الذين تفاعلوا مع البوت
    user_ids = list(user_sessions.keys())
    
    for user_id in user_ids:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=f"📢 إعلان من المالك:\n\n{message_text}"
            )
            success_count += 1
        except:
            fail_count += 1
    
    await update.message.reply_text(
        f"✅ تم إرسال الإعلان:\n"
        f"✅ نجح: {success_count}\n"
        f"❌ فشل: {fail_count}"
    )

def main():
    # تحميل البيانات المحفوظة
    load_data()
    
    # احصل على التوكن
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        TOKEN = "8097867469:AAFaAjWAOh_LgGHamjh5uUoKWLmYhNEgXpc"  # استبدل هذا بتوكن بوتك
    
    # إنشاء التطبيق
    application = Application.builder().token(TOKEN).build()
    
    # إضافة handlers - التصحيح هنا
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # إضافة handlers للوسائط بشكل منفصل
    application.add_handler(MessageHandler(filters.PHOTO, handle_media))
    application.add_handler(MessageHandler(filters.VIDEO, handle_media))
    application.add_handler(MessageHandler(filters.DOCUMENT, handle_media))
    application.add_handler(MessageHandler(filters.AUDIO, handle_media))
    
    # بدء البوت
    print("🤖 بوت التواصل يعمل...")
    print(f"👑 المالك الحالي: {owner_username} (ID: {owner_id})" if owner_id else "⚠️ لم يتم تعيين مالك بعد")
    
    application.run_polling()

if __name__ == '__main__':
    main()
