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
from ..fallbacks import get_fallbacks
from core import database
from utils import keyboards, helpers, analytics
from texts import RESPONSE_MESSAGES
import config
import asyncio
logger = logging.getLogger(__name__)

# States
SHOW_SHARE_MENU, AWAIT_USERNAME_FOR_REWARD = range(2)

#@log_callback_query
async def share_code_entry_point(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Main entry point for the sharing feature."""
    query = update.callback_query
    if query:
        helpers.add_message_to_cleanup_list(context, query.message)

    user = update.effective_user
    db_user = await database.get_or_create_user(user.id, user.first_name, user.username)

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

    edit_message = await helpers.edit_message_safely(
        query=query,
        new_text=intro_text,
        new_reply_markup=keyboard,
        new_photo_file_id=config.SHARING_IMAGE_ID
    )
    helpers.add_message_to_cleanup_list(context, edit_message)

    return SHOW_SHARE_MENU

#@log_callback_query
async def get_my_share_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Provides the user with their unique referral link."""
    query = update.callback_query
    user = update.effective_user
    asyncio.create_task(
        analytics.log_event(user_id=user.id, event_name='get_share_link')
    )

    helpers.add_message_to_cleanup_list(context, query.message)

    db_user = await database.get_or_create_user(user.id, user.first_name, user.username)
    referral_code = db_user.get("referral_code")

    if not config.BOT_USERNAME:
        await context.bot.send_message(chat_id=user.id, text=RESPONSE_MESSAGES["error_getting_bot_info"])
        return SHOW_SHARE_MENU

    share_link = f"https://t.me/{config.BOT_USERNAME}?start=ref_{referral_code}"
    message_text = RESPONSE_MESSAGES["my_share_link_message"].format(share_link=escape_markdown(share_link, version=2))
    share_text_for_friends = RESPONSE_MESSAGES['sharing_share_text_template'].format(share_link=share_link)
    keyboard = keyboards.create_my_share_link_keyboard(share_text=share_text_for_friends)

    send_message = await context.bot.send_message(
        chat_id=user.id,
        text=message_text,
        parse_mode=ParseMode.MARKDOWN_V2,
        reply_markup=keyboard
    )
    helpers.add_message_to_cleanup_list(context, send_message)
    return SHOW_SHARE_MENU

#@log_callback_query
async def request_code_reward(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Kiểm tra mốc thưởng, phiên bản đã được tái cấu trúc hoàn chỉnh.
    """
    query = update.callback_query
    user = update.effective_user

    # Bọc toàn bộ trong try...except để xử lý lỗi một cách nhất quán
    try:
        # 1. KIỂM TRA "KHÓA" TRƯỚC TIÊN
        if await database.has_pending_share_claim(user.id):
            # Nếu bị khóa, chỉ answer với alert và dừng lại.
            await query.answer(
                text="Bạn đang có một yêu cầu nhận thưởng đang chờ xử lý. Vui lòng đợi.",
                show_alert=True
            )
            return SHOW_SHARE_MENU # Giữ nguyên trạng thái


        # 3. LOGIC CHÍNH
        helpers.add_message_to_cleanup_list(context, query.message)
        db_user = await database.get_or_create_user(user.id, user.first_name, user.username)

        if not db_user:
            # Xử lý trường hợp không lấy được user
            await helpers.edit_message_safely(
                query=query,
                new_text="Lỗi: Không thể truy xuất dữ liệu người dùng\\. Vui lòng thử lại sau\\.",
                new_reply_markup=keyboards.create_cleanup_keyboard()
            )
            return ConversationHandler.END

        # Tính toán chỉ MỘT LẦN
        share_count = db_user.get('share_count', 0)
        claimed_milestones = json.loads(db_user.get('claimed_milestones', '[]'))
        claimable_milestone = next((ms for ms in config.SHARE_MILESTONES if share_count >= ms and ms not in claimed_milestones), None)

        if claimable_milestone:
            # TRƯỜNG HỢP 1: ĐỦ ĐIỀU KIỆN
            context.user_data['milestone_to_claim'] = claimable_milestone
            message = RESPONSE_MESSAGES["ask_username_for_share_reward"].format(milestone=claimable_milestone)
            keyboard = keyboards.create_cleanup_keyboard(is_fallback=True) # Dùng fallback

            await helpers.edit_message_safely(
                query=query, new_text=message, new_reply_markup=keyboard, new_photo_file_id=config.SHARING_IMAGE_ID
            )
            return AWAIT_USERNAME_FOR_REWARD
        else:
            # TRƯỜNG HỢP 2: CHƯA ĐỦ ĐIỀU KIỆN
            next_milestone = next((ms for ms in config.SHARE_MILESTONES if ms not in claimed_milestones), None)

            if next_milestone:
                message = RESPONSE_MESSAGES["no_new_milestone_message"].format(
                    share_count=share_count, needed_more=next_milestone - share_count, next_milestone=next_milestone
                )
                keyboard = keyboards.create_sharing_menu_markup(show_claim_button=False)
            else:
                message = RESPONSE_MESSAGES["all_milestones_claimed_message"]
                keyboard = keyboards.create_sharing_menu_markup(show_claim_button=False)

            await helpers.edit_message_safely(query, message, keyboard, parse_mode=ParseMode.MARKDOWN_V2)
            return SHOW_SHARE_MENU

    except telegram.error.BadRequest as e:
        # Bắt lỗi BadRequest cụ thể (như Query is too old)
        if "Query is too old" in str(e):
            logger.info(f"Bỏ qua lỗi 'Query is too old' trong request_code_reward.")
            # Không làm gì cả, vì decorator đã có thể xử lý việc này
            return
        else:
            logger.error(f"Lỗi BadRequest không mong muốn trong request_code_reward: {e}", exc_info=True)
            raise e # Ném các lỗi BadRequest khác
    except Exception as e:
        # Bắt tất cả các lỗi khác
        logger.error(f"Lỗi không mong muốn trong request_code_reward: {e}", exc_info=True)
        # Ném lỗi ra ngoài để error_handler toàn cục xử lý
        raise e




async def receive_username_for_reward(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    (Hoàn chỉnh) Nhận username, ghi vào DB, gửi cho admin, và trả lời user.
    """
    user = update.effective_user
    user_message = update.message
    helpers.add_message_to_cleanup_list(context, user_message)

    game_username = update.message.text.strip()
    milestone = context.user_data.get('milestone_to_claim')

    # --- KIỂM TRA ĐIỀU KIỆN ---
    if not milestone:
        await update.message.reply_text("Lỗi: Không tìm thấy thông tin mốc thưởng.", reply_markup=keyboards.create_cleanup_keyboard())
        return ConversationHandler.END

    # Kiểm tra định dạng username (rất khuyến nghị)
    if not helpers.is_valid_username(game_username):
        await update.message.reply_text(
            RESPONSE_MESSAGES["invalid_username_format"],
            reply_markup=keyboards.create_cleanup_keyboard(),
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return ConversationHandler.END

    try:
        # --- LOGIC CHÍNH: TƯƠNG TÁC VỚI HỆ THỐNG ---

        # 1. LẤY ĐIỂM THƯỞNG
        reward_points = config.SHARE_MILESTONES_REWARDS.get(milestone, 0)
        details = {"milestone": milestone, "reward_points": reward_points}

        # 2. GHI VÀO DATABASE (TRỰC TIẾP, BẤT ĐỒNG BỘ)
        # Hàm này bây giờ trả về claim_id
        claim_id = await database.add_promo_claim(
            user_id=user.id,
            promo_code='SHARING',
            game_username=game_username,
            details=details
        )

        # 3. GỬI TIN NHẮN CHO ADMIN
        admin_text = (
            f"Yêu cầu Thưởng Chia Sẻ Mốc {milestone} \\- [{escape_markdown(user.first_name, version=2)}](tg://user?id={user.id})\n"
            f"ID Game: `{escape_markdown(game_username, version=2)}`\n"
            f"🎁 **Điểm thưởng:** `{reward_points}`"
        )
        admin_keyboard = keyboards.create_admin_share_reward_buttons(claim_id, user.id, milestone)

        await context.bot.send_message(
            chat_id=config.ID_GROUP_PROMO,
            text=admin_text,
            reply_markup=admin_keyboard,
            parse_mode=ParseMode.MARKDOWN_V2
        )

        # 4. TRẢ LỜI NGƯỜI DÙNG
        final_text = RESPONSE_MESSAGES["share_reward_request_sent"].format(
            milestone=milestone,
            game_username=escape_markdown(game_username, version=2)
        )

        # Gửi tin nhắn MỚI
        sent_message = await context.bot.send_message(
            chat_id=user.id,
            text=final_text,
            reply_markup=keyboards.create_cleanup_keyboard(),
            parse_mode=ParseMode.MARKDOWN_V2
        )

        # 3. DỌN DẸP
        # Lấy danh sách tin nhắn cũ cần xóa (bao gồm cả tin nhắn prompt)
        messages_to_delete_ids = context.user_data.pop('messages_to_delete', [])
        # Thêm tin nhắn username của khách vào
        messages_to_delete_ids.append(user_message.message_id)

        # Xóa tất cả các tin nhắn cũ
        for msg_id in messages_to_delete_ids:
            try:
                await context.bot.delete_message(chat_id=user.id, message_id=msg_id)
            except Exception:
                pass # Bỏ qua nếu không xóa được

        # Chỉ lưu lại tin nhắn cuối cùng để dọn dẹp cho lần sau
        context.user_data['messages_to_delete'] = [sent_message.message_id]

    except Exception as e:
        logger.error(f"Lỗi trong receive_username_for_reward: {e}", exc_info=True)
        # Gửi tin nhắn lỗi MỚI
        await context.bot.send_message(
            chat_id=user.id,
            text=RESPONSE_MESSAGES["error_sending_request"],
            reply_markup=keyboards.create_cleanup_keyboard(),
            parse_mode=ParseMode.MARKDOWN_V2
        )
    finally:
        # Dọn dẹp các key không cần thiết khác
        context.user_data.pop('milestone_to_claim', None)
        context.user_data.pop('prompt_message', None) # Vẫn xóa key này cho sạch

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
    fallbacks=get_fallbacks(),
    #block=False,
    #per_message=False,
    allow_reentry=True,
    name="share_conversation"
)