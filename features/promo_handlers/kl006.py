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
from ..fallbacks import get_fallbacks
from telegram.helpers import escape_markdown
from telegram.constants import ParseMode
from utils.gspread_api import get_kl006_team_status_from_cache
from core import database
from utils import keyboards, helpers, gspread_api
from core.request_limiter import is_request_available, increment_count_in_cache
from texts import PROMO_TEXT_KL006, RESPONSE_MESSAGES
import config
from datetime import datetime
import pytz
from utils.decorators import log_callback_query


logger = logging.getLogger(__name__)

# States
AGREE_TERMS, CHOOSE_GROUP_SIZE, RECEIVE_USERNAMES = range(3)

@log_callback_query
async def start_kl006(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Shows KL006 promo details and asks for agreement."""

    query = update.callback_query
    user = update.effective_user
    user_id = user.id
    chat_id = update.effective_chat.id
    # --- BƯỚC 1: QUYẾT ĐỊNH HÀNH ĐỘNG TRƯỚC ---
    # Kiểm tra điều kiện mà không thực hiện bất kỳ lệnh `await` nào
    if not is_request_available(user_id, "promo"):
        # Nếu hết lượt, gọi answer() MỘT LẦN DUY NHẤT để hiển thị pop-up.
        await helpers.edit_message_safely(
            query=query,
            new_text=RESPONSE_MESSAGES["out_of_requests"],
            # Cung cấp nút "Quay lại Menu" để dọn dẹp
            new_reply_markup=keyboards.create_cleanup_keyboard()
        )
        try:
            await query.delete_message()
        except Exception as e:
            logger.info(f"Không thể xóa tin nhắn trong start_KL006: {e}")

        try:
            text = RESPONSE_MESSAGES["welcome_message"]
            keyboard = keyboards.create_main_menu_markup()

            sent_message = await context.bot.send_photo(
                chat_id=chat_id,
                photo=config.START_IMAGE_FILE_ID,
                caption=text,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN_V2
            )


            await helpers.cleanup_conversation_messages(context, chat_id=chat_id)

            context.user_data.clear()
            helpers.add_message_to_cleanup_list(context, sent_message)

        except Exception as e:
            logger.error(f"Lỗi khi gửi lại menu chính từ start_KL006: {e}")
            context.user_data.clear()
        return ConversationHandler.END

    tz_vietnam = pytz.timezone('Asia/Ho_Chi_Minh')
    now_vietnam = datetime.now(tz_vietnam)
    current_hour = now_vietnam.hour

    # 2. Kiểm tra nếu giờ hiện tại là 11 (tức là từ 11:00:00 đến 11:59:59)
    if current_hour == 11:
        # Gửi thông báo chờ đợi
        text = RESPONSE_MESSAGES["kl006_wait_message"]
        keyboard = keyboards.create_cleanup_keyboard()

        await helpers.edit_message_safely(
            query=query,
            new_text=text,
            new_reply_markup=keyboard,
            new_photo_file_id=config.PROMO_KL007_IMAGE_ID # <--- TRUYỀN ID ẢNH MỚI
        )

        # Kết thúc cuộc trò chuyện ngay lập tức
        return ConversationHandler.END

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
    await helpers.edit_message_safely(
        query=query,
        new_text=RESPONSE_MESSAGES["kl006_agree_ask_group_size"],
        new_reply_markup=keyboard
    )

    return CHOOSE_GROUP_SIZE

async def ask_for_usernames(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Asks for the list of usernames based on group size."""
    query = update.callback_query
    await query.answer()

    group_size = int(query.data.split(':')[1])
    context.user_data['kl006_group_size'] = group_size
    new_caption = RESPONSE_MESSAGES["kl006_ask_usernames"].format(group_size=group_size)
    await helpers.edit_message_safely(
        query=query,
        new_text=new_caption,
        new_reply_markup=keyboards.create_back_to_show_promo_menu_markup()
    )
    return RECEIVE_USERNAMES

async def receive_usernames(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Nhận usernames và thực hiện quy trình kiểm tra nhiều bước:
    1. Kiểm tra tính toàn vẹn nhóm (không phụ thuộc thứ tự/tên sai).
    2. Kiểm tra cược cá nhân (< 3000) và báo lỗi chi tiết.
    3. Kiểm tra tổng cược nhóm và báo lỗi chi tiết.
    4. Kiểm tra trạng thái đã nhận.
    5. Gửi yêu cầu thành công đến admin với đầy đủ thông tin.
    """
    # === PHẦN 1: KHỞI TẠO ===
    user = update.effective_user
    user_message = update.message
    helpers.add_message_to_cleanup_list(context, user_message)
    promo_code = context.user_data.get('promo_code', 'KL006')
    group_size = context.user_data.get('kl006_group_size')

    # Nhận và chuẩn hóa input từ user
    submitted_usernames_list = [name.strip().lower() for name in re.split(r'[,\s]+', update.message.text.strip()) if name]
    submitted_usernames_set = set(submitted_usernames_list)

    if len(submitted_usernames_list) != group_size:
        # Gửi tin nhắn lỗi và thêm vào danh sách dọn dẹp
        error_msg = await update.message.reply_text(
            RESPONSE_MESSAGES["kl006_invalid_username_count"].format(
                submitted_count=len(submitted_usernames_list), expected_count=group_size
            ),
            reply_markup=keyboards.create_back_to_show_promo_menu_markup(),
            parse_mode=ParseMode.MARKDOWN_V2
        )
        helpers.add_message_to_cleanup_list(context, error_msg)
        return RECEIVE_USERNAMES

    processing_message = await update.message.reply_text("⏳ Đang kiểm tra dữ liệu, vui lòng đợi trong giây lát...")
    helpers.add_message_to_cleanup_list(context, processing_message)

    # Chuẩn bị các biến sẽ được sử dụng nhiều lần
    yesterday_date_str = helpers.get_yesterday_dmy_str()

    back_to_menu_keyboard = keyboards.create_cleanup_keyboard()

    try:
        # === PHẦN 2: LẤY DỮ LIỆU VÀ KIỂM TRA TÍNH TOÀN VẸN NHÓM ===
        team_data = None
        for username_to_find in submitted_usernames_list:
            potential_team_data = get_kl006_team_status_from_cache(username_to_find)
            if potential_team_data:
                team_data = potential_team_data
                break

        if not team_data:
            await processing_message.edit_text(
                text=RESPONSE_MESSAGES["kl006_group_not_registered"].format(yesterday_date=yesterday_date_str),
                reply_markup=back_to_menu_keyboard,
                parse_mode=ParseMode.MARKDOWN_V2
            )
            #context.user_data.clear()
            return ConversationHandler.END

        registered_members_set = team_data['lowercase_members_set']
        if submitted_usernames_set != registered_members_set:
            mismatched_members_str = ", ".join(submitted_usernames_set - registered_members_set)
            await processing_message.edit_text(
                text=RESPONSE_MESSAGES["kl006_members_mismatch"].format(
                    mismatched_members=mismatched_members_str,
                    yesterday_date=yesterday_date_str
                ),
                reply_markup=back_to_menu_keyboard,
                parse_mode=ParseMode.MARKDOWN_V2
            )
            #context.user_data.clear()
            return ConversationHandler.END

        # === PHẦN 3: KIỂM TRA CƯỢC CÁ NHÂN VÀ CHUẨN BỊ DỮ LIỆU CHI TIẾT ===
        low_bet_members = []
        all_members_bet_details = []
        member_bets_map = team_data.get('member_bets', {})

        for original_name in team_data['original_members']:
            bet_amount = member_bets_map.get(original_name.lower(), 0)
            all_members_bet_details.append(f"  \\- `{original_name}` : `{bet_amount:,.0f}` điểm")

            if bet_amount < 3000:
                low_bet_members.append(f"  🚨 `{original_name}` : `{bet_amount:,.0f}` điểm ")

        if low_bet_members:
            bets_details_list_str = "\n".join(low_bet_members)
            await processing_message.edit_text(
                text=RESPONSE_MESSAGES["kl006_low_bet_members"].format(
                    yesterday_date=yesterday_date_str,
                    bets_details_list=bets_details_list_str
                ),
                reply_markup=back_to_menu_keyboard,
                parse_mode=ParseMode.MARKDOWN_V2
            )
            #context.user_data.clear()
            return ConversationHandler.END

        # === PHẦN 4: KIỂM TRA ĐIỀU KIỆN CHUNG CỦA NHÓM ===
        if "không đủ" in team_data["eligibility"].lower():
            group_total_bet = sum(member_bets_map.values())
            bets_details_list_str = "\n".join(all_members_bet_details)
            await processing_message.edit_text(
                text=RESPONSE_MESSAGES["kl006_group_ineligible"].format(
                    yesterday_date=yesterday_date_str,
                    bets_details_list=bets_details_list_str,
                    group_total_bet=group_total_bet
                ),
                reply_markup=back_to_menu_keyboard,
                parse_mode=ParseMode.MARKDOWN_V2
            )
            #context.user_data.clear()
            return ConversationHandler.END

        # === PHẦN 5: KIỂM TRA TRẠNG THÁI NHẬN THƯỞNG ===
        if team_data["claimed_status"]:
            await processing_message.edit_text(
                text=RESPONSE_MESSAGES["kl006_already_claimed"].format(yesterday_date=yesterday_date_str),
                reply_markup=back_to_menu_keyboard,
                parse_mode=ParseMode.MARKDOWN_V2
            )
            #context.user_data.clear()
            return ConversationHandler.END

        # === PHẦN 6: TRƯỜNG HỢP THÀNH CÔNG ===
        original_member_names = team_data['original_members']
        bonus_points = team_data.get('bonus', 'N/A')

        claim_id = await database.add_promo_claim(
            user_id=user.id, promo_code=promo_code,
            details={"members": original_member_names, "bonus_points": bonus_points}
        )

        usernames_md = ", ".join([f"`{escape_markdown(name, version=2)}`" for name in original_member_names])
        admin_text = (
            f"Yêu cầu {promo_code} \\(Nhóm {group_size}\\) \\- [{escape_markdown(user.first_name, version=2)}](tg://user?id={user.id})\n\n"
            f"**Thành viên:**\n{usernames_md}\n\n"
            f"🎁 **Điểm thưởng đề xuất:** `{bonus_points}`"
        )
        admin_keyboard = keyboards.create_admin_promo_buttons(claim_id, user.id, promo_code, usernames=original_member_names)

        await context.bot.send_message(
            chat_id=config.ID_GROUP_PROMO, text=admin_text,
            reply_markup=admin_keyboard, parse_mode=ParseMode.MARKDOWN_V2
        )

        await processing_message.edit_text(
            text=RESPONSE_MESSAGES["yeu_cau_dang_xu_ly"],
            reply_markup=back_to_menu_keyboard
        )
        increment_count_in_cache(user.id, "promo")

    except Exception as e:
        logger.error(f"Failed to process KL006 claim for user {user.id}: {e}", exc_info=True)
        await processing_message.edit_text(
            text=RESPONSE_MESSAGES["error_sending_request"],
            reply_markup=keyboards.create_cleanup_keyboard()
        )

    #context.user_data.clear()
    return ConversationHandler.END

kl006_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_kl006, pattern='^promo_KL006$')],
    states={
        AGREE_TERMS: [CallbackQueryHandler(ask_group_size, pattern='^agree_terms:KL006$')],
        CHOOSE_GROUP_SIZE: [CallbackQueryHandler(ask_for_usernames, pattern=r'^kl006_select_group:\d+$')],
        RECEIVE_USERNAMES: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_usernames)],
    },
    fallbacks=get_fallbacks(),
    block=False,
    per_message=False,
    name="kl006_conversation"
)