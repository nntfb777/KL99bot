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
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown

from utils import helpers, keyboards
from texts import RESPONSE_MESSAGES
import config
from features.common_handlers import show_main_menu

logger = logging.getLogger(__name__)

# State constants for the deposit flow
AWAIT_DEPOSIT_USERNAME, AWAIT_DEPOSIT_RECEIPT = range(2)

async def start_deposit_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for the deposit support flow. Asks for username."""
    query = update.callback_query
    await query.answer()

    text = RESPONSE_MESSAGES["ask_username_deposit"]
    await helpers.edit_message_safely(query, text, keyboards.create_cancel_keyboard(), ParseMode.MARKDOWN_V2)
    return AWAIT_DEPOSIT_USERNAME

async def receive_deposit_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the username and asks for the receipt."""
    context.user_data['game_username'] = update.message.text.strip()

    text = RESPONSE_MESSAGES["ask_for_receipt"]
    await update.message.reply_text(text)
    return AWAIT_DEPOSIT_RECEIPT

async def receive_deposit_receipt_and_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the receipt, sends it to the admin, and ends the conversation."""
    user = update.effective_user
    game_username = context.user_data.get('game_username', 'Chưa cung cấp')
    photo_id = update.message.photo[-1].file_id

    await update.message.reply_text(RESPONSE_MESSAGES["receipt_received_thanks"], reply_markup=keyboards.create_back_to_main_menu_markup())

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
    except Exception as e:
        logger.error(f"Failed to send DEPOSIT request to admin group: {e}")

    context.user_data.clear()
    return ConversationHandler.END

# --- Deposit Conversation Handler ---
deposit_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_deposit_flow, pattern='^transaction_deposit$')],
    states={
        AWAIT_DEPOSIT_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_deposit_username)],
        AWAIT_DEPOSIT_RECEIPT: [MessageHandler(filters.PHOTO, receive_deposit_receipt_and_end)],
    },
    fallbacks=[CallbackQueryHandler(show_main_menu, pattern='^back_to_main_menu$')],
    block=False,
    name="deposit_conversation"
)