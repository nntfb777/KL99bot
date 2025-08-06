# features/promo_handlers/kl007.py

import logging
from telegram import Update
from telegram.ext import (
    ConversationHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
import telegram
from ..fallbacks import get_fallbacks
from telegram.helpers import escape_markdown
from telegram.constants import ParseMode
from core import database
from utils import keyboards, helpers, gspread_api
from texts import PROMO_TEXT_KL007, RESPONSE_MESSAGES
import config
from datetime import datetime
import pytz
from utils.decorators import log_callback_query
from core.request_limiter import is_request_available, increment_count_in_cache
import asyncio
logger = logging.getLogger(__name__)

# States
AGREE_TERMS, RECEIVE_USERNAME, AWAITING_USER_ACK = range(3)


@log_callback_query
async def start_kl007(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Shows KL007 promo details and asks for agreement."""
    query = update.callback_query
    user = update.effective_user
    user_id = user.id
    # Kiểm tra điều kiện mà không thực hiện bất kỳ lệnh `await` nào
    if not is_request_available(user_id, "promo"):
        # Nếu hết lượt, gọi answer() MỘT LẦN DUY NHẤT để hiển thị pop-up.
        await helpers.edit_message_safely(
            query=query,
            new_text=RESPONSE_MESSAGES["out_of_requests"],
            # Cung cấp nút "Quay lại Menu" để dọn dẹp
            new_reply_markup=keyboards.create_cleanup_keyboard()
        )
        return ConversationHandler.END

    helpers.add_message_to_cleanup_list(context, query.message)
    tz_vietnam = pytz.timezone('Asia/Ho_Chi_Minh')
    now_vietnam = datetime.now(tz_vietnam)
    current_hour = now_vietnam.hour

    if current_hour == 11:
        text = RESPONSE_MESSAGES["kl007_wait_message"]

        keyboard = keyboards.create_cleanup_keyboard()
        edited_message = await helpers.edit_message_safely(
            query=query,
            new_text=text,
            new_reply_markup=keyboard,
            new_photo_file_id=config.PROMO_KL007_IMAGE_ID
        )
        if edited_message:
            helpers.add_message_to_cleanup_list(context, edited_message)
        return ConversationHandler.END

    context.user_data['promo_code'] = 'KL007'
    keyboard = keyboards.create_agree_keyboard('KL007')

    edited_message = await helpers.edit_message_safely(
        query=query,
        new_text=PROMO_TEXT_KL007,
        new_reply_markup=keyboard,
        new_photo_file_id=config.PROMO_KL007_IMAGE_ID
    )
    if edited_message:
        helpers.add_message_to_cleanup_list(context, edited_message)

    return AGREE_TERMS

async def ask_for_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Asks for the user's game username after they agree."""
    query = update.callback_query
    try:
        await query.answer()
    except telegram.error.BadRequest as e:
        if "Query is too old" in str(e):
            logger.info(f"Bỏ qua query đã cũ trong kl007.ask_for_username.")
            return # Dừng lại nếu là double-click
        else:
            raise e



    new_caption = RESPONSE_MESSAGES["ask_username_kl007"]
    keyboard = keyboards.create_back_to_show_promo_menu_markup()

    edited_message = await helpers.edit_message_safely(
        query=query,
        new_text=new_caption,
        new_reply_markup=keyboard
    )
    helpers.add_message_to_cleanup_list(context, edited_message)

    return RECEIVE_USERNAME


async def receive_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Nhận username, gửi tin nhắn chờ, tra cứu Google Sheet,
    sau đó EDIT tin nhắn chờ với kết quả cuối cùng.
    """
    user = update.effective_user
    user_message = update.message
    helpers.add_message_to_cleanup_list(context, user_message)
    game_username = update.message.text.strip()
    if not helpers.is_valid_username(game_username):
        # Gửi tin nhắn báo lỗi
        final_keyboard = keyboards.create_cleanup_keyboard()
        error_message = await update.message.reply_text(
            text=RESPONSE_MESSAGES["invalid_username_format"],
            reply_markup=final_keyboard,
            parse_mode=ParseMode.MARKDOWN_V2
        )

        # Thêm cả tin nhắn sai của user và tin nhắn báo lỗi của bot vào danh sách dọn dẹp
        helpers.add_message_to_cleanup_list(context, error_message)

        # QUAN TRỌNG: Kết thúc cuộc hội thoại ngay lập tức
        return ConversationHandler.END

    # === BƯỚC 1: GỬI TIN NHẮN CHỜ (SEND FIRST) ===
    # Bot phản hồi ngay lập tức và lưu lại đối tượng tin nhắn này để edit sau.
    processing_message = await update.message.reply_text("⏳ Đang kiểm tra dữ liệu, vui lòng đợi trong giây lát...")
    #helpers.add_message_to_cleanup_list(context, processing_message)


    # --- Bắt đầu các tác vụ có thể tốn thời gian ---
    try:
        promo_code = 'KL007'

        # Lấy ngày hôm qua và dữ liệu từ Google Sheet
        yesterday_str = helpers.get_yesterday_dmy_str()
        sheet_data = gspread_api.get_kl007_data(game_username, yesterday_str)

        # === BƯỚC 2: XỬ LÝ KẾT QUẢ VÀ CHUẨN BỊ NỘI DUNG/BÀN PHÍM MỚI ===

        final_text = ""



        final_keyboard = keyboards.create_cleanup_keyboard()
        send_to_admin = False
        admin_text = ""
        admin_keyboard = None

        # Kịch bản 1: Không tìm thấy user trong Sheet
        if not sheet_data:
            send_to_admin = True
            final_text = RESPONSE_MESSAGES["yeu_cau_dang_xu_ly"]
            claim_id = await database.add_promo_claim(user.id, promo_code, game_username)
            admin_text = (
                f"ID Game: `{escape_markdown(game_username, version=2)}`\n"
                f"Ngày có vé: {escape_markdown(yesterday_str, version=2)}\n"
                f"Yêu cầu {promo_code} UID:{user.id} \\- [{escape_markdown(user.first_name, version=2)}](tg://user?id={user.id})\n"
            )
            admin_keyboard = keyboards.create_admin_promo_buttons(claim_id, user.id, promo_code)

        else:
            status = sheet_data.get('status', '').strip()
            # Kịch bản 2: Tìm thấy, nhưng đã nhận thưởng
            if status:
                final_text = RESPONSE_MESSAGES["kl007_da_nhan"].format(yesterday_date=yesterday_str)
            # Kịch bản 3: Tìm thấy, đủ điều kiện
            else:
                send_to_admin = True
                final_text = RESPONSE_MESSAGES["yeu_cau_dang_xu_ly"]
                claim_id = await database.add_promo_claim(user.id, promo_code, game_username)
                reward_points = sheet_data.get('reward', 'N/A')
                bet_ticket_info = sheet_data.get('bet_ticket', 'N/A')
                admin_text_parts = [
                    f"ID Game: `{escape_markdown(game_username, version=2)}`",
                    f"Ngày có vé: {yesterday_str}",
                    f"🎟️ Vé cược thắng: {escape_markdown(str(bet_ticket_info), version=2)}",
                    f"💰 Điểm thưởng đề xuất: `{escape_markdown(str(reward_points), version=2)}`",
                    f"Yêu cầu {promo_code} UID:{user.id} \\- [{escape_markdown(user.first_name, version=2)}](tg://user?id={user.id})"
                ]
                admin_text = "\n".join(admin_text_parts)
                admin_keyboard = None

        # Gửi tin nhắn đến admin nếu cần
        if send_to_admin:
            try:
                await context.bot.send_message(
                    chat_id=config.ID_GROUP_KL007, text=admin_text,
                    reply_markup=admin_keyboard, parse_mode=ParseMode.MARKDOWN_V2
                )
                increment_count_in_cache(user.id, "promo")
            except Exception as e:
                logger.error(f"Lỗi khi gửi yêu cầu KL007 đến admin: {e}", exc_info=True)
                final_text = RESPONSE_MESSAGES["error_sending_request"]

        # === BƯỚC 3: EDIT TIN NHẮN CHỜ BAN ĐẦU ===
        await processing_message.edit_text(
            text=final_text,
            reply_markup=final_keyboard,
            parse_mode=ParseMode.MARKDOWN_V2
        )

    except Exception as e:
        # Nếu có bất kỳ lỗi nào trong toàn bộ quá trình, edit tin nhắn chờ để báo lỗi
        logger.error(f"Lỗi nghiêm trọng trong luồng KL007 cho user {user.id}: {e}", exc_info=True)
        try:
            await processing_message.edit_text(
            text=RESPONSE_MESSAGES["error_sending_request"],
            reply_markup=final_keyboard
        )

        except Exception as edit_error:
            logger.error(f"Không thể edit tin nhắn báo lỗi: {edit_error}")

    # Luôn kết thúc cuộc trò chuyện
    # context.user_data.clear()
    return ConversationHandler.END

# Build the conversation handler
kl007_conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_kl007, pattern='^promo_KL007$')
    ],
    states={
        AGREE_TERMS: [
            CallbackQueryHandler(ask_for_username, pattern='^agree_terms:KL007$')
        ],
        RECEIVE_USERNAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_username)
        ],
    },
    fallbacks=get_fallbacks(),
    block=False,
    name="kl007_conversation",
    per_message=False
)
