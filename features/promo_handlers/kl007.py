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
from .common import PROMO_FALLBACKS
from telegram.helpers import escape_markdown
from telegram.constants import ParseMode
from core import database
from utils import keyboards, helpers, gspread_api
from texts import PROMO_TEXT_KL007, RESPONSE_MESSAGES
from features.common_handlers import cancel
import config
from datetime import datetime
import pytz


logger = logging.getLogger(__name__)

# States
AGREE_TERMS, RECEIVE_USERNAME = range(2)

async def start_kl007(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Shows KL007 promo details and asks for agreement."""
    query = update.callback_query
    await query.answer()


    tz_vietnam = pytz.timezone('Asia/Ho_Chi_Minh')
    now_vietnam = datetime.now(tz_vietnam)
    current_hour = now_vietnam.hour

    # 2. Kiểm tra nếu giờ hiện tại là 11 (tức là từ 11:00:00 đến 11:59:59)
    if current_hour == 11:
        # Gửi thông báo chờ đợi
        text = RESPONSE_MESSAGES["kl007_wait_message"]
        keyboard = keyboards.create_back_to_main_menu_markup()

        await helpers.edit_message_safely(
            query=query,
            new_text=text,
            new_reply_markup=keyboard,
            new_photo_file_id=config.PROMO_KL007_IMAGE_ID # <--- TRUYỀN ID ẢNH MỚI
        )

        # Kết thúc cuộc trò chuyện ngay lập tức
        return ConversationHandler.END

    context.user_data['promo_code'] = 'KL007'
    keyboard = keyboards.create_agree_keyboard('KL007')

    # Assuming we are editing a message with a photo caption
    await helpers.edit_message_safely(
        query=query,
        new_text=PROMO_TEXT_KL007,
        new_reply_markup=keyboard,
        new_photo_file_id=config.PROMO_KL007_IMAGE_ID
    )
    return AGREE_TERMS

async def ask_for_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Asks for the user's game username after they agree."""
    query = update.callback_query
    await query.answer()

    new_caption = RESPONSE_MESSAGES["ask_username_kl007"]

    if query.message.caption:
        await query.edit_message_caption(
            caption=new_caption,
            reply_markup=keyboards.create_cancel_keyboard()
        )
    else:
        await query.edit_message_text(
            text=new_caption,
            reply_markup=keyboards.create_cancel_keyboard()
        )
    return RECEIVE_USERNAME

# features/promo_handlers/kl007.py

# Đảm bảo bạn có các import này ở đầu file:
# from datetime import datetime, timedelta
# import pytz
# from utils import helpers, gspread_api


async def receive_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Nhận username, gửi tin nhắn chờ, tra cứu Google Sheet,
    sau đó EDIT tin nhắn chờ với kết quả cuối cùng.
    """
    user = update.effective_user
    game_username = update.message.text.strip()

    # === BƯỚC 1: GỬI TIN NHẮN CHỜ (SEND FIRST) ===
    # Bot phản hồi ngay lập tức và lưu lại đối tượng tin nhắn này để edit sau.
    processing_message = await update.message.reply_text("⏳ Đang kiểm tra dữ liệu, vui lòng đợi trong giây lát...")

    # --- Bắt đầu các tác vụ có thể tốn thời gian ---
    try:
        promo_code = 'KL007'

        # Lấy ngày hôm qua và dữ liệu từ Google Sheet
        yesterday_str = helpers.get_yesterday_dmy_str()
        sheet_data = gspread_api.get_kl007_data(game_username, yesterday_str)

        # === BƯỚC 2: XỬ LÝ KẾT QUẢ VÀ CHUẨN BỊ NỘI DUNG/BÀN PHÍM MỚI ===

        final_text = ""
        final_keyboard = keyboards.create_back_to_main_menu_markup()
        send_to_admin = False
        admin_text = ""
        admin_keyboard = None

        # Kịch bản 1: Không tìm thấy user trong Sheet
        if not sheet_data:
            send_to_admin = True
            final_text = RESPONSE_MESSAGES["yeu_cau_dang_xu_ly"]
            claim_id = database.add_promo_claim(user.id, promo_code, game_username)
            admin_text = (
                f"Yêu cầu {promo_code} UID:`{user.id}` \\- [{escape_markdown(user.first_name, version=2)}](tg://user?id={user.id})\n"
                f"ID Game: `{escape_markdown(game_username, version=2)}`\n"
                f"Ngày có vé: {yesterday_str}\n"
            )
            admin_keyboard = keyboards.create_admin_promo_buttons(claim_id, user.id, promo_code)

        else:
            status = sheet_data.get('status', '').strip()
            # Kịch bản 2: Tìm thấy, nhưng đã nhận thưởng
            if status:
                final_text = RESPONSE_MESSAGES["kl007_da_nhan"]
            # Kịch bản 3: Tìm thấy, đủ điều kiện
            else:
                send_to_admin = True
                final_text = RESPONSE_MESSAGES["yeu_cau_dang_xu_ly"]
                claim_id = database.add_promo_claim(user.id, promo_code, game_username)
                reward_points = sheet_data.get('reward', 'N/A')
                bet_ticket_info = sheet_data.get('bet_ticket', 'N/A')
                admin_text_parts = [
                    f"Yêu cầu {promo_code} UID:`{user.id}` \\- [{escape_markdown(user.first_name, version=2)}](tg://user?id={user.id})",
                    f"ID Game: `{escape_markdown(game_username, version=2)}`",
                    f"Ngày có vé: {yesterday_str}",
                    f"🎟️ Vé cược thắng: `{escape_markdown(str(bet_ticket_info), version=2)}`",
                    f"💰 Điểm thưởng đề xuất: `{escape_markdown(str(reward_points), version=2)}`"
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
            except Exception as e:
                logger.error(f"Lỗi khi gửi yêu cầu KL007 đến admin: {e}", exc_info=True)
                final_text = RESPONSE_MESSAGES["error_sending_request"]

        # === BƯỚC 3: EDIT TIN NHẮN CHỜ BAN ĐẦU ===
        await processing_message.edit_text(
            text=final_text,
            reply_markup=final_keyboard
        )

    except Exception as e:
        # Nếu có bất kỳ lỗi nào trong toàn bộ quá trình, edit tin nhắn chờ để báo lỗi
        logger.error(f"Lỗi nghiêm trọng trong luồng KL007 cho user {user.id}: {e}", exc_info=True)
        try:
            await processing_message.edit_text(RESPONSE_MESSAGES["error_sending_request"])
        except Exception as edit_error:
            logger.error(f"Không thể edit tin nhắn báo lỗi: {edit_error}")

    # Luôn kết thúc cuộc trò chuyện
    context.user_data.clear()
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
    fallbacks=PROMO_FALLBACKS,
    block=False,
    name="kl007_conversation",
    per_message=False
)
