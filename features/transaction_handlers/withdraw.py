# features/transaction_handlers/withdraw.py

import logging
from telegram import Update
from telegram.ext import (
    ConversationHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown
from utils.decorators import log_callback_query
from utils import helpers, keyboards
from texts import RESPONSE_MESSAGES
import config
from ..fallbacks import get_fallbacks
from core.request_limiter import is_request_available, increment_count_in_cache

logger = logging.getLogger(__name__)

# State constants for the withdraw flow
AWAIT_WITHDRAW_USERNAME, AWAIT_WITHDRAW_AMOUNT = range(2)

@log_callback_query
async def start_withdraw_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for the withdraw support flow. Asks for username."""
    query = update.callback_query
    user = update.effective_user
    user_id = user.id
    chat_id = update.effective_chat.id
    # --- BƯỚC 1: QUYẾT ĐỊNH HÀNH ĐỘNG TRƯỚC ---
    # Kiểm tra điều kiện mà không thực hiện bất kỳ lệnh `await` nào
    if not is_request_available(user_id, "transaction"):
        # Nếu hết lượt, gọi answer() MỘT LẦN DUY NHẤT để hiển thị pop-up.
        await query.answer(
            text=RESPONSE_MESSAGES["out_of_requests_trans"],
            show_alert=True
        )
        try:
            await query.delete_message()
        except Exception as e:
            logger.info(f"Không thể xóa tin nhắn trong start_withdraw_flow: {e}")

        try:
            text = RESPONSE_MESSAGES["welcome_message"]
            keyboard = keyboards.create_main_menu_markup()

            sent_message = await context.bot.send_photo(
                chat_id=chat_id,
                photo=config.START_IMAGE_FILE_ID,
                caption=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN_V2
            )


            await helpers.cleanup_conversation_messages(context, chat_id=chat_id)

            context.user_data.clear()
            helpers.add_message_to_cleanup_list( context, sent_message)

        except Exception as e:
            logger.error(f"Lỗi khi gửi lại menu chính từ start_withdraw_flow : {e}")
            context.user_data.clear()
        return ConversationHandler.END


    await query.answer()
    helpers.add_message_to_cleanup_list( context, query.message)

    text = RESPONSE_MESSAGES["ask_username_withdraw"]
    sent_message = await helpers.edit_message_safely(
    query=query,
    new_text=text,
    new_reply_markup=keyboards.create_back_to_transaction_menu_markup(),
    parse_mode=ParseMode.MARKDOWN_V2
    )
    helpers.add_message_to_cleanup_list( context, sent_message)

    return AWAIT_WITHDRAW_USERNAME

async def receive_withdraw_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the username and asks for the amount."""
    user_message = update.message
    helpers.add_message_to_cleanup_list( context, user_message)
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

    text = RESPONSE_MESSAGES["ask_for_amount"]
    send_message = await update.message.reply_text(text,
    reply_markup=keyboards.create_cleanup_keyboard(),
    parse_mode=ParseMode.MARKDOWN_V2
    )
    helpers.add_message_to_cleanup_list(context, send_message)
    return AWAIT_WITHDRAW_AMOUNT

async def receive_withdraw_amount_and_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the amount, sends it to the admin, and ends the conversation."""
    user = update.effective_user
    user_message = update.message
    helpers.add_message_to_cleanup_list( context, user_message)
    game_username = context.user_data.get('game_username', 'Chưa cung cấp')

    try:
        amount = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text(RESPONSE_MESSAGES["invalid_amount"])
        return AWAIT_WITHDRAW_AMOUNT


    final_keyboard = keyboards.create_cleanup_keyboard()
    send_message = await update.message.reply_text(RESPONSE_MESSAGES["amount_received_thanks"], reply_markup=final_keyboard,parse_mode=ParseMode.MARKDOWN_V2)
    helpers.add_message_to_cleanup_list(context, send_message)
    admin_text = (
        f"📝 *Yêu cầu RÚT TIỀN*\\- [{escape_markdown(user.first_name, version=2)}](tg://user?id={user.id})\n"
        f"🎮 ID: `{escape_markdown(game_username, version=2)}`\n Số tiền rút: `{amount}`"
    )
    admin_keyboard = keyboards.create_admin_withdraw_keyboard(user.id)

    try:
        await context.bot.send_message(
            chat_id=config.ID_GROUP_TRANSACTION, # Gửi đến nhóm Nạp/Rút
            text=admin_text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=admin_keyboard # Gửi kèm bàn phím
        )
        increment_count_in_cache(user.id, "transaction")
    except Exception as e:
        logger.error(f"Failed to send WITHDRAW request to admin group for user {user.id}: {e}")

    #context.user_data.clear()
    return ConversationHandler.END

# --- Withdraw Conversation Handler ---
withdraw_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_withdraw_flow, pattern='^transaction_withdraw$')],
    states={
        AWAIT_WITHDRAW_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_withdraw_username)],
        AWAIT_WITHDRAW_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_withdraw_amount_and_end)],
    },
    fallbacks=get_fallbacks(),
    block=False,
    name="withdraw_conversation"
)