# features/common_handlers.py

import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.helpers import escape_markdown

from core import database
from utils import helpers, keyboards
from texts import RESPONSE_MESSAGES
import config

logger = logging.getLogger(__name__)

# Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the /start command and referrals."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    logger.info(f"Command /start from user: {user.id} ({user.username}) in chat {chat_id}")

    # Ensure user exists in the database
    db_user = database.get_or_create_user(user.id, user.first_name, user.username)

    # Handle referral logic if 'start' has arguments
    if context.args and context.args[0].startswith('ref_'):
        referral_code = context.args[0][4:]
        referrer = database.get_user_by_referral_code(referral_code) # You'll need to create this function in database.py

        if referrer and referrer['user_id'] != user.id:
            # set_referrer now returns True if successful, False otherwise
            if database.set_referrer(user.id, referrer['user_id']):
                try:
                    referrer_share_count = database.get_user_by_id(referrer['user_id'])['share_count']
                    await context.bot.send_message(
                        chat_id=referrer['user_id'],
                        text=RESPONSE_MESSAGES["referral_successful_notification_to_referrer"].format(share_count=referrer_share_count)
                    )
                except Exception as e:
                    logger.error(f"Failed to notify referrer {referrer['user_id']}: {e}")

                referrer_name = escape_markdown(referrer['first_name'], version=2)
                await update.message.reply_text(
                    RESPONSE_MESSAGES["new_user_welcome_referred"].format(referrer_name=referrer_name),
                    parse_mode='MarkdownV2'
                )
        elif referrer and referrer['user_id'] == user.id:
            await update.message.reply_text(RESPONSE_MESSAGES["cannot_refer_self"])
        else:
            logger.info(f"Invalid or non-existent referral code used: {referral_code}")

    # Send the main menu
    await show_main_menu(update, context)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handler cho /cancel: Dùng để huỷ mọi conversation đang diễn ra.
    Hỗ trợ cả tin nhắn và callback query.
    """
    if update.message:
        await update.message.reply_text("🚫 Bạn đã huỷ thao tác.")
    elif update.callback_query:
        await update.callback_query.answer("🚫 Bạn đã huỷ thao tác.")
        await update.callback_query.edit_message_reply_markup(None)

    return -1  # END trong ConversationHandler


# Menu Navigation Handlers
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Hiển thị menu chính.
    - Nếu được gọi từ CallbackQuery (bấm nút), nó sẽ edit tin nhắn.
    - Nếu được gọi từ Message (lệnh /start), nó sẽ gửi tin nhắn mới.
    """
    # Tạo nội dung và bàn phím trước
    # Lấy user từ đúng nguồn (effective_user là an toàn nhất)
    text = RESPONSE_MESSAGES["welcome_message"]
    keyboard = keyboards.create_main_menu_markup()

    # Kiểm tra xem update này đến từ việc bấm nút hay không
    if update.callback_query:
        # Đây là trường hợp bấm nút "Quay lại"
        query = update.callback_query
        await query.answer()
        # Sử dụng hàm helper an toàn để edit
        await helpers.edit_message_safely(query, text, keyboard)
    else:
        # Đây là trường hợp được gọi từ /start (hoặc một lệnh khác)
        # Gửi một tin nhắn MỚI
        if config.START_IMAGE_FILE_ID :
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=config.START_IMAGE_FILE_ID ,
                caption=text,
                reply_markup=keyboard
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=text,
                reply_markup=keyboard
            )

    # Nếu hàm này được dùng trong ConversationHandler, nó cần trả về trạng thái kết thúc
    return ConversationHandler.END

async def show_promo_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the promotions menu."""
    query = update.callback_query
    await query.answer()

    text = RESPONSE_MESSAGES["choose_promo_message"]
    reply_markup = keyboards.create_promo_menu_markup()

    await helpers.edit_message_safely(query, text, reply_markup)
    return ConversationHandler.END

async def show_transaction_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hiển thị menu Nạp/Rút."""
    query = update.callback_query
    await query.answer()
    text = RESPONSE_MESSAGES["transaction_menu_intro"]
    keyboard = keyboards.create_transaction_menu_markup()
    await helpers.edit_message_safely(query, text, keyboard, parse_mode=None)