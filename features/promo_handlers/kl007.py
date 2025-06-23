# features/promo_handlers/kl007.py

import logging
from telegram import Update
from telegram.ext import (
    ConversationHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from telegram.helpers import escape_markdown
from telegram.constants import ParseMode

from core import database
from utils import keyboards, helpers
from texts import PROMO_TEXT_KL007, RESPONSE_MESSAGES, YESTERDAY_DMY
from features.common_handlers import cancel
import config

logger = logging.getLogger(__name__)

# States
AGREE_TERMS, RECEIVE_USERNAME = range(2)

async def start_kl007(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Shows KL007 promo details and asks for agreement."""
    query = update.callback_query
    await query.answer()

    context.user_data['promo_code'] = 'KL007'
    keyboard = keyboards.create_agree_keyboard('KL007')

    # Assuming we are editing a message with a photo caption
    try:
        await query.edit_message_caption(
            caption=PROMO_TEXT_KL007,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception:
        # Fallback if the original message was text-only
        await query.edit_message_text(
            text=PROMO_TEXT_KL007,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    return AGREE_TERMS

async def ask_for_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Asks for the user's game username after they agree."""
    query = update.callback_query
    await query.answer()

    new_caption = RESPONSE_MESSAGES["ask_username_kl007"]

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
    promo_code = context.user_data.get('promo_code', 'KL007')

    # Add claim to the database queue
    claim_id = database.add_promo_claim(
        user_id=user.id,
        promo_code=promo_code,
        game_username=game_username
    )
    logger.info(f"User {user.id} created claim {claim_id} for {promo_code}.")

    # Format the message for the admin group
    admin_text = (
        f"Yêu cầu {escape_markdown(promo_code, version=2)} UID:{user.id} \\- [{escape_markdown(user.first_name, version=2)}](tg://user?id={user.id})\n"
        f"ID: `{escape_markdown(game_username, version=2)}`\n"
        f"NGÀY CÓ VÉ: {YESTERDAY_DMY}"
    )

    admin_keyboard = keyboards.create_admin_promo_buttons(claim_id, user.id, 'KL007')

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
        logger.error(f"Failed to send KL007 claim {claim_id} to admin group: {e}", exc_info=True)
        await update.message.reply_text(RESPONSE_MESSAGES["error_sending_request"])

    context.user_data.clear()
    return ConversationHandler.END

# Build the conversation handler
kl007_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_kl007, pattern='^promo_KL007$')],
    states={
        AGREE_TERMS: [CallbackQueryHandler(ask_for_username, pattern='^agree_terms:KL007$')],
        RECEIVE_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_username)],
    },
    fallbacks=[CallbackQueryHandler(cancel, pattern='^cancel$')],
    map_to_parent={
        ConversationHandler.END: ConversationHandler.END
    }
)