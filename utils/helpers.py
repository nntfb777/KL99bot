# utils/helpers.py

import logging
from datetime import datetime
import pytz
from telegram import CallbackQuery, Update
from telegram.ext import ContextTypes
import telegram

logger = logging.getLogger(__name__)
TIMEZONE = pytz.timezone('Asia/Ho_Chi_Minh')

def get_current_time_str() -> str:
    """Returns the current time in 'HH:MM:SS DD/MM/YYYY' format."""
    return datetime.now(TIMEZONE).strftime('%H:%M:%S %d/%m/%Y')

async def remove_buttons(update: Update):
    """Edits the message to remove its inline keyboard."""
    try:
        if update.callback_query:
            query = update.callback_query
            await query.answer()
            await query.edit_message_reply_markup(reply_markup=None)
    except telegram.error.BadRequest as e:
        if "message is not modified" not in str(e).lower():
            logger.warning(f"Error removing buttons (known issue, often harmless): {e}")
    except Exception as e:
        logger.error(f"Unexpected error while removing buttons: {e}", exc_info=True)