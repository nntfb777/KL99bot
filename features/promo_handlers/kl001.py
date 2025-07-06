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
from .common import PROMO_FALLBACKS
from telegram.helpers import escape_markdown
from telegram.constants import ParseMode

from core import database
from utils import keyboards, helpers
from texts import PROMO_TEXT_KL001, RESPONSE_MESSAGES
from features.common_handlers import cancel
import config

logger = logging.getLogger(__name__)

# States
AGREE_TERMS, RECEIVE_USERNAME = range(2)

async def start_kl001(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Shows KL001 promo details and asks for agreement."""
    query = update.callback_query
    await query.answer()

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

    if query.message.caption:
        await query.edit_message_caption(
            caption=new_caption,
            reply_markup=keyboards.create_cancel_keyboard()
        )
    else:
        await query.edit_message_text(
            text=new_caption,
            reply_markup=keyboards.create_cancel_keyboard()
        )
    return RECEIVE_USERNAME


async def receive_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives username, adds claim to DB, and notifies admin."""
    user = update.effective_user
    game_username = update.message.text.strip()
    promo_code = context.user_data.get('promo_code', 'KL001')

    # Add claim to the database queue
    claim_id = database.add_promo_claim(
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

    try:
        await context.bot.send_message(
            chat_id=config.ID_GROUP_PROMO,
            text=admin_text,
            reply_markup=admin_keyboard,
            parse_mode=ParseMode.MARKDOWN_V2
        )
        await update.message.reply_text(
            RESPONSE_MESSAGES["yeu_cau_dang_xu_ly"],
            reply_markup=keyboards.create_back_to_main_menu_markup()
        )
    except Exception as e:
        logger.error(f"Failed to send KL001 claim {claim_id} to admin group: {e}")
        await update.message.reply_text(RESPONSE_MESSAGES["error_sending_request"])

    context.user_data.clear()
    return ConversationHandler.END

# Build the conversation handler
kl001_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_kl001, pattern='^promo_KL001$')],
    states={
        AGREE_TERMS: [CallbackQueryHandler(ask_for_username, pattern='^agree_terms:KL001$')],
        RECEIVE_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_username)],
    },
    fallbacks=PROMO_FALLBACKS,  # <--- SỬ DỤNG FALLBACK CHUNG
    block=False,                # <--- THÊM THAM SỐ NÀY
    per_message=False,
    name="kl001_conversation"
)