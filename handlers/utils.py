# Tệp: handlers/utils.py

from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown

# Lấy ID của nhóm chat
async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    escaped_chat_id = escape_markdown(str(chat_id), version=2)
    await update.message.reply_text(f"ID của nhóm chat này là: `{escaped_chat_id}`", parse_mode=ParseMode.MARKDOWN_V2)

# Lấy File ID của ảnh
async def get_file_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message and update.message.photo:
        photo_id = update.message.photo[-1].file_id
        escaped_photo_id = escape_markdown(photo_id, version=2)
        await update.message.reply_text(
            f"File ID của ảnh này là:\n`{escaped_photo_id}`",
            parse_mode=ParseMode.MARKDOWN_V2
        )