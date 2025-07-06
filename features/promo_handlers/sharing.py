# features/promo_handlers/sharing.py
import telegram
import logging
import json
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
from .common import PROMO_FALLBACKS
from core import database
from utils import keyboards, helpers
from texts import RESPONSE_MESSAGES
import config

logger = logging.getLogger(__name__)

# States
SHOW_SHARE_MENU, AWAIT_USERNAME_FOR_REWARD = range(2)

async def share_code_entry_point(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Main entry point for the sharing feature."""
    query = update.callback_query
    if query:
        await query.answer()

    user = update.effective_user
    db_user = database.get_or_create_user(user.id, user.first_name, user.username)

    share_count = db_user.get('share_count', 0)
    claimed_milestones = json.loads(db_user.get('claimed_milestones', '[]'))

    # Determine the next milestone
    next_milestone_val = None
    for ms in config.SHARE_MILESTONES:
        if ms not in claimed_milestones:
            next_milestone_val = ms
            break

    # Format intro text
    if share_count == 0:
        intro_text = RESPONSE_MESSAGES['share_code_intro_no_shares']
    elif next_milestone_val:
        needed_shares = next_milestone_val - share_count
        intro_text = RESPONSE_MESSAGES['share_code_intro'].format(
            share_count=share_count,
            next_milestone=next_milestone_val,
            needed_shares=max(0, needed_shares) # Ensure it's not negative
        )
    else:
        intro_text = RESPONSE_MESSAGES['all_milestones_claimed_message']


    keyboard = keyboards.create_sharing_menu_markup(show_claim_button=True)

    original_message = query.message
    try:
        if original_message.caption:
            # Nếu có, sử dụng edit_message_caption
            await query.edit_message_caption(
                caption=intro_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN_V2
            )
        else:
            # Nếu không (chỉ có text), sử dụng edit_message_text
            await query.edit_message_text(
                text=intro_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN_V2
            )
    except telegram.error.BadRequest as e:
        # Nếu lỗi là "Message is not modified", thì bỏ qua
        if "Message is not modified" in str(e):
            pass # Không làm gì cả, vì đây là hành vi mong muốn
        else:
            # Nếu là một lỗi BadRequest khác, thì ghi log
            logger.error(f"Lỗi BadRequest khi sửa tin nhắn nhận thưởng: {e}")
    except Exception as e:
        # Bắt các lỗi khác
        logger.error(f"Lỗi không xác định khi sửa tin nhắn nhận thưởng: {e}")

    return SHOW_SHARE_MENU

async def get_my_share_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Provides the user with their unique referral link."""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    db_user = database.get_or_create_user(user.id, user.first_name, user.username)
    referral_code = db_user.get("referral_code")

    if not config.BOT_USERNAME:
        await context.bot.send_message(chat_id=user.id, text=RESPONSE_MESSAGES["error_getting_bot_info"])
        return SHOW_SHARE_MENU

    share_link = f"https://t.me/{config.BOT_USERNAME}?start=ref_{referral_code}"
    message_text = RESPONSE_MESSAGES["my_share_link_message"].format(share_link=escape_markdown(share_link, version=2))

    await context.bot.send_message(chat_id=user.id, text=message_text, parse_mode=ParseMode.MARKDOWN_V2)
    return SHOW_SHARE_MENU


async def request_code_reward(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Checks for claimable milestones and asks for username or shows status."""
    query = update.callback_query
    await query.answer()
    user = update.effective_user

    db_user = database.get_or_create_user(user.id, user.first_name, user.username)
    share_count = db_user.get('share_count', 0)
    claimed_milestones = json.loads(db_user.get('claimed_milestones', '[]'))

    # Tìm mốc thưởng có thể nhận
    claimable_milestone = None
    for ms in config.SHARE_MILESTONES:
        if share_count >= ms and ms not in claimed_milestones:
            claimable_milestone = ms
            break

    if claimable_milestone:
        # Trường hợp ĐỦ mốc, yêu cầu username
        context.user_data['milestone_to_claim'] = claimable_milestone
        message = RESPONSE_MESSAGES["ask_username_for_share_reward"].format(milestone=claimable_milestone)
        keyboard = keyboards.create_cancel_keyboard()

        # Dùng hàm helper an toàn để edit và chuyển state
        await helpers.edit_message_safely(query, message, keyboard, parse_mode=ParseMode.MARKDOWN_V2)
        return AWAIT_USERNAME_FOR_REWARD
    else:
        # Trường hợp CHƯA đủ mốc, thông báo tình hình
        next_milestone_to_achieve = next((ms for ms in config.SHARE_MILESTONES if ms not in claimed_milestones), None)

        if next_milestone_to_achieve:
            needed_more = next_milestone_to_achieve - share_count
            # Tạo tin nhắn thông báo
            message = RESPONSE_MESSAGES["no_new_milestone_message"].format(
                share_count=share_count,
                needed_more=needed_more,
                next_milestone=next_milestone_to_achieve
            )
            # Tạo bàn phím mới KHÔNG có nút "Nhận thưởng"
            keyboard = keyboards.create_sharing_menu_markup(show_claim_button=False)
        else:
            # Trường hợp đã nhận hết tất cả các mốc
            message = RESPONSE_MESSAGES["all_milestones_claimed_message"]
            keyboard = keyboards.create_sharing_menu_markup(show_claim_button=False)

        # Dùng hàm helper an toàn để edit
        await helpers.edit_message_safely(query, message, keyboard, parse_mode=ParseMode.MARKDOWN_V2)
        return SHOW_SHARE_MENU

async def receive_username_for_reward(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives username for the milestone reward and sends it to admin."""
    user = update.effective_user
    game_username = update.message.text.strip()
    milestone = context.user_data.get('milestone_to_claim')

    if not milestone:
        await update.message.reply_text("Lỗi: Không tìm thấy thông tin mốc thưởng\\. Vui lòng thử lại\\.")
        context.user_data.clear()
        return ConversationHandler.END

    claim_id = database.add_share_claim(user.id, milestone, game_username)
    admin_text = (
        f"Yêu cầu Thưởng Chia Sẻ \\(Mốc {milestone}\\) \\- [{escape_markdown(user.first_name, version=2)}](tg://user?id={user.id})\n"
        f"ID: `{escape_markdown(game_username, version=2)}`"
    )

    admin_keyboard = keyboards.create_admin_share_reward_buttons(claim_id, user.id, milestone)

    try:
        await context.bot.send_message(
            chat_id=config.ID_GROUP_PROMO,
            text=admin_text,
            reply_markup=admin_keyboard,
            parse_mode=ParseMode.MARKDOWN_V2
        )
        await update.message.reply_text(
            RESPONSE_MESSAGES["share_reward_request_sent"].format(milestone=milestone, game_username=game_username),
            reply_markup=keyboards.create_back_to_main_menu_markup()
        )
    except Exception as e:
        logger.error(f"Failed to send share reward claim {claim_id} to admin group: {e}", exc_info=True)
        await update.message.reply_text(RESPONSE_MESSAGES["error_sending_request"])

    context.user_data.clear()
    return ConversationHandler.END


sharing_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(share_code_entry_point, pattern='^share_code_entry_point$')],
    states={
        SHOW_SHARE_MENU: [
            CallbackQueryHandler(get_my_share_link, pattern='^share_get_link$'),
            CallbackQueryHandler(request_code_reward, pattern='^share_request_reward$'),
        ],
        AWAIT_USERNAME_FOR_REWARD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_username_for_reward)],
    },
    fallbacks=PROMO_FALLBACKS,  # <--- SỬ DỤNG FALLBACK CHUNG
    block=False,                # <--- THÊM THAM SỐ NÀY
    per_message=False,
    name="share_conversation"
)