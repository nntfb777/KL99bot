# Tệp: handlers/core.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import ContextTypes, ConversationHandler # Đảm bảo ConversationHandler được import
from texts import RESPONSE_MESSAGES # Đảm bảo bạn có file texts.py và các keys cần thiết
import database # Cần import database để sử dụng add_or_update_user trong hàm start

logger = logging.getLogger(__name__)

# Hàm hủy hội thoại
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Hủy cuộc trò chuyện hiện tại và thông báo cho người dùng."""
    user = update.effective_user
    logger.info("Người dùng %s đã hủy cuộc trò chuyện.", user.first_name)
    
    # Xóa tất cả các dữ liệu tạm thời của người dùng liên quan đến conversation hiện tại
    # Điều này quan trọng để đảm bảo không có dữ liệu cũ ảnh hưởng đến các tương tác sau
    context.user_data.clear()

    message_text = RESPONSE_MESSAGES.get("cancel_message", "Hành động đã bị hủy.")

    if update.callback_query:
        await update.callback_query.answer()
        # Cố gắng chỉnh sửa tin nhắn, nếu không thành công (ví dụ: đã quá cũ), gửi tin nhắn mới
        try:
            await update.callback_query.edit_message_text(text=message_text)
        except Exception as e:
            logger.warning(f"Không thể chỉnh sửa tin nhắn khi hủy: {e}")
            await update.callback_query.message.reply_text(text=message_text)
    else:
        await update.message.reply_text(text=message_text)
        
    return ConversationHandler.END

# Hàm tiện ích để xóa các nút inline từ tin nhắn
async def _remove_buttons(query: CallbackQuery) -> None:
    """Xóa các nút inline từ một tin nhắn CallbackQuery đã nhận."""
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception as e:
        logger.warning(f"Không thể xóa nút inline từ tin nhắn: {e}")

# Hàm hiển thị menu chính
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Hiển thị menu chính của bot cho người dùng."""
    keyboard = [
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("deposit_button", "Nạp tiền"), callback_data='deposit')],
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("withdraw_button", "Rút tiền"), callback_data='withdraw')],
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("promo_button", "Khuyến mãi"), callback_data='khuyen_mai')],
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("share_task_button", "Chia sẻ nhận thưởng"), callback_data='share_task')], 
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("check_in_button", "Điểm danh"), callback_data='check_in')],
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("faq_button", "FAQ"), callback_data='faq')] 
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_message = RESPONSE_MESSAGES.get("welcome_back", "Chào mừng bạn trở lại! Vui lòng chọn một tùy chọn:")

    # Xác định cách gửi tin nhắn (chỉnh sửa hay gửi mới)
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        try:
            await query.edit_message_text(
                text=welcome_message,
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.warning(f"Không thể chỉnh sửa tin nhắn để hiển thị menu chính: {e}")
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=welcome_message,
                reply_markup=reply_markup
            )
    elif update.message: # Nếu đến từ một Command (ví dụ: /start) hoặc MessageHandler
        await update.message.reply_text(
            RESPONSE_MESSAGES.get("welcome_message", "Chào mừng bạn đến với bot!"),
            reply_markup=reply_markup
        )
    return ConversationHandler.END # Kết thúc mọi cuộc trò chuyện đang hoạt động và hiển thị menu chính

# Hàm start (được gọi khi người dùng gõ /start)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Xử lý lệnh /start, chào mừng người dùng và hiển thị menu chính."""
    user = update.effective_user
    logger.info(f"Người dùng {user.id} ({user.first_name}) đã bắt đầu bot.")

    # Đảm bảo user được lưu vào database.
    # Hàm này cần được định nghĩa trong database.py.
    database.add_or_update_user(user.id, user.first_name, user.username)

    # Chuyển hướng đến hàm hiển thị menu chính
    return await show_main_menu(update, context)

# Hàm back_to_menu_handler (dùng làm fallback để quay lại menu chính từ các conversation khác)
async def back_to_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Xử lý hành động quay lại menu chính từ các cuộc trò chuyện con."""
    # Chỉ trả lời callback query nếu nó tồn tại để tránh lỗi
    if update.callback_query:
        query = update.callback_query
        await query.answer()
    
    # Xóa tất cả các dữ liệu tạm thời của người dùng liên quan đến conversation bị hủy.
    context.user_data.clear() 

    # Gọi hàm hiển thị menu chính để người dùng có thể tiếp tục.
    return await show_main_menu(update, context)

# Hàm xử lý lỗi
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ghi log lỗi và thông báo cho người dùng/admin."""
    logger.error("Đã xảy ra ngoại lệ khi xử lý một update:", exc_info=context.error)
    # Gửi tin nhắn lỗi chung cho người dùng nếu có thể
    if update and update.effective_message:
        await update.effective_message.reply_text(RESPONSE_MESSAGES.get("error_generic", "Đã xảy ra lỗi không mong muốn. Vui lòng thử lại sau."))