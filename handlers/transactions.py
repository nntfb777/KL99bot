import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    CommandHandler
)
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown
import database, config
from texts import RESPONSE_MESSAGES
from .core import back_to_menu_handler, _remove_buttons, cancel
import time # Để tạo request_id duy nhất
import uuid # Hoặc có thể dùng uuid để tạo ID ngẫu nhiên và đảm bảo duy nhất

logger = logging.getLogger(__name__)

# Định nghĩa các trạng thái cho ConversationHandler
(
    AWAIT_DEPOSIT_USERNAME,
    AWAIT_DEPOSIT_IMAGE,
    AWAIT_WITHDRAWAL_USERNAME,
    AWAIT_WITHDRAWAL_AMOUNT,
) = range(4)


async def deposit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.message:
        await _remove_buttons(query)
    
    await query.message.reply_text(RESPONSE_MESSAGES["deposit_ask_username"], parse_mode=ParseMode.MARKDOWN_V2)
    return AWAIT_DEPOSIT_USERNAME

async def process_deposit_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    username = escape_markdown(update.message.text.strip(), version=2)
    
    # Lưu username vào user_data của context
    context.user_data['deposit_username'] = username

    await update.message.reply_text(RESPONSE_MESSAGES["deposit_ask_image"], parse_mode=ParseMode.MARKDOWN_V2)
    return AWAIT_DEPOSIT_IMAGE

async def process_deposit_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    
    if not update.message.photo:
        await update.message.reply_text(RESPONSE_MESSAGES["no_image_provided"], parse_mode=ParseMode.MARKDOWN_V2)
        return AWAIT_DEPOSIT_IMAGE

    photo_file_id = update.message.photo[-1].file_id # Lấy ID của ảnh chất lượng cao nhất
    
    deposit_username = context.user_data.get('deposit_username', 'N/A')
    
    # Tạo một request_id duy nhất cho yêu cầu này
    # Bạn có thể dùng uuid.uuid4().hex hoặc timestamp kết hợp user_id để đảm bảo duy nhất
    request_id = str(uuid.uuid4()) # Sử dụng UUID để đảm bảo tính duy nhất

    try:
        # Ghi yêu cầu ban đầu vào database, bao gồm request_id
        # Hàm này cần được bạn định nghĩa trong database.py
        database.create_deposit_request(
            request_id=request_id,
            user_id=user_id,
            username=deposit_username,
            photo_file_id=photo_file_id,
            status="pending", # Trạng thái ban đầu
            timestamp=int(time.time())
        )
        logger.info(f"Đã tạo yêu cầu nạp tiền {request_id} của user {user_id} trong DB.")

        # Gửi yêu cầu đến nhóm admin
        admin_message = (
            f"*YÊU CẦU NẠP TIỀN MỚI*\n"
            f"👤 Khách: [{escape_markdown(update.effective_user.first_name, version=2)}](tg://user?id={user_id}) (`{user_id}`)\n"
            f"Tên game: `{deposit_username}`\n"
            f"⏳ Trạng thái: Đang chờ xử lý\n"
            f"ID yêu cầu: `{request_id}`" # Thêm ID yêu cầu để dễ tra cứu
        )

        keyboard = [
            [
                InlineKeyboardButton("✅ Duyệt", callback_data=f"admin_response:{request_id}:deposit:approve"),
            ],
            [
                InlineKeyboardButton("❌ Từ chối (Sai ID)", callback_data=f"admin_response:{request_id}:deposit:wrong_id"),
                InlineKeyboardButton("❌ Từ chối (Chuyển khoản thất bại)", callback_data=f"admin_response:{request_id}:deposit:failed_transfer"),
            ],
            [
                InlineKeyboardButton("❌ Từ chối (Sai số tiền)", callback_data=f"admin_response:{request_id}:deposit:wrong_amount"),
                InlineKeyboardButton("❌ Từ chối (Chưa chuyển khoản)", callback_data=f"admin_response:{request_id}:deposit:no_transfer"),
            ],
            [
                InlineKeyboardButton("❌ Từ chối (Bill đã sử dụng)", callback_data=f"admin_response:{request_id}:deposit:duplicate_receipt"),
                InlineKeyboardButton("❌ Từ chối (Lý do khác)", callback_data=f"admin_response:{request_id}:deposit:generic"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        sent_message = await context.bot.send_photo(
            chat_id=config.ID_GROUP_PROMO,
            photo=photo_file_id,
            caption=admin_message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN_V2
        )
        logger.info(f"Yêu cầu nạp tiền của user {user_id} đã được gửi tới admin: {sent_message.message_id}")

        # Cập nhật message_id và chat_id của tin nhắn admin vào database
        # Hàm này cần được bạn định nghĩa trong database.py
        database.update_deposit_request(
            request_id=request_id,
            admin_message_id=sent_message.message_id,
            admin_chat_id=sent_message.chat_id
        )
        logger.info(f"Đã cập nhật message_id admin ({sent_message.message_id}) cho yêu cầu {request_id}.")

        await update.message.reply_text(RESPONSE_MESSAGES["yeu_cau_dang_xu_ly"], parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logger.error(f"Lỗi khi xử lý yêu cầu nạp tiền cho user {user_id}: {e}", exc_info=True)
        await update.message.reply_text(RESPONSE_MESSAGES["error_sending_request"], parse_mode=ParseMode.MARKDOWN_V2)

    # Xóa dữ liệu tạm thời khỏi context.user_data sau khi hoàn tất yêu cầu
    context.user_data.pop('deposit_username', None)
    
    return ConversationHandler.END


async def withdrawal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.message:
        await _remove_buttons(query)

    await query.message.reply_text(RESPONSE_MESSAGES["withdrawal_ask_username"], parse_mode=ParseMode.MARKDOWN_V2)
    return AWAIT_WITHDRAWAL_USERNAME

async def process_withdrawal_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    username = escape_markdown(update.message.text.strip(), version=2)
    
    # Lưu username vào user_data của context
    context.user_data['withdrawal_username'] = username

    await update.message.reply_text(RESPONSE_MESSAGES["withdrawal_ask_amount"], parse_mode=ParseMode.MARKDOWN_V2)
    return AWAIT_WITHDRAWAL_AMOUNT

async def process_withdrawal_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    amount_str = update.message.text.strip()
    
    if not amount_str.isdigit() or int(amount_str) <= 0:
        await update.message.reply_text(RESPONSE_MESSAGES["invalid_amount"], parse_mode=ParseMode.MARKDOWN_V2)
        return AWAIT_WITHDRAWAL_AMOUNT # Vẫn ở trạng thái này cho đến khi nhận được số tiền hợp lệ

    amount = int(amount_str)
    
    withdrawal_username = context.user_data.get('withdrawal_username', 'N/A')

    # Tạo một request_id duy nhất cho yêu cầu này
    request_id = str(uuid.uuid4()) # Sử dụng UUID để đảm bảo tính duy nhất

    try:
        # Ghi yêu cầu ban đầu vào database, bao gồm request_id
        # Hàm này cần được bạn định nghĩa trong database.py
        database.create_withdrawal_request(
            request_id=request_id,
            user_id=user_id,
            username=withdrawal_username,
            amount=amount,
            status="pending", # Trạng thái ban đầu
            timestamp=int(time.time())
        )
        logger.info(f"Đã tạo yêu cầu rút tiền {request_id} của user {user_id} trong DB.")

        # Gửi yêu cầu đến nhóm admin
        admin_message = (
            f"*YÊU CẦU RÚT TIỀN MỚI*\n"
            f"👤 Khách: [{escape_markdown(update.effective_user.first_name, version=2)}](tg://user?id={user_id}) (`{user_id}`)\n"
            f"Tên game: `{withdrawal_username}`\n"
            f"Số tiền: `{amount:,}` VNĐ\n"
            f"⏳ Trạng thái: Đang chờ xử lý\n"
            f"ID yêu cầu: `{request_id}`" # Thêm ID yêu cầu để dễ tra cứu
        )

        keyboard = [
            [
                InlineKeyboardButton("✅ Duyệt", callback_data=f"admin_response:{request_id}:withdrawal:approve"),
            ],
            [
                InlineKeyboardButton("❌ Từ chối (Rút thất bại)", callback_data=f"admin_response:{request_id}:withdrawal:failed"),
                InlineKeyboardButton("❌ Từ chối (Sai thông tin)", callback_data=f"admin_response:{request_id}:withdrawal:wrong_info"),
            ],
            [
                InlineKeyboardButton("❌ Từ chối (Không đủ số dư)", callback_data=f"admin_response:{request_id}:withdrawal:insufficient_balance"),
                InlineKeyboardButton("❌ Từ chối (Đang có yêu cầu nạp)", callback_data=f"admin_response:{request_id}:withdrawal:pending_deposit"),
            ],
            [
                InlineKeyboardButton("❌ Từ chối (Chưa đủ vòng cược)", callback_data=f"admin_response:{request_id}:withdrawal:turnover"),
                InlineKeyboardButton("❌ Từ chối (Lý do khác)", callback_data=f"admin_response:{request_id}:withdrawal:generic"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        sent_message = await context.bot.send_message(
            chat_id=config.ID_GROUP_PROMO,
            text=admin_message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN_V2
        )
        logger.info(f"Yêu cầu rút tiền của user {user_id} đã được gửi tới admin: {sent_message.message_id}")

        # Cập nhật message_id và chat_id của tin nhắn admin vào database
        # Hàm này cần được bạn định nghĩa trong database.py
        database.update_withdrawal_request(
            request_id=request_id,
            admin_message_id=sent_message.message_id,
            admin_chat_id=sent_message.chat_id
        )
        logger.info(f"Đã cập nhật message_id admin ({sent_message.message_id}) cho yêu cầu {request_id}.")


        await update.message.reply_text(RESPONSE_MESSAGES["yeu_cau_dang_xu_ly"], parse_mode=ParseMode.MARKDOWN_V2)
    except Exception as e:
        logger.error(f"Lỗi khi xử lý yêu cầu rút tiền cho user {user_id}: {e}", exc_info=True)
        await update.message.reply_text(RESPONSE_MESSAGES["error_sending_request"], parse_mode=ParseMode.MARKDOWN_V2)

    # Xóa dữ liệu tạm thời khỏi context.user_data sau khi hoàn tất yêu cầu
    context.user_data.pop('withdrawal_username', None)

    return ConversationHandler.END


# Conversation handler cho Nạp tiền
deposit_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(deposit_callback, pattern='^deposit$')],
    states={
        AWAIT_DEPOSIT_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_deposit_username)],
        AWAIT_DEPOSIT_IMAGE: [MessageHandler(filters.PHOTO & ~filters.COMMAND, process_deposit_image)],
    },
    fallbacks=[
        CallbackQueryHandler(back_to_menu_handler, pattern='^back_to_menu$'),
        CommandHandler('cancel', cancel)
    ]
)

# Conversation handler cho Rút tiền
withdrawal_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(withdrawal_callback, pattern='^withdrawal$')],
    states={
        AWAIT_WITHDRAWAL_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_withdrawal_username)],
        AWAIT_WITHDRAWAL_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_withdrawal_amount)],
    },
    fallbacks=[
        CallbackQueryHandler(back_to_menu_handler, pattern='^back_to_menu$'),
        CommandHandler('cancel', cancel)
    ]
)
