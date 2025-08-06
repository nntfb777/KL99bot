# utils/helpers.py

import logging
import pytz
from telegram import Bot
from telegram import CallbackQuery, Update, InlineKeyboardMarkup, InputMediaPhoto, Message
from telegram.ext import ContextTypes
import telegram
from telegram.constants import ParseMode
from datetime import datetime, timedelta
from telegram.error import BadRequest
import re
from utils import keyboards
from texts import RESPONSE_MESSAGES
import config


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


async def edit_message_safely(
    query: telegram.CallbackQuery,
    new_text: str,
    new_reply_markup: InlineKeyboardMarkup = None,
    new_photo_file_id: str = None, # <--- THAM SỐ MỚI
    parse_mode: str = ParseMode.MARKDOWN_V2
) -> Message | None:
    """
    Chỉnh sửa một tin nhắn một cách an toàn. Có khả năng thay đổi cả hình ảnh.
    - Nếu new_photo_file_id được cung cấp, nó sẽ thay đổi cả ảnh và caption.
    - Nếu không, nó sẽ chỉ edit text hoặc caption như cũ.
    """
    if not query or not query.message:
        logger.warning("edit_message_safely được gọi mà không có query hoặc message hợp lệ.")
        return None

    try:
        # TRƯỜNG HỢP 1: CẦN THAY ĐỔI HÌNH ẢNH
        if new_photo_file_id:
            logging.info(f"Đang cố gắng sử dụng file_id: '{new_photo_file_id}'")
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
            # Bỏ qua lỗi khi nội dung không thay đổi, không cần log
            pass
        elif "Canceled by new editmessagemedia request" in str(e):
            # Bỏ qua lỗi do người dùng bấm nút quá nhanh
            logging.warning(f"Edit message was canceled by a new request. (User clicked too fast). Error: {e}")
        else:
            # Ghi log các lỗi BadRequest khác
            logging.error(f"Lỗi BadRequest khi chỉnh sửa tin nhắn: {e}")
    except Exception as e:
        logger.error(f"Lỗi không xác định khi chỉnh sửa tin nhắn: {e}")


def add_message_to_cleanup_list(context: ContextTypes.DEFAULT_TYPE, message: Message):
    """Lưu message_id vào danh sách dọn dẹp trong bot_data theo user_id."""
    if not message:
        return

    user_id = message.chat_id # Giả định chat_id là user_id trong chat riêng

    # Khởi tạo dict cho user nếu chưa có
    if user_id not in context.bot_data:
        context.bot_data[user_id] = {}

    # Khởi tạo danh sách messages_to_delete nếu chưa có
    if 'messages_to_delete' not in context.bot_data[user_id]:
        context.bot_data[user_id]['messages_to_delete'] = []

    # Thêm message_id vào danh sách
    context.bot_data[user_id]['messages_to_delete'].append(message.message_id)


async def cleanup_conversation_messages(context: ContextTypes.DEFAULT_TYPE, chat_id: int): # Thêm tham số chat_id
    """Xóa tất cả các tin nhắn trong danh sách dọn dẹp cho một chat_id cụ thể."""
    if 'messages_to_delete' in context.user_data:
        # chat_id giờ đây được truyền trực tiếp vào, không cần lấy từ context._chat_id nữa

        # Tạo một bản sao của danh sách để lặp qua, tránh lỗi khi sửa đổi trong lúc lặp
        message_ids_to_process = list(context.user_data['messages_to_delete'])

        for message_id in message_ids_to_process:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            except Exception as e:
                logger.info(f"Không thể xóa message_id {message_id} trong chat {chat_id}: {e}")

        # Sau khi hoàn tất, xóa key đi
        # Dùng pop để an toàn hơn
        context.user_data.pop('messages_to_delete', None)

async def delete_message_safely(bot: Bot, chat_id: int, message_id: int):
    """
    Xóa một tin nhắn và bỏ qua lỗi nếu tin nhắn không tồn tại hoặc không thể xóa.
    """
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except BadRequest as e:
        # Bỏ qua các lỗi thường gặp khi xóa tin nhắn
        if "message to delete not found" in str(e) or "message can't be deleted" in str(e):
            logger.warning(f"Could not delete message {message_id} in chat {chat_id}: {e}")
        else:
            # Ghi log các lỗi BadRequest khác
            logger.error(f"Error deleting message {message_id} in chat {chat_id}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error deleting message {message_id} in chat {chat_id}: {e}")


def is_valid_username(username: str) -> bool:
    """
    Kiểm tra xem tên đăng nhập có tuân thủ các quy tắc hay không.

    Quy tắc:
    - Từ 2 đến 15 ký tự.
    - Phải bắt đầu bằng một chữ cái.
    - Chỉ chứa chữ cái (a-z, A-Z), số (0-9), và dấu gạch dưới (_).

    Args:
        username (str): Tên đăng nhập cần kiểm tra.

    Returns:
        bool: True nếu hợp lệ, False nếu không.
    """
    if not username:
        return False

    # ^                  -> Bắt đầu chuỗi
    # [a-zA-Z]         -> Ký tự đầu tiên phải là chữ cái (hoa hoặc thường)
    # \w{1,14}         -> Theo sau là từ 1 đến 14 ký tự "word"
    #                      (\w bao gồm chữ cái, số, và gạch dưới)
    # $                  -> Kết thúc chuỗi
    # Tổng cộng: 1 + (1 đến 14) = 2 đến 15 ký tự.
    pattern = r"^[a-zA-Z]\w{1,14}$"

    # re.match() sẽ trả về một đối tượng nếu khớp, None nếu không.
    # bool() sẽ chuyển đổi kết quả đó thành True/False.
    return bool(re.match(pattern, username))


async def delban_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    (Admin only) Xóa tất cả các yêu cầu đang chờ trong promo_claims của một user.
    Cú pháp: /delban <USER_ID>
    """
    # 1. KIỂM TRA QUYỀN ADMIN - Rất quan trọng!
    if update.effective_user.id not in config.ADMIN_IDS:
        return # Bỏ qua trong im lặng nếu không phải admin

    # 2. KIỂM TRA CÚ PHÁP LỆNH
    if not context.args or len(context.args) != 1:
        await update.message.reply_text(
            "Cú pháp sai\\. Dùng: `/delban <USER_ID>`",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return

    # 3. PHÂN TÍCH USER_ID
    try:
        target_user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("USER\\_ID phải là một con số\\.", parse_mode=ParseMode.MARKDOWN_V2)
        return

    # 4. GỌI HÀM DATABASE VÀ LẤY KẾT QUẢ
    deleted_count = database.clear_all_claims_for_user(target_user_id)

    # 5. GỬI PHẢN HỒI CHO ADMIN
    admin_name = update.effective_user.first_name
    if deleted_count > 0:
        reply_text = (
            f"✅ Admin *{escape_markdown(admin_name, version=2)}* đã xóa thành công "
            f"*{deleted_count}* yêu cầu đang chờ của User ID `{target_user_id}`\\."
        )
    else:
        reply_text = (
            f"ℹ️ Không tìm thấy yêu cầu nào đang chờ của User ID `{target_user_id}` để xóa\\."
        )

    await update.message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN_V2)

async def send_main_menu_new(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    """
    Gửi một tin nhắn menu chính hoàn toàn mới (ảnh + caption + bàn phím).
    Hàm này được dùng bởi unified_cleanup_handler.

    Args:
        context: Context của bot.
        chat_id: ID của cuộc trò chuyện cần gửi tin nhắn đến.

    Returns:
        Message: Đối tượng Message của tin nhắn đã gửi, hoặc None nếu thất bại.
    """
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
        return sent_message
    except Exception as e:
        logger.error(f"Lỗi khi gửi menu chính mới cho chat_id {chat_id}: {e}", exc_info=True)
        return None