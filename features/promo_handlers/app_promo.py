# features/promo_handlers/app_promo.py

import logging
from telegram import Update
from telegram.ext import (
    ConversationHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
from telegram.helpers import escape_markdown
from telegram.constants import ParseMode

from core import database
from utils import keyboards, helpers
from texts import PROMO_TEXT_APP_EXPERIENCE, RESPONSE_MESSAGES
from features.common_handlers import cancel
import config

logger = logging.getLogger(__name__)

# States
AGREE_TERMS, RECEIVE_USERNAME, AWAIT_IMAGE_CONFIRM, RECEIVE_IMAGE = range(4)

async def start_app_promo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Shows App Promo details and asks for agreement."""
    query = update.callback_query
    await query.answer()

    context.user_data['promo_code'] = 'APP_PROMO'
    keyboard = keyboards.create_agree_keyboard('APP_PROMO')

    try:
        await query.edit_message_caption(
            caption=PROMO_TEXT_APP_EXPERIENCE,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception:
        await query.edit_message_text(
            text=PROMO_TEXT_APP_EXPERIENCE,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN
        )
    return AGREE_TERMS

async def ask_for_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Asks for the user's game username."""
    query = update.callback_query
    await query.answer()

    await helpers.remove_buttons(update)
    await context.bot.send_message(
        chat_id=query.effective_chat.id,
        text=RESPONSE_MESSAGES["ask_username_app_promo"],
        reply_markup=keyboards.create_cancel_keyboard()
    )
    return RECEIVE_USERNAME

async def ask_for_image_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Saves username and asks if they have a confirmation image."""
    context.user_data['game_username'] = update.message.text.strip()

    await update.message.reply_text(
        text=RESPONSE_MESSAGES["app_promo_ask_image"],
        reply_markup=keyboards.create_app_promo_image_confirm_keyboard()
    )
    return AWAIT_IMAGE_CONFIRM

async def handle_image_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles user's 'Yes/No' answer for providing an image."""
    query = update.callback_query
    await query.answer()
    choice = query.data.split(':')[1]

    if choice == 'yes':
        await query.edit_message_text(
            text=RESPONSE_MESSAGES["app_promo_request_image"],
            reply_markup=keyboards.create_cancel_keyboard()
        )
        return RECEIVE_IMAGE
    else: # choice == 'no'
        await query.edit_message_text(RESPONSE_MESSAGES["yeu_cau_dang_xu_ly"])
        return await send_request_to_admin(update, context, with_photo=False)


async def receive_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the photo and sends the request to admin."""
    if not update.message.photo:
        await update.message.reply_text("Vui lòng gửi một hình ảnh.")
        return RECEIVE_IMAGE

    context.user_data['photo_id'] = update.message.photo[-1].file_id
    await update.message.reply_text(RESPONSE_MESSAGES["yeu_cau_dang_xu_ly"])
    return await send_request_to_admin(update, context, with_photo=True)


async def send_request_to_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, with_photo: bool) -> int:
    """Helper function to format and send the request to the admin group."""
    user = update.effective_user
    game_username = context.user_data.get('game_username', 'N/A')
    promo_code = context.user_data.get('promo_code', 'APP_PROMO')

    claim_id = database.add_promo_claim(
        user_id=user.id,
        promo_code=promo_code,
        game_username=game_username,
        details={"has_photo": with_photo}
    )

    user_link = f"[{escape_markdown(user.first_name, version=2)}](tg://user?id={user.id})"
    admin_caption = (
        f"Yêu cầu {promo_code} \\- {user_link} ({user.id})\n"
        f"ID: `{claim_id}`\n"
        f"Tên đăng nhập: `{escape_markdown(game_username, version=2)}`"
    )

    admin_keyboard = keyboards.create_admin_promo_buttons(claim_id, user.id, promo_code)

    try:
        if with_photo and 'photo_id' in context.user_data:
            await context.bot.send_photo(
                chat_id=config.ID_GROUP_PROMO,
                photo=context.user_data['photo_id'],
                caption=admin_caption,
                reply_markup=admin_keyboard,
                parse_mode=ParseMode.MARKDOWN_V2
            )
        else:
            admin_caption += "\n*KHÔNG có ảnh xác nhận*"
            await context.bot.send_message(
                chat_id=config.ID_GROUP_PROMO,
                text=admin_caption,
                reply_markup=admin_keyboard,
                parse_mode=ParseMode.MARKDOWN_V2
            )
        
        # Notify user
        user_message = RESPONSE_MESSAGES["app_promo_image_sent_to_admin"] if with_photo else RESPONSE_MESSAGES["app_promo_no_image_sent_to_admin"]
        await context.bot.send_message(
            chat_id=user.id,
            text=user_message,
            reply_markup=keyboards.create_back_to_main_menu_markup()
        )

    except Exception as e:
        logger.error(f"Failed to send App Promo claim {claim_id} to admin group: {e}", exc_info=True)
        await context.bot.send_message(chat_id=user.id, text=RESPONSE_MESSAGES["error_sending_request"])
    
    context.user_data.clear()
    return ConversationHandler.END

app_promo_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_app_promo, pattern='^promo_APP_PROMO$')],
    states={
        AGREE_TERMS: [CallbackQueryHandler(ask_for_username, pattern='^agree_terms:APP_PROMO$')],
        RECEIVE_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_for_image_confirm)],
        AWAIT_IMAGE_CONFIRM: [CallbackQueryHandler(handle_image_confirm, pattern=r'^app_promo_has_image:(yes|no)$')],
        RECEIVE_IMAGE: [MessageHandler(filters.PHOTO, receive_image)],
    },
    fallbacks=[CallbackQueryHandler(cancel, pattern='^cancel$')],
)