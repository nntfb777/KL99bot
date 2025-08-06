# features/common_handlers.py
import telegram
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, CallbackQueryHandler
from telegram.helpers import escape_markdown
from telegram.constants import ParseMode
from utils.decorators import log_callback_query
from core import database
from utils import helpers, keyboards, analytics
from texts import RESPONSE_MESSAGES
import config
from telegram.error import BadRequest
from core.referral_processor import REFERRAL_QUEUE

logger = logging.getLogger(__name__)

@log_callback_query
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the /start command and referrals."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    chat = update.effective_chat
    user_message = update.message
    helpers.add_message_to_cleanup_list( context, user_message)
    logger.info(f"Command /start from user: {user.id} ({user.username}) in chat {chat_id}")
    if not chat:
        logger.warning("Lệnh /start được gọi nhưng không tìm thấy effective_chat.")
        return ConversationHandler.END
    old_messages_to_delete = context.user_data.pop('messages_to_delete', [])

    if user_message:
        old_messages_to_delete.append(user_message.message_id)
    context.user_data.clear()
    text = RESPONSE_MESSAGES["welcome_message"]
    keyboard = keyboards.create_main_menu_markup()
    sent_message = await update.message.reply_photo(
        photo=config.START_IMAGE_FILE_ID, caption=text,
        reply_markup=keyboard, parse_mode=ParseMode.MARKDOWN_V2
    )
    helpers.add_message_to_cleanup_list(context, sent_message)

    task_data = (
        'CREATE_USER_AND_PROCESS_REF',
        {
            'user': user.to_dict(),
            'context_args': context.args
        }
    )
    await REFERRAL_QUEUE.put(task_data)

    logger.info(f"User {user.id} /start command queued for background processing.")

        #elif referrer and referrer['user_id'] == user.id:
            #await update.message.reply_text(RESPONSE_MESSAGES["cannot_self_refer"]) # Sửa lại key nếu cần

    return ConversationHandler.END


async def unified_cleanup_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handler "Tất cả trong một" để dọn dẹp và hiển thị menu chính.
    PHIÊN BẢN CUỐI CÙNG: Đã được trang bị cơ chế chống double-click.
    """
    query = update.callback_query
    user = update.effective_user

    if not user or not query:
        # Nếu không có user hoặc query, không có gì để làm
        return ConversationHandler.END

    # <<<<<<<<< LOGIC "BẢO VỆ" BẮT ĐẦU TẠI ĐÂY >>>>>>>>>
    # 1. Trả lời query ngay lập tức và một cách an toàn
    try:
        await query.answer()
    except telegram.error.BadRequest as e:
        if "Query is too old" in str(e):
            logger.warning(f"Cleanup handler caught 'Query is too old' for '{query.data}'. Stopping execution.")
            return ConversationHandler.END # Dừng hẳn
        else:
            raise e # Ném các lỗi BadRequest khác

    # 2. Cơ chế khóa chống double-click (tùy chọn nhưng rất tốt)
    lock_key = f"query_lock_{query.id}"
    if context.chat_data.get(lock_key):
        logger.warning(f"Cleanup handler blocked duplicate execution for query_id '{query.id}'.")
        return ConversationHandler.END # Dừng hẳn

    context.chat_data[lock_key] = True
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<

    try:
        # === PHẦN LOGIC CHÍNH CỦA HÀM (GIỮ NGUYÊN) ===
        user_id = user.id
        chat_id = query.message.chat_id
        all_messages_to_delete = set()

        # Nguồn 1: Từ user_data
        all_messages_to_delete.update(context.user_data.pop('messages_to_delete', []))

        # Nguồn 2: Từ bot_data
        if context.bot_data.get(user_id):
            all_messages_to_delete.update(context.bot_data[user_id].pop('messages_to_delete', []))
            if not context.bot_data[user_id]:
                del context.bot_data[user_id]

        # Nguồn 3: Chính tin nhắn chứa nút bấm
        all_messages_to_delete.add(query.message.message_id)

        sent_message = await helpers.send_main_menu_new(context, user.id)

        # Dọn dẹp
        if all_messages_to_delete:
            logger.info(f"Unified Cleanup: Deleting {len(all_messages_to_delete)} messages for user {user_id}.")
            for message_id in all_messages_to_delete:
                if sent_message and message_id == sent_message.message_id:
                    continue
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
                except Exception:
                    pass

        # Dọn dẹp và chuẩn bị cho lần sau
        context.user_data.clear()
        if sent_message:
            helpers.add_message_to_cleanup_list(context, sent_message)

    finally:
        # Mở khóa dù có lỗi hay không
        context.chat_data.pop(lock_key, None)

    return ConversationHandler.END

# Dọn dẹp
    if all_messages_to_delete:
        logger.info(f"Cancel All-in-One: Cleaning up {len(all_messages_to_delete)} messages for user {user_id}.")
        for message_id in all_messages_to_delete:
            if sent_message and message_id == sent_message.message_id:
                continue
            try:
                await context.bot.delete_message(chat_id=user.id, message_id=message_id)
            except Exception:
                pass

    # Dọn dẹp context và chuẩn bị cho lần sau
    context.user_data.clear()
    if sent_message:
        helpers.add_message_to_cleanup_list(context, sent_message) # Hàm này bây giờ nên ghi vào user_data

    return ConversationHandler.END


# Menu Navigation Handlers
@log_callback_query
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: # Không trả về state
    """Chỉ EDIT tin nhắn để hiển thị menu chính (dùng cho điều hướng)."""
    query = update.callback_query

    text = RESPONSE_MESSAGES["welcome_message"]
    keyboard = keyboards.create_main_menu_markup()
    await helpers.edit_message_safely(
        query=query,
        new_text=text,
        new_reply_markup=keyboard,
        new_photo_file_id=config.START_IMAGE_FILE_ID
    )
    return ConversationHandler.END

@log_callback_query
async def show_promo_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Displays the promotions menu."""
    query = update.callback_query


    text = RESPONSE_MESSAGES["choose_promo_message"]
    reply_markup = keyboards.create_promo_menu_markup()

    edited_message = await helpers.edit_message_safely(query, text, reply_markup)
    if edited_message:
        helpers.add_message_to_cleanup_list( context, edited_message)
    return ConversationHandler.END

@log_callback_query
async def show_transaction_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hiển thị menu Nạp/Rút."""
    query = update.callback_query

    text = RESPONSE_MESSAGES["transaction_menu_intro"]
    keyboard = keyboards.create_transaction_menu_markup()
    await helpers.edit_message_safely(
        query=query,
        new_text=text,
        new_reply_markup=keyboard,
        new_photo_file_id=config.TRANS_IMAGE_ID
    )
    return ConversationHandler.END

async def handle_stray_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Xử lý "trong im lặng" các tin nhắn văn bản không mong muốn từ người dùng.
    Chỉ thêm tin nhắn vào danh sách dọn dẹp và không phản hồi gì.
    """
    user_message = update.message
    helpers.add_message_to_cleanup_list( context, user_message)

@log_callback_query
async def show_cskh_warning(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sửa tin nhắn để hiển thị cảnh báo VPN/1.1.1.1 trước khi đến trang CSKH."""
    query = update.callback_query


    # Lấy văn bản cảnh báo từ texts.py (bạn sẽ cần thêm key này)
    text = RESPONSE_MESSAGES.get(
        "cskh_vpn_warning_text",
        "Lưu ý: Nếu quý khách đang sử dụng 1.1.1.1 hoặc VPN, vui lòng tắt ứng dụng trước khi liên hệ CSKH để đảm bảo kết nối ổn định."
    )
    # Tạo bàn phím mới
    keyboard = keyboards.create_cskh_warning_keyboard()

    # Edit tin nhắn hiện tại
    await helpers.edit_message_safely(
        query=query,
        new_text=text,
        new_reply_markup=keyboard,
        # Giữ lại ảnh nền của menu chính để không bị mất
        new_photo_file_id=config.START_IMAGE_FILE_ID
    )
