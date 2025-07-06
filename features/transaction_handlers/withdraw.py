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

from utils import helpers, keyboards
from texts import RESPONSE_MESSAGES
import config
from features.common_handlers import show_main_menu

logger = logging.getLogger(__name__)

# State constants for the withdraw flow
AWAIT_WITHDRAW_USERNAME, AWAIT_WITHDRAW_AMOUNT = range(2)

async def start_withdraw_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point for the withdraw support flow. Asks for username."""
    query = update.callback_query
    await query.answer()

    text = RESPONSE_MESSAGES["ask_username_withdraw"]
    await helpers.edit_message_safely(query, text, keyboards.create_cancel_keyboard(), ParseMode.MARKDOWN_V2)
    return AWAIT_WITHDRAW_USERNAME

async def receive_withdraw_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the username and asks for the amount."""
    context.user_data['game_username'] = update.message.text.strip()

    text = RESPONSE_MESSAGES["ask_for_amount"]
    await update.message.reply_text(text)
    return AWAIT_WITHDRAW_AMOUNT

async def receive_withdraw_amount_and_end(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the amount, sends it to the admin, and ends the conversation."""
    user = update.effective_user
    game_username = context.user_data.get('game_username', 'Chưa cung cấp')

    try:
        amount = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text(RESPONSE_MESSAGES["invalid_amount"])
        return AWAIT_WITHDRAW_AMOUNT

    await update.message.reply_text(RESPONSE_MESSAGES["amount_received_thanks"], reply_markup=keyboards.create_back_to_main_menu_markup())

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
    except Exception as e:
        logger.error(f"Failed to send WITHDRAW request to admin group for user {user.id}: {e}")

    context.user_data.clear()
    return ConversationHandler.END

# --- Withdraw Conversation Handler ---
withdraw_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_withdraw_flow, pattern='^transaction_withdraw$')],
    states={
        AWAIT_WITHDRAW_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_withdraw_username)],
        AWAIT_WITHDRAW_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_withdraw_amount_and_end)],
    },
    fallbacks=[CallbackQueryHandler(show_main_menu, pattern='^back_to_main_menu$')],
    block=False,
    name="withdraw_conversation"
)