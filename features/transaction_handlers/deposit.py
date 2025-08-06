# features/transaction_handlers/deposit.py

import logging
from telegram import Update
from telegram.ext import (
    ConversationHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from ..fallbacks import get_fallbacks
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown
from utils.decorators import log_callback_query
from utils import helpers, keyboards
from texts import RESPONSE_MESSAGES
import config
from core.request_limiter import is_request_available, increment_count_in_cache

logger = logging.getLogger(__name__)

# State constants for the deposit flow
AWAIT_DEPOSIT_USERNAME, AWAIT_DEPOSIT_RECEIPT = range(2)

@log_callback_query
async def start_deposit_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for the deposit support flow. Asks for username."""
    query = update.callback_query
    user = update.effective_user
    user_id = user.id

    # Kiểm tra điều kiện mà không thực hiện bất kỳ lệnh `await` nào
    if not is_request_available(user_id, "transaction"):
        # Nếu hết lượt, gọi answer() MỘT LẦN DUY NHẤT để hiển thị pop-up.
        await helpers.edit_message_safely(
            query=query,
            new_text=RESPONSE_MESSAGES["out_of_requests_trans"],
            # Cung cấp nút "Quay lại Menu" để dọn dẹp
            new_reply_markup=keyboards.create_cleanup_keyboard()
        )
        return ConversationHandler.END

    helpers.add_message_to_cleanup_list(context, query.message)

    text = RESPONSE_MESSAGES["ask_username_deposit"]
    reply_text = await helpers.edit_message_safely(
    query=query,
    new_text=text,
    new_reply_markup=keyboards.create_back_to_transaction_menu_markup()
    )
    helpers.add_message_to_cleanup_list(context, reply_text)
    return AWAIT_DEPOSIT_USERNAME

async def receive_deposit_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the username and asks for the receipt."""
    user_message = update.message
    helpers.add_message_to_cleanup_list(context, user_message)
    context.user_data['game_username'] = update.message.text.strip()
    game_username = user_message.text.strip()
    if not helpers.is_valid_username(game_username):
        # Gửi tin nhắn báo lỗi
        final_keyboard = keyboards.create_cleanup_keyboard()
        error_message = await update.message.reply_text(
            text=RESPONSE_MESSAGES["invalid_username_format"],
            reply_markup=final_keyboard,
            parse_mode=ParseMode.MARKDOWN_V2
        )

        # Thêm cả tin nhắn sai của user và tin nhắn báo lỗi của bot vào danh sách dọn dẹp
        helpers.add_message_to_cleanup_list(context, error_message)

        # QUAN TRỌNG: Kết thúc cuộc hội thoại ngay lập tức
        return ConversationHandler.END
    text = RESPONSE_MESSAGES["ask_for_receipt"]
    reply_text = await update.message.reply_text(text, reply_markup=keyboards.create_cleanup_keyboard())
    helpers.add_message_to_cleanup_list(context, reply_text)
    return AWAIT_DEPOSIT_RECEIPT

async def receive_deposit_receipt_and_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the receipt, sends it to the admin, and ends the conversation."""
    user = update.effective_user
    user_message = update.message
    helpers.add_message_to_cleanup_list(context, user_message)
    game_username = context.user_data.get('game_username', 'Chưa cung cấp')
    photo_id = update.message.photo[-1].file_id


    final_keyboard = keyboards.create_cleanup_keyboard()
    reply_text = await update.message.reply_text(RESPONSE_MESSAGES["receipt_received_thanks"], reply_markup=final_keyboard)
    helpers.add_message_to_cleanup_list(context, reply_text)

    admin_caption = (
        f"📝 *Yêu cầu NẠP TIỀN*\\- [{escape_markdown(user.first_name, version=2)}](tg://user?id={user.id})\n"
        f"🎮 ID: `{escape_markdown(game_username, version=2)}`\n"
    )
    admin_keyboard = keyboards.create_admin_deposit_keyboard(user.id)

    try:
        await context.bot.send_photo(
            chat_id=config.ID_GROUP_TRANSACTION,
            photo=photo_id,
            caption=admin_caption,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=admin_keyboard
        )
        increment_count_in_cache(user.id, "transaction")
    except Exception as e:
        logger.error(f"Failed to send DEPOSIT request to admin group: {e}")

    #context.user_data.clear()
    return ConversationHandler.END

# --- Deposit Conversation Handler ---
deposit_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_deposit_flow, pattern='^transaction_deposit$')],
    states={
        AWAIT_DEPOSIT_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_deposit_username)],
        AWAIT_DEPOSIT_RECEIPT: [MessageHandler(filters.PHOTO, receive_deposit_receipt_and_end)],
    },
    fallbacks=get_fallbacks(),
    block=False,
    name="deposit_conversation"
)