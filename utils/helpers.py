# utils/helpers.py

import logging
import pytz
from telegram import CallbackQuery, Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import telegram
from telegram.constants import ParseMode
from telegram import InlineKeyboardMarkup, InputMediaPhoto
from datetime import datetime, timedelta



logger = logging.getLogger(__name__)
TIMEZONE = pytz.timezone('Asia/Ho_Chi_Minh')

def get_current_time_str() -> str:
    """Returns the current time in 'HH:MM:SS DD/MM/YYYY' format."""
    return datetime.now(TIMEZONE).strftime('%H:%M:%S %d/%m/%Y')

def get_yesterday_dmy_str() -> str:
    """
    Lấy ngày hôm qua dựa trên múi giờ hệ thống (UTC-4 / GMT+4)
    và trả về dưới dạng chuỗi 'DD/MM/YYYY'.
    """
    try:
        target_timezone = pytz.timezone('Etc/GMT+4')
        yesterday = datetime.now(target_timezone) - timedelta(days=1)
        return yesterday.strftime('%d/%m/%Y')
    except Exception as e:
        logger.error(f"Lỗi khi tính toán ngày hôm qua: {e}")
        return "ngày hôm qua"

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



async def edit_message_safely(
    query: telegram.CallbackQuery,
    new_text: str,
    new_reply_markup: InlineKeyboardMarkup = None,
    new_photo_file_id: str = None, # <--- THAM SỐ MỚI
    parse_mode: str = ParseMode.MARKDOWN_V2
):
    """
    Chỉnh sửa một tin nhắn một cách an toàn. Có khả năng thay đổi cả hình ảnh.
    - Nếu new_photo_file_id được cung cấp, nó sẽ thay đổi cả ảnh và caption.
    - Nếu không, nó sẽ chỉ edit text hoặc caption như cũ.
    """
    if not query:
        logger.warning("edit_message_safely được gọi mà không có query.")
        return

    try:
        # TRƯỜNG HỢP 1: CẦN THAY ĐỔI HÌNH ẢNH
        if new_photo_file_id:
            media = InputMediaPhoto(media=new_photo_file_id, caption=new_text, parse_mode=parse_mode)
            await query.edit_message_media(media=media, reply_markup=new_reply_markup)

        # TRƯỜNG HỢP 2: CHỈ THAY ĐỔI TEXT/CAPTION (như cũ)
        else:
            if query.message.caption is not None:
                await query.edit_message_caption(
                    caption=new_text,
                    reply_markup=new_reply_markup,
                    parse_mode=parse_mode
                )
            else:
                await query.edit_message_text(
                    text=new_text,
                    reply_markup=new_reply_markup,
                    parse_mode=parse_mode
                )

    except telegram.error.BadRequest as e:
        if "Message is not modified" in str(e):
            pass # Bỏ qua nếu không có gì thay đổi
        else:
            logger.error(f"Lỗi BadRequest khi chỉnh sửa tin nhắn: {e}")
    except Exception as e:
        logger.error(f"Lỗi không xác định khi chỉnh sửa tin nhắn: {e}")
    finally:
        # Luôn trả lời callback để tắt loading
        await query.answer()