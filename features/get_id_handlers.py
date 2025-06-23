# features/get_id_handlers.py

import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

logger = logging.getLogger(__name__)

async def get_chat_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends the chat ID."""
    chat_id = update.effective_chat.id
    escaped_chat_id = escape_markdown(str(chat_id), version=2)
    await update.message.reply_text(
        f"ID của nhóm chat này là: `{escaped_chat_id}`",
        parse_mode='MarkdownV2'
    )

async def get_file_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends the file_id of a received photo."""
    if update.message and update.message.photo:
        photo_id = update.message.photo[-1].file_id
        file_size = update.message.photo[-1].file_size
        logger.info(f"Received photo. File ID: {photo_id}, Size: {file_size} bytes")

        escaped_photo_id = escape_markdown(photo_id, version=2)
        await update.message.reply_text(
            f"File ID của ảnh này là:\n`{escaped_photo_id}`",
            parse_mode='MarkdownV2'
        )