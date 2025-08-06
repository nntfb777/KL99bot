# features/promo_handlers/kl001.py

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
from telegram.helpers import escape_markdown
from telegram.constants import ParseMode
from utils.decorators import log_callback_query
from core import database
from utils import keyboards, helpers
from texts import PROMO_TEXT_KL001, RESPONSE_MESSAGES
import config
from core.request_limiter import is_request_available, increment_count_in_cache

logger = logging.getLogger(__name__)

# States
AGREE_TERMS, RECEIVE_USERNAME = range(2)

@log_callback_query
async def start_kl001(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Shows KL001 promo details and asks for agreement."""
    query = update.callback_query
    user = update.effective_user
    user_id = user.id
    chat_id = update.effective_chat.id
    # --- BƯỚC 1: QUYẾT ĐỊNH HÀNH ĐỘNG TRƯỚC ---
    # Kiểm tra điều kiện mà không thực hiện bất kỳ lệnh `await` nào
    if not is_request_available(user_id, "promo"):
        # Nếu hết lượt, gọi answer() MỘT LẦN DUY NHẤT để hiển thị pop-up.
        await helpers.edit_message_safely(
            query=query,
            new_text=RESPONSE_MESSAGES["out_of_requests"],
            # Cung cấp nút "Quay lại Menu" để dọn dẹp
            new_reply_markup=keyboards.create_cleanup_keyboard()
        )
        try:
            await query.delete_message()
        except Exception as e:
            logger.info(f"Không thể xóa tin nhắn trong start_KL001: {e}")

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
            helpers.add_message_to_cleanup_list(context, sent_message)

        except Exception as e:
            logger.error(f"Lỗi khi gửi lại menu chính từ start_KL001: {e}")
            context.user_data.clear()
        return ConversationHandler.END




    context.user_data['promo_code'] = 'KL001'
    keyboard = keyboards.create_agree_keyboard('KL001')

    await helpers.edit_message_safely(
        query=query,
        new_text=PROMO_TEXT_KL001,
        new_reply_markup=keyboard,
        new_photo_file_id=config.PROMO_KL001_IMAGE_ID # <--- TRUYỀN ID ẢNH MỚI
    )

    return AGREE_TERMS

async def ask_for_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Asks for the user's game username."""
    query = update.callback_query
    await query.answer()

    new_caption = RESPONSE_MESSAGES["ask_username_kl001_after_agree"]
    keyboard = keyboards.create_back_to_show_promo_menu_markup()

    await helpers.edit_message_safely(
        query=query,
        new_text=new_caption,
        new_reply_markup=keyboard
    )
    return RECEIVE_USERNAME


async def receive_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives username, adds claim to DB, and notifies admin."""
    user = update.effective_user
    user_message = update.message
    helpers.add_message_to_cleanup_list(context, user_message)
    game_username = update.message.text.strip()
    promo_code = context.user_data.get('promo_code', 'KL001')
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
    # Add claim to the database queue
    claim_id = await database.add_promo_claim(
        user_id=user.id,
        promo_code=promo_code,
        game_username=game_username
    )
    logger.info(f"User {user.id} created claim {claim_id} for {promo_code}.")

    # Format the message for the admin group
    admin_text = (
        f"Yêu cầu {escape_markdown(promo_code, version=2)} \\- [{escape_markdown(user.first_name, version=2)}](tg://user?id={user.id})\n"
        f"ID:  `{escape_markdown(game_username, version=2)}`"
    )

    admin_keyboard = keyboards.create_admin_promo_buttons(claim_id, user.id, promo_code)

    final_keyboard = keyboards.create_cleanup_keyboard()

    try:
        await context.bot.send_message(
            chat_id=config.ID_GROUP_PROMO,
            text=admin_text,
            reply_markup=admin_keyboard,
            parse_mode=ParseMode.MARKDOWN_V2
        )
        send_message = await update.message.reply_text(
            RESPONSE_MESSAGES["yeu_cau_dang_xu_ly"],
            reply_markup=final_keyboard,
            parse_mode=ParseMode.MARKDOWN_V2
        )
        helpers.add_message_to_cleanup_list(context, send_message)
        increment_count_in_cache(user.id, "promo")
    except Exception as e:
        logger.error(f"Failed to send KL001 claim {claim_id} to admin group: {e}")
        await update.message.reply_text(RESPONSE_MESSAGES["error_sending_request"])

    #context.user_data.clear()
    return ConversationHandler.END

# Build the conversation handler
kl001_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_kl001, pattern='^promo_KL001$')],
    states={
        AGREE_TERMS: [CallbackQueryHandler(ask_for_username, pattern='^agree_terms:KL001$')],
        RECEIVE_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_username)],
    },
    fallbacks=get_fallbacks(),
    block=False,
    per_message=False,
    name="kl001_conversation"
)