# features/get_id_handlers.py

import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)


async def get_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Trả về ID của người dùng/nhóm chat.
    Nếu reply vào một tin nhắn có media (ảnh, video, file...), sẽ trả về cả file_id.
    """
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Tin nhắn mà lệnh /id đã reply vào
    replied_message = update.message.reply_to_message

    # Chuẩn bị nội dung tin nhắn phản hồi
    text = (
        f"Thông tin ID:\n"
        f"  \\- Chat ID: `{chat_id}`\n"
        f"  \\- User ID của bạn: `{user_id}`"
    )

    file_id = None
    file_type = "N/A"

    if replied_message:
        if replied_message.photo:
            file_id = replied_message.photo[-1].file_id
            file_type = "Photo"
        elif replied_message.video:
            file_id = replied_message.video.file_id
            file_type = "Video"
        elif replied_message.document:
            file_id = replied_message.document.file_id
            file_type = "Document"
        elif replied_message.audio:
            file_id = replied_message.audio.file_id
            file_type = "Audio"
        elif replied_message.sticker:
            file_id = replied_message.sticker.file_id
            file_type = "Sticker"

        if file_id:
            logger.info(f"Command /id on a message with media. Type: {file_type}, File ID: {file_id}")
            text += (
                f"\n\nThông tin Media được Reply:\n"
                f"  \\- Loại: {file_type}\n"
                f"  \\- File ID: `{file_id}`"
            )

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2)