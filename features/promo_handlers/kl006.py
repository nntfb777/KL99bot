# features/promo_handlers/kl006.py
import logging
import re
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
from texts import PROMO_TEXT_KL006, RESPONSE_MESSAGES
from features.common_handlers import cancel
import config

logger = logging.getLogger(__name__)

# States
AGREE_TERMS, CHOOSE_GROUP_SIZE, RECEIVE_USERNAMES = range(3)

async def start_kl006(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Shows KL006 promo details and asks for agreement."""
    query = update.callback_query
    await query.answer()

    context.user_data['promo_code'] = 'KL006'
    keyboard = keyboards.create_agree_keyboard('KL006')


    await helpers.edit_message_safely(
        query=query,
        new_text=PROMO_TEXT_KL006,
        new_reply_markup=keyboard,
        new_photo_file_id=config.PROMO_KL006_IMAGE_ID
    )
    return AGREE_TERMS

async def ask_group_size(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Asks user to select their group size."""
    query = update.callback_query
    await query.answer()


    keyboard = keyboards.create_kl006_group_size_keyboard()
    if query.message.caption:
        await query.edit_message_caption(
            caption=RESPONSE_MESSAGES["kl006_agree_ask_group_size"],
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN_V2
        )
    else:
        await query.edit_message_text(
            text=RESPONSE_MESSAGES["kl006_agree_ask_group_size"],
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN_V2
        )

    return CHOOSE_GROUP_SIZE

async def ask_for_usernames(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Asks for the list of usernames based on group size."""
    query = update.callback_query
    await query.answer()

    group_size = int(query.data.split(':')[1])
    context.user_data['kl006_group_size'] = group_size

    if query.message.caption:
        await query.edit_message_caption(
            caption=RESPONSE_MESSAGES["kl006_ask_usernames"].format(group_size=group_size),
            reply_markup=keyboards.create_cancel_keyboard(),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    else:
        await query.edit_message_text(
            text=RESPONSE_MESSAGES["kl006_ask_usernames"].format(group_size=group_size),
            reply_markup=keyboards.create_cancel_keyboard(),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    return RECEIVE_USERNAMES

async def receive_usernames(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives usernames, validates count, and sends to admin."""
    user = update.effective_user
    promo_code = context.user_data.get('promo_code', 'KL006')
    group_size = context.user_data.get('kl006_group_size')

    usernames = re.split(r'[,\s]+', update.message.text.strip())
    # Loại bỏ các chuỗi rỗng có thể có
    usernames = [name for name in usernames if name]

    if len(usernames) != group_size:
        message = RESPONSE_MESSAGES["kl006_invalid_username_count"].format(
            submitted_count=len(usernames),
            expected_count=group_size
        )
        await update.message.reply_text(message)
        return AWAIT_USERNAMES # Yêu cầu nhập lại

    # === LOGIC KIỂM TRA MỚI ===
    # Gọi API để kiểm tra nhóm
    is_valid_group, error_message = gspread_api.find_kl006_group(usernames)

    if not is_valid_group:
        # Nếu nhóm không hợp lệ, thông báo lỗi cho người dùng và kết thúc
        # Tùy chỉnh thông báo lỗi dựa trên kết quả trả về
        if "chưa được đăng ký" in error_message:
            # Format lại để chèn tên user vào
            username_not_found = error_message.split("'")[1]
            final_error_message = RESPONSE_MESSAGES["kl006_user_not_registered"].format(username=username_not_found)
        else:
            final_error_message = RESPONSE_MESSAGES["kl006_users_not_in_same_group"]

        await update.message.reply_text(final_error_message, reply_markup=keyboards.create_back_to_main_menu_markup())
        return ConversationHandler.END

    # Add claim to DB
    claim_id = database.add_promo_claim(
        user_id=user.id,
        promo_code=promo_code,
        game_username=None, # Not applicable for group leader
        details={"members": usernames}
    )

    # Format message for admin
    usernames_md = "\n".join([f"`{escape_markdown(name, version=2)}`" for name in usernames])
    admin_text = (
        f"Yêu cầu {promo_code} \\(Nhóm {group_size}\\) \\- [{escape_markdown(user.first_name, version=2)}](tg://user?id={user.id})\n"
        f"Thành viên:\n{usernames_md}"
    )

    admin_keyboard = keyboards.create_admin_promo_buttons(claim_id, user.id, promo_code, usernames=usernames)

    try:
        await context.bot.send_message(
            chat_id=config.ID_GROUP_PROMO,
            text=admin_text,
            reply_markup=admin_keyboard,
            parse_mode=ParseMode.MARKDOWN_V2
        )
        await update.message.reply_text(
            RESPONSE_MESSAGES["yeu_cau_dang_xu_ly"],
            reply_markup=keyboards.create_back_to_main_menu_markup()
        )
    except Exception as e:
        logger.error(f"Failed to send KL006 claim {claim_id} to admin group: {e}")
        await update.message.reply_text(RESPONSE_MESSAGES["error_sending_request"])

    context.user_data.clear()
    return ConversationHandler.END

kl006_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_kl006, pattern='^promo_KL006$')],
    states={
        AGREE_TERMS: [CallbackQueryHandler(ask_group_size, pattern='^agree_terms:KL006$')],
        CHOOSE_GROUP_SIZE: [CallbackQueryHandler(ask_for_usernames, pattern=r'^kl006_select_group:\d+$')],
        RECEIVE_USERNAMES: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_usernames)],
    },
    fallbacks=PROMO_FALLBACKS,  # <--- SỬ DỤNG FALLBACK CHUNG
    block=False,                # <--- THÊM THAM SỐ NÀY
    per_message=False,
    name="kl006_conversation"
)