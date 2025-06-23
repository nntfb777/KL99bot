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
from telegram.helpers import escape_markdown
from telegram.constants import ParseMode

from core import database
from utils import keyboards
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


    if query.message.caption:
        await query.edit_message_caption(
            caption=PROMO_TEXT_KL006,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN_V2
        )
    else:
        await query.edit_message_text(
            text=PROMO_TEXT_KL006,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN_V2
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

    usernames = [u.strip() for u in re.split(r'[,\n\s]+', update.message.text) if u.strip()]

    if len(usernames) != group_size:
        await update.message.reply_text(
            RESPONSE_MESSAGES["kl006_invalid_username_count"].format(
                submitted_count=len(usernames),
                expected_count=group_size
            )
        )
        return RECEIVE_USERNAMES # Stay in the same state to re-enter

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
    fallbacks=[CallbackQueryHandler(cancel, pattern='^cancel$')],
)