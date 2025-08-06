# features/admin_handlers.py
import asyncio
import logging
import json
import re
import telegram
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    CommandHandler
)
from telegram.helpers import escape_markdown
from telegram.constants import ParseMode
from telegram.ext.filters import BaseFilter
from core import database
from utils import helpers, keyboards
from utils.helpers import get_current_time_str
from texts import RESPONSE_MESSAGES
import config
from utils.decorators import log_callback_query
from features.fallbacks import get_fallbacks
from collections import defaultdict

logger = logging.getLogger(__name__)

AWAIT_GATEWAY, AWAIT_PROCESS_TIME, AWAIT_KL007_POINTS, AWAIT_WITHDRAW_RECEIPT = range(4)

class FilterByReplyText(BaseFilter):
    """
    Filter tùy chỉnh, trả về True nếu tin nhắn là một reply
    và nội dung của tin nhắn được reply có chứa một chuỗi text nhất định.
    """
    def __init__(self, text_to_find: str):
        # 1. GỌI INIT CỦA LỚP CHA VÀ THIẾT LẬP data_filter
        super().__init__(data_filter=True)
        self.text_to_find = text_to_find.lower()

    def filter(self, data: dict) -> bool:
        # 2. HÀM FILTER BÂY GIỜ NHẬN VÀO MỘT DICTIONARY
        # Lấy đối tượng message từ dictionary đó
        message = data.get('message')
        if not message or not message.reply_to_message:
            return False

        replied_text = (message.reply_to_message.text or message.reply_to_message.caption or "").lower()
        return self.text_to_find in replied_text

# Tạo các instance của filter để sử dụng trong admin_deposit_conv_handler
# Các đoạn text này PHẢI KHỚP với text mà bot gửi ra để yêu cầu admin reply
filter_gateway_reply = FilterByReplyText("tên cổng thanh toán")
filter_time_reply = FilterByReplyText("thời gian lên điểm")
filter_withdraw_receipt_reply = FilterByReplyText("gửi hóa đơn rút tiền")


@log_callback_query
async def handle_admin_promo_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles simple promo responses from admins (approve/reject)."""
    query = update.callback_query


    try:
        # admin_response:{claim_id}:{user_id}:{promo_code}:{action}
        _prefix, claim_id_str, user_id_str, promo_code, action = query.data.split(':', 4)
        claim_id = int(claim_id_str)
        user_id = int(user_id_str)
    except (ValueError, IndexError) as e:
        logger.error(f"Error parsing admin callback data: {query.data} - {e}")
        await query.edit_message_text(f"Lỗi callback data: {query.data}")
        return

    claim = await database.get_promo_claim(claim_id)
    if not claim:
        await query.reply_text(f"Lỗi: Yêu cầu ID {claim_id} không còn trong hàng đợi hoặc đã được xử lý.", reply_markup=None)
        return

    admin_user = query.from_user
    admin_mention = f"[{escape_markdown(admin_user.first_name, version=2)}](tg://user?id={admin_user.id})"

    # Generate response message for the customer
    customer_message_template = RESPONSE_MESSAGES.get(action)
    if customer_message_template:
        all_possible_vars = {
            'customer_username': escape_markdown(claim.get('game_username', '') or '', version=2), # Thêm or '' để đảm bảo không phải None
            'promo_code': promo_code,
            'yesterday_date': helpers.get_yesterday_dmy_str()
        }
        formatter = defaultdict(str, all_possible_vars)
        customer_message = customer_message_template.format_map(formatter)
    else:
        customer_message = ""

    if customer_message:


        customer_keyboard = keyboards.create_cleanup_keyboard()

        try:
            edited_message = await context.bot.send_message(
                chat_id=user_id,
                text=customer_message,
                reply_markup=customer_keyboard,
                parse_mode=ParseMode.MARKDOWN_V2
            )
            if user_id not in context.bot_data:
                context.bot_data[user_id] = {}
            if 'messages_to_delete' not in context.bot_data[user_id]:
                context.bot_data[user_id]['messages_to_delete'] = []

            context.bot_data[user_id]['messages_to_delete'].append(edited_message.message_id)
        except telegram.error.Forbidden:
            # Lỗi: Bot bị người dùng chặn
            error_reply = f"⚠️ Không thể gửi thông báo cho User ID `{user_id}`\\. Bot đã bị người dùng này chặn\\."
            logger.warning(f"Failed to send message to {user_id}: Bot was blocked.")
            await query.message.reply_text(
            text=error_reply,
            parse_mode=ParseMode.MARKDOWN_V2,
            )
        except telegram.error.BadRequest as e:
            # Lỗi: Có thể do người dùng xóa chat, hoặc một vấn đề khác
            if "Chat not found" in str(e):
                error_reply = f"⚠️ Không thể gửi thông báo cho User ID `{user_id}`\\. Không tìm thấy cuộc trò chuyện \\(có thể đã bị xóa\\)\\."
                logger.warning(f"Failed to send message to {user_id}: Chat not found.")
                await query.message.reply_text(
                text=error_reply,
                parse_mode=ParseMode.MARKDOWN_V2
                )
            else:
                # Một lỗi BadRequest khác không lường trước
                error_reply = f"⚠️ Lỗi BadRequest khi gửi tin cho User ID `{user_id}`: {e}"
                logger.error(f"Unexpected BadRequest when sending to {user_id}: {e}", exc_info=True)
                await query.message.reply_text(
                text=error_reply,
                parse_mode=ParseMode.MARKDOWN_V2,
                )
        except Exception as e:
            # Các lỗi không mong muốn khác
            error_reply = f"⚠️ Lỗi không xác định khi gửi tin cho User ID `{user_id}`\\."
            logger.error(f"Unexpected error sending to {user_id}: {e}", exc_info=True)
            await query.message.reply_text(
            text=error_reply,
            parse_mode=ParseMode.MARKDOWN_V2,
            )



    admin_mention = f"[{escape_markdown(query.from_user.first_name, version=2)}](tg://user?id={query.from_user.id})"
    time_str = get_current_time_str()
    action_text = action.replace('_', ' ').title()

    original_message = query.message

    original_text = original_message.caption_markdown_v2 if original_message.caption else original_message.text_markdown_v2
    original_text = original_text or "" # Đảm bảo là chuỗi

    processed_text = (
        f"{original_text}\n———\n"
        f"✅ Xử lý bởi {admin_mention} lúc {time_str}\\. "
        f"Hành động: *{action_text}*"
    )

    if original_message.caption:
        await query.edit_message_caption(caption=processed_text, reply_markup=None, parse_mode=ParseMode.MARKDOWN_V2)
    else:
        await query.edit_message_text(text=processed_text, reply_markup=None, parse_mode=ParseMode.MARKDOWN_V2)

    # Delete the claim from the queue
    await database.delete_promo_claim(claim_id)
    logger.info(f"Admin {admin_user.id} processed promo claim {claim_id} with action '{action}'. Claim deleted.")

@log_callback_query
async def handle_admin_share_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles share reward responses from admins."""
    query = update.callback_query


    try:
        # admin_share_resp:{claim_id}:{user_id}:{milestone}:{action}
        _prefix, claim_id_str, user_id_str, milestone_str, action = query.data.split(':', 4)
        claim_id = int(claim_id_str)
        user_id = int(user_id_str)
    except (ValueError, IndexError) as e:
        logger.error(f"Error parsing admin share callback data: {query.data} - {e}")
        await query.edit_message_text(f"Lỗi callback data: {query.data}")
        return

    claim = await  database.get_promo_claim(claim_id)
    if not claim:
        await query.edit_message_text(f"Lỗi: Yêu cầu chia sẻ ID {claim_id} không còn trong hàng đợi.", reply_markup=None)
        return

    details = json.loads(claim.get('details', '{}'))
    milestone = details.get('milestone', 'không rõ')
    game_username = claim.get('game_username', 'không rõ')
    reward_points = details.get('reward_points', 'không xác định')

    response_text = ""
    action_log_text = ""
    # Xử lý dựa trên hành động của admin
    if action == 'approved' or action == 'lam_dung':
        # Cả hai hành động này đều cần "duyệt" để chặn mốc
        success = await database.process_approved_share_claim(claim_id)

        if success:
            if action == 'approved':
                template = RESPONSE_MESSAGES.get('share_reward_approved')
                if template:
                    response_text = template.format(reward_points=reward_points)
                action_log_text = "Thành Công"

            elif action == 'lam_dung':
                response_text = RESPONSE_MESSAGES.get('admin_resp_lam_dung')
                action_log_text = "Lạm Dụng (Đã chặn mốc)"
        else:
            # Xử lý trường hợp process_approved_share_claim thất bại
            action_log_text = "Lỗi Xử Lý (Xem Log)"
            await query.message.reply_text(f"⚠️ Có lỗi xảy ra khi xử lý claim #{claim_id}. Vui lòng kiểm tra log.")


    else: # Các trường hợp từ chối (sai_id, cskh, etc.)
        await database.delete_promo_claim(claim_id)

        # Lấy mẫu tin nhắn dựa trên action
        # Ví dụ: action='sai_id' -> key='admin_resp_sai_id'
        customer_message_key = f"share_reward_{action}"
        template = RESPONSE_MESSAGES.get(customer_message_key)

        if template:
            try:
                response_text = template.format(
                    milestone=milestone,
                    game_username=game_username,
                    reward_points=reward_points
                )
            except KeyError:
                response_text = template

    action_log_text = action.replace('_', ' ').title()


    if response_text:
        try:


            customer_keyboard = keyboards.create_cleanup_keyboard()
            send_message = await context.bot.send_message(
                chat_id=user_id,
                text=response_text,
                reply_markup=customer_keyboard,
                parse_mode=ParseMode.MARKDOWN_V2
            )
            if user_id not in context.bot_data:
                context.bot_data[user_id] = {}
            if 'messages_to_delete' not in context.bot_data[user_id]:
                context.bot_data[user_id]['messages_to_delete'] = []

            context.bot_data[user_id]['messages_to_delete'].append(send_message.message_id)
        except Exception as e:
            logger.error(f"Failed to send share response for claim {claim_id} to user {user_id}: {e}")

    # Cập nhật tin nhắn trong nhóm admin
    admin_mention = f"[{escape_markdown(query.from_user.first_name, version=2)}](tg://user?id={query.from_user.id})"
    original_text = query.message.text_markdown_v2
    processed_text = (
        f"{original_text}\n———\n"
        f"✅ Xử lý bởi {admin_mention} lúc {helpers.get_current_time_str()}\\. "
        f"Hành động: *{action_log_text}*\\."
    )
    await query.edit_message_text(text=processed_text, reply_markup=None, parse_mode=ParseMode.MARKDOWN_V2)

    logger.info(f"Admin {query.from_user.id} processed share claim {claim_id} with action '{action}'.")

@log_callback_query
async def handle_admin_kl006_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Xử lý các phản hồi của admin cho khuyến mãi KL006.
    """
    query = update.callback_query

    try:
        # Tách callback_data: admin_kl006:{claim_id}:{user_id}:{member_specifier}:{action}
        _prefix, claim_id_str, user_id_str, member_specifier, action = query.data.split(':', 4)
        claim_id = int(claim_id_str)
        user_id = int(user_id_str)
    except (ValueError, IndexError) as e:
        logger.error(f"Lỗi bóc tách callback data KL006: {query.data} - {e}")
        await query.answer("Lỗi: Callback data không hợp lệ!", show_alert=True)
        return

    # Lấy thông tin yêu cầu từ CSDL
    claim = await database.get_promo_claim(claim_id)
    if not claim:
        await query.answer("Lỗi: Yêu cầu này đã được xử lý hoặc không tồn tại.", show_alert=True)
        await query.edit_message_reply_markup(reply_markup=None)
        return

    # Chuẩn bị thông tin cho các bước tiếp theo
    admin_user = query.from_user
    admin_mention = f"[{escape_markdown(admin_user.first_name, version=2)}](tg://user?id={admin_user.id})"
    customer_message = ""
    affected_username = ""
    action_description_for_admin = ""

    # --- YÊU CẦU 2: PHẢN HỒI POP-UP VÀ CHUẨN BỊ TIN NHẮN CHO USER ---
    if member_specifier != 'GROUP':
        try:
            member_index = int(member_specifier)
            details = json.loads(claim['details'])
            usernames = details.get('members', [])
            affected_username = usernames[member_index]

            # Hiển thị pop-up cho admin
            await query.answer(f"Đã ghi nhận hành động cho thành viên: {affected_username}")
            action_description_for_admin = f"Lý do: {action.replace('_', ' ')} (Thành viên: {affected_username})"

        except (ValueError, IndexError, KeyError) as e:
            logger.error(f"Không thể lấy thông tin thành viên cho claim KL006 {claim_id}: {e}")
            await query.answer("Lỗi: Không tìm thấy thông tin thành viên.", show_alert=True)
            return
    else:
        # Hành động cho cả nhóm
        await query.answer(f"Đã ghi nhận hành động cho toàn bộ nhóm.")
        action_description_for_admin = f"Lý do: {action.replace('_', ' ')} (Cả nhóm)"


    # Lấy mẫu tin nhắn từ texts.py và định dạng nó
    customer_message_key = f"kl006_{action}"
    message_template = RESPONSE_MESSAGES.get(customer_message_key)

    if message_template:
        try:
            # Lấy ngày hôm qua từ hàm helper
            yesterday_str = helpers.get_yesterday_dmy_str()

            # Định dạng chuỗi với tất cả các biến cần thiết
            customer_message = message_template.format(
                username=affected_username,
                yesterday_date=yesterday_str
            )
        except KeyError as e:
            # Xử lý nếu một chuỗi không cần cả hai placeholder
            logger.warning(f"KeyError khi format tin nhắn KL006, có thể do thiếu placeholder: {e}")
            customer_message = message_template
    else:
        customer_message = "Yêu cầu của bạn đã được xử lý."
        logger.warning(f"Không tìm thấy message template cho key: {customer_message_key}")

    # Gửi tin nhắn phản hồi cho người dùng
    try:


        customer_keyboard = keyboards.create_cleanup_keyboard()
        send_message = await context.bot.send_message(
            chat_id=user_id,
            text=customer_message,
            reply_markup=customer_keyboard,
            parse_mode=ParseMode.MARKDOWN_V2
        )
        if user_id not in context.bot_data:
                context.bot_data[user_id] = {}
        if 'messages_to_delete' not in context.bot_data[user_id]:
            context.bot_data[user_id]['messages_to_delete'] = []

        context.bot_data[user_id]['messages_to_delete'].append(send_message.message_id)



    except Exception as e:
        logger.error(f"Không thể gửi phản hồi KL006 cho user {user_id}: {e}")

    # Sửa tin nhắn trong nhóm admin để ghi nhận đã xử lý
    original_text_md = query.message.text_markdown_v2
    processed_text = (
        f"{original_text_md}\n———\n"
        f"✅ *ĐÃ XỬ LÝ* bởi {admin_mention} lúc {helpers.get_current_time_str()}\n"
        f"➡️ {escape_markdown(action_description_for_admin, version=2)}"
    )

    try:
        await query.edit_message_text(
            text=processed_text,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=None
        )
    except Exception as e:
        logger.error(f"Không thể sửa tin nhắn admin cho claim KL006 {claim_id}: {e}")

    await database.delete_promo_claim(claim_id)
    logger.info(f"Admin {admin_user.id} đã xử lý claim KL006 {claim_id}. Yêu cầu đã bị xóa.")

@log_callback_query
async def handle_admin_kl007_point_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
     Admin reply số điểm. Bot sẽ kiểm tra xem yêu cầu đã được xử lý chưa.
    """
    message = update.message
    replied = message.reply_to_message # Đây là tin nhắn yêu cầu gốc của bot

    # --- BƯỚC 1: KIỂM TRA ĐIỀU KIỆN BAN ĐẦU ---
    if not replied or not replied.from_user.is_bot or message.chat_id != config.ID_GROUP_KL007:
        return

    # --- BƯỚC 2: KIỂM TRA TRẠNG THÁI "ĐÃ XỬ LÝ" ---
    original_text = replied.text or replied.caption or ""
    if "\u200b" in original_text:
        await context.bot.send_message(
            chat_id=message.chat_id,
            text="⚠️ Yêu cầu này đã được xử lý xong.",
            reply_to_message_id=message.message_id # Trả lời lại tin nhắn của admin
        )
        return

    # --- BƯỚC 3: XỬ LÝ INPUT CỦA ADMIN (Code cũ của bạn giữ nguyên) ---
    text = message.text.strip()
    match = re.match(r'^\+?(\d+)$', text)
    if not match:
        # Nếu không phải là số, chúng ta có thể phớt lờ thay vì báo lỗi
        logger.info(f"Admin reply với text không phải số điểm ('{text}'), bot phớt lờ.")
        # Tùy chọn: Xóa tin nhắn reply không hợp lệ của admin
        return

    delta = int(match.group(1))

    # Logic phớt lờ các số nhỏ của bạn vẫn rất hữu ích
    if delta < 9:
        logger.info(f"Admin reply với số nhỏ ({delta}), bot phớt lờ.")
        return

    # --- BƯỚC 4: XỬ LÝ LOGIC CHÍNH (Code cũ của bạn giữ nguyên) ---
    id_match = re.search(r'UID:\s*(\d+)', original_text)
    if not id_match:
        await message.reply_text("Không xác định được User ID từ tin nhắn gốc.")
        return
    target_user_id = int(id_match.group(1))

    # Thông báo cho user
    try:


        customer_keyboard = keyboards.create_cleanup_keyboard()
        send_message = await context.bot.send_message(
            chat_id=target_user_id,
            text=RESPONSE_MESSAGES["kl007_points_added"].format(points=delta),
            reply_markup=customer_keyboard,
            parse_mode=ParseMode.MARKDOWN_V2
        )
        user_id = target_user_id
        if user_id not in context.bot_data:
            context.bot_data[user_id] = {}
        if 'messages_to_delete' not in context.bot_data[user_id]:
            context.bot_data[user_id]['messages_to_delete'] = []

        context.bot_data[user_id]['messages_to_delete'].append(send_message.message_id)


    except Exception as e:
        logger.error(f"KL007: lỗi gửi tin nhắn cộng điểm cho {target_user_id}: {e}")

    admin_user = message.from_user
    admin_mention = f"[{escape_markdown(admin_user.first_name, version=2)}](tg://user?id={admin_user.id})"
    original_text_md = replied.text_markdown_v2 or replied.caption_markdown_v2 or ""
    PROCESSED_TAG = "\n\u200b"
    processed_text = (
        f"{original_text_md}\n———\n"
        f"✅ *ĐÃ XỬ LÝ* bởi {admin_mention} lúc {helpers.get_current_time_str()}\n"
        f"➡️ *{delta} điểm*"
        f"{PROCESSED_TAG}"
    )

    try:
        await context.bot.edit_message_text(
            text=processed_text,
            chat_id=replied.chat_id,
            message_id=replied.message_id,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=None  # Xóa các nút bấm sau khi đã xử lý
        )
    except Exception as e:
        logger.error(f"Không thể sửa tin nhắn admin cho claim KL007 của user {target_user_id}: {e}")


async def share_add_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    (Admin only) Thêm hoặc bớt thủ công lượt chia sẻ cho người dùng.
    Cú pháp: /shareadd <user_id> <số_lượt>
    Ví dụ:
    /shareadd 12345 5   (để cộng 5 lượt)
    /shareadd 12345 -2  (để trừ 2 lượt)
    """
    # 1. Kiểm tra quyền Admin
    if update.effective_user.id not in config.ADMIN_IDS:
        return  # Bỏ qua trong im lặng nếu không phải admin

    # 2. Kiểm tra cú pháp lệnh
    if not context.args or len(context.args) != 2:
        await update.message.reply_text(
            "Cú pháp sai\\. Sử dụng: `/shareadd <USER_ID> <SỐ_LƯỢT>`\n"
            "Ví dụ: `/shareadd 12345 5` hoặc `/shareadd 12345 -2`",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return

    # 3. Phân tích các tham số
    try:
        target_user_id = int(context.args[0])
        # Đổi tên biến cho rõ nghĩa
        shares_delta = int(context.args[1])
    except ValueError:
        await update.message.reply_text("USER\\_ID và SỐ\\_LƯỢT phải là số nguyên\\.", parse_mode=ParseMode.MARKDOWN_V2)
        return

    if shares_delta == 0:
        await update.message.reply_text("Số lượt thay đổi phải khác 0\\.", parse_mode=ParseMode.MARKDOWN_V2)
        return

    # 4. Gọi hàm database để cập nhật
    success, new_total = await database.add_shares_to_user(target_user_id, shares_delta)

    # 5. Phản hồi kết quả chi tiết cho admin
    if success:
        if shares_delta > 0:
            action_text = f"cộng thêm *{shares_delta}*"
        else:
            action_text = f"trừ đi *{abs(shares_delta)}*" # abs() để hiển thị số dương

        await update.message.reply_text(
            f"✅ Thành công\\!\n"
            f"Đã {action_text} lượt chia sẻ cho User ID `{target_user_id}`\\.\n"
            f"Tổng số lượt mới: *{new_total}*",
            parse_mode=ParseMode.MARKDOWN_V2
        )
    else:
        await update.message.reply_text(
            f"❌ Thất bại\\.\n"
            f"Không thể xử lý lượt chia sẻ cho User ID `{target_user_id}`\\.\n\n"
            f"Lý do có thể: người dùng chưa từng tương tác với bot, hoặc bạn đang cố trừ điểm cho người chưa có trong danh sách chia sẻ\\.",
            parse_mode=ParseMode.MARKDOWN_V2
        )


# --- Conversation cho các nút cần admin nhập liệu ---

async def ask_for_gateway(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Entry point, hỏi admin tên cổng thanh toán.
    Lưu context của yêu cầu vào chat_data bằng message_id.
    Nhúng message_id vào tin nhắn prompt.
    """
    query = update.callback_query
    await query.answer()

    try:
        # Trích xuất user_id từ callback_data
        _, user_id_str, _ = query.data.split(':')
        user_id = int(user_id_str)

        # Lấy tin nhắn gốc mà admin đã tương tác
        original_message = query.message

        # Sử dụng chat_data để lưu thông tin theo từng cuộc hội thoại của nhóm admin.
        # Key là message_id của tin nhắn gốc để đảm bảo tính duy nhất.
        context.chat_data[original_message.message_id] = {
            'target_user_id': user_id,
            'original_message': original_message
        }

        # Tạo tin nhắn prompt, nhúng ID của tin nhắn gốc vào để tham chiếu sau này
        prompt_text = (
            f"Vui lòng trả lời (reply) tin nhắn này với Tên cổng thanh toán.\n"
            f"Ref Msg ID: {original_message.message_id}"
        )
        await query.message.reply_text(prompt_text)

        return AWAIT_GATEWAY

    except (ValueError, IndexError) as e:
        logger.error(f"Lỗi khi bắt đầu luồng hỏi cổng thanh toán: {e}")
        await query.message.reply_text("Lỗi: Dữ liệu callback không hợp lệ.")
        return ConversationHandler.END


async def receive_gateway_and_notify(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Nhận tên cổng, trích xuất ID tham chiếu từ tin nhắn được reply,
    lấy đúng context, gửi thông báo cho user và edit tin nhắn gốc.
    """
    admin = update.effective_user
    gateway_name = update.message.text.strip()
    replied_message = update.message.reply_to_message

    # 1. Trích xuất Ref Msg ID từ tin nhắn được reply
    try:
        match = re.search(r"Ref Msg ID: (\d+)", replied_message.text)
        if not match:
            # Nếu không tìm thấy ID, có thể admin reply nhầm tin nhắn
            await update.message.reply_text("Vui lòng trả lời đúng tin nhắn yêu cầu Tên cổng thanh toán.")
            return AWAIT_GATEWAY # Giữ nguyên state, chờ reply đúng

        original_message_id = int(match.group(1))

        # 2. Lấy lại context của đúng yêu cầu từ chat_data
        request_context = context.chat_data.get(original_message_id)
        if not request_context:
            await update.message.reply_text("Lỗi: Yêu cầu này đã hết hạn hoặc đã được xử lý. Vui lòng bắt đầu lại.")
            return ConversationHandler.END

        target_user_id = request_context['target_user_id']
        original_message = request_context['original_message']

    except (AttributeError, ValueError) as e:
        await update.message.reply_text(f"Lỗi: Không thể xác định yêu cầu gốc. {e}")
        return ConversationHandler.END

    # 3. Gửi tin nhắn cho khách hàng
    try:
        message_to_customer = RESPONSE_MESSAGES["deposit_lam_lai_lenh"].format(
            payment_gateway=escape_markdown(gateway_name, version=2)
        )


        customer_keyboard = keyboards.create_cleanup_keyboard()
        send_message = await context.bot.send_message(
            chat_id=target_user_id,
            text=message_to_customer,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=customer_keyboard
        )
        user_id = target_user_id
        if user_id not in context.bot_data:
                context.bot_data[user_id] = {}
        if 'messages_to_delete' not in context.bot_data[user_id]:
                context.bot_data[user_id]['messages_to_delete'] = []

        context.bot_data[user_id]['messages_to_delete'].append(send_message.message_id)


        await update.message.reply_text(f"✅ Đã gửi yêu cầu làm lại lệnh với cổng '{gateway_name}' cho User ID {target_user_id}.")
    except Exception as e:
        logger.error(f"Failed to send 'lam_lai_lenh' message to user {target_user_id}: {e}")
        await update.message.reply_text(f"❌ Lỗi khi gửi tin nhắn đến User ID {target_user_id}: {e}")

    # 4. Chỉnh sửa lại tin nhắn gốc trong nhóm admin
    try:
        admin_mention = f"[{escape_markdown(admin.first_name, version=2)}](tg://user?id={admin.id})"
        original_caption = original_message.caption_markdown_v2 or ""
        processed_caption = (
            f"{original_caption}\n———\n"
            f"✅ Xử lý bởi {admin_mention} lúc {helpers.get_current_time_str()}\\.\n"
            f"Hành động: *Làm lại lệnh* \\(Cổng: *{escape_markdown(gateway_name, version=2)}*\\)"
        )

        # Edit tường minh, không cần helper ở đây
        if original_message.caption is not None:
             await context.bot.edit_message_caption(
                chat_id=original_message.chat_id, message_id=original_message.message_id,
                caption=processed_caption, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=None
            )
        else:
             await context.bot.edit_message_text(
                chat_id=original_message.chat_id, message_id=original_message.message_id,
                text=processed_caption, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=None
            )
    except Exception as e:
        logger.error(f"Failed to edit original admin message for ID {original_message_id}: {e}")

    # 5. Dọn dẹp context cho yêu cầu này và kết thúc
    if original_message_id in context.chat_data:
        del context.chat_data[original_message_id]

    return ConversationHandler.END

async def handle_admin_deposit_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý các nút bấm đơn giản cho yêu cầu Hỗ trợ Nạp tiền."""
    query = update.callback_query
    await query.answer()


    try:
        # Format: admin_deposit:<user_id>:<action>
        _, user_id_str, action = query.data.split(':')
        user_id = int(user_id_str)
    except (ValueError, IndexError):
        logger.error(f"Invalid callback data format for deposit response: {query.data}")
        await query.edit_message_reply_markup(reply_markup=None)
        return

    # Lấy mẫu tin nhắn từ `texts.py` với prefix 'deposit_'
    # Ví dụ action là 'sai_id', key sẽ là 'deposit_sai_id'
    customer_message_template = RESPONSE_MESSAGES.get(f"deposit_{action}")

    if customer_message_template:
        try:
            # Gửi tin nhắn phản hồi cho khách hàng


            customer_keyboard = keyboards.create_cleanup_keyboard()
            send_message = await context.bot.send_message(
                chat_id=user_id,
                text=customer_message_template,
                reply_markup=customer_keyboard,
                parse_mode=ParseMode.MARKDOWN_V2
            )


            if user_id not in context.bot_data:
                context.bot_data[user_id] = {}
            if 'messages_to_delete' not in context.bot_data[user_id]:
                context.bot_data[user_id]['messages_to_delete'] = []

            context.bot_data[user_id]['messages_to_delete'].append(send_message.message_id)
        except telegram.error.Forbidden:
            logger.warning(f"Failed to send DEPOSIT response to {user_id}: Bot was blocked.")
        except Exception as e:
            logger.error(f"Failed to send DEPOSIT response for action '{action}' to user {user_id}: {e}")

    # Edit tin nhắn admin để đánh dấu đã xử lý
    admin_mention = f"[{escape_markdown(query.from_user.first_name, version=2)}](tg://user?id={query.from_user.id})"
    action_text = action.replace('_', ' ').title()

    # Dùng hàm helper an toàn để edit
    original_caption = query.message.caption_markdown_v2 or ""
    processed_text = (
        f"{original_caption}\n———\n"
        f"✅ Xử lý bởi {admin_mention} lúc {helpers.get_current_time_str()}\\. "
        f"Hành động: *{action_text}*"
    )
    await helpers.edit_message_safely(query, processed_text, None)

async def ask_for_input(update: Update, context: ContextTypes.DEFAULT_TYPE, prompt: str, next_state: int) -> int:
    """Hàm chung để hỏi admin nhập liệu."""
    query = update.callback_query
    await query.answer()
    try:
        _, user_id_str, _ = query.data.split(':')
        context.user_data['target_user_id'] = int(user_id_str)
        context.user_data['original_message'] = query.message
        await query.message.reply_text(prompt)
        return next_state
    except (ValueError, IndexError):
        await query.message.reply_text("Lỗi: Dữ liệu callback không hợp lệ.")
        return ConversationHandler.END



async def ask_for_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Entry point, hỏi admin thời gian lên điểm.
    Lưu context của yêu cầu vào chat_data bằng message_id và nhúng ID đó vào prompt.
    """
    query = update.callback_query
    await query.answer()

    try:
        # Trích xuất user_id từ callback_data (ví dụ: 'admin_deposit:12345:da_len_diem')
        _, user_id_str, _ = query.data.split(':')
        user_id = int(user_id_str)

        # Lấy tin nhắn gốc mà admin đã tương tác
        original_message = query.message

        # Sử dụng chat_data để lưu thông tin theo từng cuộc hội thoại của nhóm admin.
        # Key là message_id của tin nhắn gốc để đảm bảo tính duy nhất.
        if not context.chat_data:
            context.chat_data.clear()

        context.chat_data[original_message.message_id] = {
            'target_user_id': user_id,
            'original_message': original_message
        }

        # Tạo tin nhắn prompt, nhúng ID của tin nhắn gốc vào để tham chiếu sau này
        prompt_text = (
            f"Vui lòng trả lời (reply) tin nhắn này với thời gian lên điểm.\n"
            f"Định dạng: YYYY/MM/DD HH:MM\n"
            f"Ref Msg ID: {original_message.message_id}"
        )
        await query.message.reply_text(prompt_text)

        return AWAIT_PROCESS_TIME

    except (ValueError, IndexError) as e:
        logger.error(f"Lỗi khi bắt đầu luồng hỏi thời gian lên điểm: {e}")
        await query.message.reply_text("Lỗi: Dữ liệu callback không hợp lệ.")
        return ConversationHandler.END


async def receive_time_and_notify(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Nhận thời gian, trích xuất ID tham chiếu từ tin nhắn được reply,
    lấy đúng context, gửi thông báo cho user và edit tin nhắn gốc.
    """
    # 1. Lấy thông tin từ update và tin nhắn được reply
    admin = update.effective_user
    process_time = update.message.text.strip()
    replied_message = update.message.reply_to_message

    # 2. Trích xuất Ref Msg ID và lấy lại context của yêu cầu
    try:
        match = re.search(r"Ref Msg ID: (\d+)", replied_message.text)
        if not match:
            # Nếu không tìm thấy ID, admin có thể đã reply nhầm tin nhắn
            await update.message.reply_text("Vui lòng trả lời đúng tin nhắn yêu cầu thời gian lên điểm.")
            return AWAIT_PROCESS_TIME # Giữ nguyên state, chờ reply đúng

        original_message_id = int(match.group(1))

        # Lấy lại context của đúng yêu cầu từ chat_data
        request_context = context.chat_data.get(original_message_id)
        if not request_context:
            await update.message.reply_text("Lỗi: Yêu cầu này đã hết hạn hoặc đã được xử lý. Vui lòng bắt đầu lại.")
            return ConversationHandler.END

        target_user_id = request_context['target_user_id']
        original_message = request_context['original_message']

    except (AttributeError, ValueError) as e:
        await update.message.reply_text(f"Lỗi: Không thể xác định yêu cầu gốc. {e}")
        return ConversationHandler.END

    # 3. Gửi tin nhắn thông báo cho khách hàng
    try:
        message_to_customer = RESPONSE_MESSAGES["deposit_da_len_diem"].format(
            process_time=escape_markdown(process_time, version=2)
        )


        customer_keyboard = keyboards.create_cleanup_keyboard()
        send_message = await context.bot.send_message(
            chat_id=target_user_id,
            text=message_to_customer,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=customer_keyboard
        )

        user_id = target_user_id
        if user_id not in context.bot_data:
                context.bot_data[user_id] = {}
        if 'messages_to_delete' not in context.bot_data[user_id]:
            context.bot_data[user_id]['messages_to_delete'] = []

        context.bot_data[user_id]['messages_to_delete'].append(send_message.message_id)
        await update.message.reply_text(f"✅ Đã gửi thông báo lên điểm vào lúc '{process_time}' cho User ID {target_user_id}.")
    except Exception as e:
        logger.error(f"Failed to send 'da_len_diem' message to user {target_user_id}: {e}")
        await update.message.reply_text(f"❌ Lỗi khi gửi tin nhắn đến User ID {target_user_id}: {e}")

    # 4. Chỉnh sửa lại tin nhắn gốc trong nhóm admin
    try:
        admin_mention = f"[{escape_markdown(admin.first_name, version=2)}](tg://user?id={admin.id})"
        original_caption = original_message.caption_markdown_v2 or ""
        processed_caption = (
            f"{original_caption}\n———\n"
            f"✅ Xử lý bởi {admin_mention} lúc {helpers.get_current_time_str()}\\.\n"
            f"Hành động: *Đã lên điểm* \\(Lúc: *{escape_markdown(process_time, version=2)}*\\)"
        )

        # Logic edit tường minh, không dùng helper
        if original_message.caption is not None:
             await context.bot.edit_message_caption(
                chat_id=original_message.chat_id, message_id=original_message.message_id,
                caption=processed_caption, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=None
            )
        else:
             await context.bot.edit_message_text(
                chat_id=original_message.chat_id, message_id=original_message.message_id,
                text=processed_caption, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=None
            )
    except Exception as e:
        logger.error(f"Failed to edit original admin message for ID {original_message_id}: {e}")

    # 5. Dọn dẹp context cho yêu cầu này và kết thúc
    if original_message_id in context.chat_data:
        del context.chat_data[original_message_id]

    return ConversationHandler.END

async def handle_admin_withdraw_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý các nút bấm cho yêu cầu Hỗ trợ Rút Tiền."""
    query = update.callback_query
    await query.answer()

    try:
        # Format: admin_withdraw:<user_id>:<action>
        _, user_id_str, action = query.data.split(':')
        user_id = int(user_id_str)
    except (ValueError, IndexError):
        logger.error(f"Invalid callback data format for withdraw response: {query.data}")
        await helpers.edit_message_safely(query, "Lỗi: Dữ liệu callback không hợp lệ.", None)
        return

    # Lấy mẫu tin nhắn từ `texts.py` với prefix 'withdraw_'
    customer_message_template = RESPONSE_MESSAGES.get(f"withdraw_{action}")

    if customer_message_template:
        try:
            # Gửi tin nhắn phản hồi cho khách hàng


            customer_keyboard = keyboards.create_cleanup_keyboard()
            send_message = await context.bot.send_message(
                chat_id=user_id,
                text=customer_message_template,
                reply_markup=customer_keyboard,
                parse_mode=ParseMode.MARKDOWN_V2
            )


            if user_id not in context.bot_data:
                context.bot_data[user_id] = {}
            if 'messages_to_delete' not in context.bot_data[user_id]:
                context.bot_data[user_id]['messages_to_delete'] = []

            context.bot_data[user_id]['messages_to_delete'].append(send_message.message_id)
        except Exception as e:
            # Xử lý các lỗi như bị chặn, xóa chat
            logger.error(f"Failed to send WITHDRAW response for action '{action}' to user {user_id}: {e}")
            await query.message.reply_text(f"⚠️ Không thể gửi thông báo cho User ID `{user_id}`\\. Lỗi: {e}", parse_mode=ParseMode.MARKDOWN_V2)


    # Edit tin nhắn admin để đánh dấu đã xử lý
    admin_mention = f"[{escape_markdown(query.from_user.first_name, version=2)}](tg://user?id={query.from_user.id})"
    action_text = action.replace('_', ' ').title()

    original_content = query.message.text_markdown_v2 or ""
    processed_text = (
        f"{original_content}\n———\n"
        f"✅ Xử lý bởi {admin_mention} lúc {helpers.get_current_time_str()}\\. "
        f"Hành động: *{action_text}*"
    )
    await helpers.edit_message_safely(query, processed_text, None)

async def ask_for_withdraw_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Entry point, yêu cầu admin gửi ảnh hóa đơn rút tiền.
    """
    query = update.callback_query
    await query.answer()
    try:
        # Format: admin_withdraw:<user_id>:gui_hd
        _, user_id_str, _ = query.data.split(':')

        # Lưu thông tin cần thiết vào chat_data để xử lý song song
        original_message = query.message
        context.chat_data[original_message.message_id] = {
            'target_user_id': int(user_id_str),
            'original_message': original_message
        }

        # Tạo tin nhắn prompt
        prompt_text = (
            f"Vui lòng trả lời (reply) tin nhắn này với hình ảnh hóa đơn rút tiền.\n"
            f"Hóa đơn sẽ được gửi đến User ID: {user_id_str}.\n"
            f"Ref Msg ID: {original_message.message_id}"
        )
        await query.message.reply_text(prompt_text)

        return AWAIT_WITHDRAW_RECEIPT

    except (ValueError, IndexError) as e:
        logger.error(f"Lỗi khi bắt đầu luồng hỏi hóa đơn rút tiền: {e}")
        await query.message.reply_text("Lỗi: Dữ liệu callback không hợp lệ.")
        return ConversationHandler.END


async def receive_withdraw_receipt_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Nhận ảnh hóa đơn từ admin, gửi cho khách hàng, và cập nhật tin nhắn gốc.
    """
    admin = update.effective_user
    replied_message = update.message.reply_to_message

    # 1. Trích xuất Ref Msg ID và lấy lại context của yêu cầu
    try:
        match = re.search(r"Ref Msg ID: (\d+)", replied_message.text)
        if not match:
            await update.message.reply_text("Vui lòng trả lời đúng tin nhắn yêu cầu hóa đơn.")
            return AWAIT_WITHDRAW_RECEIPT

        original_message_id = int(match.group(1))
        request_context = context.chat_data.get(original_message_id)
        if not request_context:
            await update.message.reply_text("Lỗi: Yêu cầu này đã hết hạn hoặc đã được xử lý.")
            return ConversationHandler.END

        target_user_id = request_context['target_user_id']
        original_message = request_context['original_message']

    except (AttributeError, ValueError) as e:
        await update.message.reply_text(f"Lỗi: Không thể xác định yêu cầu gốc. {e}")
        return ConversationHandler.END

    # 2. Gửi ảnh hóa đơn cho khách hàng
    try:
        receipt_photo_id = update.message.photo[-1].file_id


        customer_keyboard = keyboards.create_cleanup_keyboard()
        send_message = await context.bot.send_photo(
            chat_id=target_user_id,
            photo=receipt_photo_id,
            caption="Đây là hóa đơn/biên lai cho giao dịch rút tiền của bạn.",
            reply_markup=customer_keyboard
        )

        user_id = target_user_id
        if user_id not in context.bot_data:
            context.bot_data[target_user_id] = {}
        if 'messages_to_delete' not in context.bot_data[user_id]:
            context.bot_data[user_id]['messages_to_delete'] = []

        context.bot_data[user_id]['messages_to_delete'].append(send_message.message_id)
        await update.message.reply_text(f"✅ Đã gửi hóa đơn cho User ID {target_user_id}.")
    except Exception as e:
        logger.error(f"Failed to send withdraw receipt to user {target_user_id}: {e}")
        await update.message.reply_text(f"❌ Lỗi khi gửi hóa đơn đến User ID {target_user_id}: {e}")

    # 3. Chỉnh sửa lại tin nhắn gốc trong nhóm admin
    try:
        admin_mention = f"[{escape_markdown(admin.first_name, version=2)}](tg://user?id={admin.id})"
        original_content = original_message.text_markdown_v2 or ""
        processed_text = (
            f"{original_content}\n———\n"
            f"✅ Xử lý bởi {admin_mention} lúc {helpers.get_current_time_str()}\\.\n"
            f"Hành động: *Đã Gửi Hóa Đơn*"
        )

        if original_message.caption is not None:
             await context.bot.edit_message_caption(
                chat_id=original_message.chat_id,
                message_id=original_message.message_id,
                caption=processed_text,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=None # Xóa bàn phím
            )
        else:
             await context.bot.edit_message_text(
                chat_id=original_message.chat_id,
                message_id=original_message.message_id,
                text=processed_text,
                parse_mode=ParseMode.MARKDOWN_V2,
                reply_markup=None # Xóa bàn phím
            )

    except telegram.error.BadRequest as e:
        # Bỏ qua lỗi 'Message is not modified' một cách an toàn
        if "Message is not modified" not in str(e):
             logger.error(f"Lỗi BadRequest khi edit tin nhắn admin: {e}")
    except Exception as e:
        logger.error(f"Failed to edit original admin message for ID {original_message.message_id}: {e}")

    # 4. Dọn dẹp context và kết thúc
    if original_message_id in context.chat_data:
        del context.chat_data[original_message_id]

    return ConversationHandler.END


async def delcid_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    (Admin only) Xóa tất cả các yêu cầu đang chờ trong promo_claims của một user.
    Cú pháp: /delban <USER_ID>
    """
    # 1. KIỂM TRA QUYỀN ADMIN - Rất quan trọng!
    if update.effective_user.id not in config.ADMIN_IDS:
        return # Bỏ qua trong im lặng nếu không phải admin

    # 2. KIỂM TRA CÚ PHÁP LỆNH
    if not context.args or len(context.args) != 1:
        await update.message.reply_text(
            "Cú pháp sai\\. Dùng: `/delban <USER_ID>`",
            parse_mode=ParseMode.MARKDOWN_V2
        )
        return

    # 3. PHÂN TÍCH USER_ID
    try:
        target_user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("USER\\_ID phải là một con số\\.", parse_mode=ParseMode.MARKDOWN_V2)
        return

    # 4. GỌI HÀM DATABASE VÀ LẤY KẾT QUẢ
    deleted_count = await database.clear_all_claims_for_user(target_user_id)

    # 5. GỬI PHẢN HỒI CHO ADMIN
    admin_name = update.effective_user.first_name
    if deleted_count > 0:
        reply_text = (
            f"✅ Admin *{escape_markdown(admin_name, version=2)}* đã xóa thành công "
            f"*{deleted_count}* yêu cầu đang chờ của User ID `{target_user_id}`\\."
        )
    else:
        reply_text = (
            f"ℹ️ Không tìm thấy yêu cầu nào đang chờ của User ID `{target_user_id}` để xóa\\."
        )

    await update.message.reply_text(reply_text, parse_mode=ParseMode.MARKDOWN_V2)



async def resend_pending_claims_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    (Admin only) Quét và gửi lại tất cả các yêu cầu đang chờ xử lý.
    """
    # 1. KIỂM TRA QUYỀN ADMIN
    if update.effective_user.id not in config.ADMIN_IDS:
        return

    admin_message = await update.message.reply_text("🔍 Bắt đầu quét và gửi lại các yêu cầu đang chờ...")

    # 2. LẤY DANH SÁCH YÊU CẦU "MỒ CÔI"
    pending_claims = await database.get_all_pending_claims()

    if not pending_claims:
        await admin_message.edit_text("✅ Không tìm thấy yêu cầu nào đang chờ để gửi lại.")
        return

    # 3. VÒNG LẶP GỬI LẠI
    success_count = 0
    fail_count = 0

    for claim in pending_claims:
        claim_id_for_log = claim.get('claim_id', 'N/A')
        try:
            claim_id = claim['claim_id']
            user_id = claim['user_id']
            promo_code = claim['promo_code']
            game_username = claim.get('game_username', '')
            details = json.loads(claim.get('details', '{}'))

            # Tái tạo lại tin nhắn và bàn phím cho admin
            admin_text = ""
            admin_keyboard = None
            target_admin_group = config.ID_GROUP_PROMO

            if promo_code == 'SHARING':
                milestone = details.get('milestone', 'N/A')
                reward_points = details.get('reward_points', 'N/A')

                # Cần lấy thông tin user để hiển thị tên
                user_info = await database.get_user_by_id(user_id)
                user_first_name = user_info['first_name'] if user_info else f"User ID {user_id}"

                admin_text = (
                    f"Yêu cầu Thưởng Chia Sẻ \\(Mốc {milestone}\\) \\- {escape_markdown(user_first_name, version=2)}\n"
                    f"ID Game: `{escape_markdown(game_username, version=2)}`\n"
                    f"🎁 Điểm thưởng: `{reward_points}`"
                )
                admin_keyboard = keyboards.create_admin_share_reward_buttons(claim_id, user_id, milestone)
            elif promo_code == 'KL001':
                # THÊM LOGIC CHO CÁC LOẠI KHÁC
                user_info = await database.get_user_by_id(user_id)
                user_first_name = user_info['first_name'] if user_info else f"User ID {user_id}"
                admin_text = f"Yêu cầu KL001 - {user_first_name}\nID Game: `{game_username}`"
                admin_keyboard = keyboards.create_admin_promo_buttons(claim_id, user_id, promo_code)
            # ... (THÊM CÁC `elif promo_code == ...` KHÁC Ở ĐÂY) ...
            else:
                # Trường hợp không xác định được promo_code
                logger.warning(f"Resend: Không có logic xử lý cho promo_code '{promo_code}' của claim #{claim_id_for_log}.")
                fail_count += 1
                continue

            # Gửi tin nhắn
            if admin_text:
                await context.bot.send_message(
                    chat_id=target_admin_group,
                    text=admin_text,
                    reply_markup=admin_keyboard,
                    parse_mode=ParseMode.MARKDOWN_V2
                )
                success_count += 1
            else:
                # Ghi log rõ lý do tại sao text rỗng
                logger.warning(f"Resend: admin_text rỗng cho claim #{claim_id_for_log}, không gửi.")
                fail_count += 1

            # Thêm một khoảng nghỉ nhỏ để tránh bị rate limit
            await asyncio.sleep(0.5)

        except Exception as e:
            fail_count += 1
            logger.error(f"Lỗi khi gửi lại claim #{claim.get('claim_id')}: {e}")

    # 4. BÁO CÁO KẾT QUẢ
    final_report = (
        f"✅ Hoàn tất!\n\n"
        f"- Gửi lại thành công: {success_count}\n"
        f"- Gửi lại thất bại: {fail_count}"
    )
    await admin_message.edit_text(final_report)


# --- Conversation Handler cho Admin ---

admin_reply_conv_handler = ConversationHandler(
    entry_points=[
        # Entry points cho luồng Nạp Tiền
        CallbackQueryHandler(ask_for_gateway, pattern='^admin_deposit:.*:lam_lai_lenh$'),
        CallbackQueryHandler(ask_for_time, pattern='^admin_deposit:.*:da_len_diem$'),

        # Entry point cho luồng Rút Tiền
        CallbackQueryHandler(ask_for_withdraw_receipt, pattern='^admin_withdraw:.*:gui_hd$'),
    ],
    states={
        # State chờ admin nhập tên cổng (Nạp)
        AWAIT_GATEWAY: [MessageHandler(
            filters.REPLY & filter_gateway_reply & filters.TEXT & ~filters.COMMAND,
            receive_gateway_and_notify
        )],

        # State chờ admin nhập thời gian (Nạp)
        AWAIT_PROCESS_TIME: [MessageHandler(
            filters.REPLY & filter_time_reply & filters.TEXT & ~filters.COMMAND,
            receive_time_and_notify
        )],

        # State chờ admin gửi ảnh hóa đơn (Rút)
        AWAIT_WITHDRAW_RECEIPT: [MessageHandler(
            filters.REPLY & filter_withdraw_receipt_reply & filters.PHOTO,
            receive_withdraw_receipt_and_send
        )],
    },
    fallbacks=get_fallbacks(),
    allow_reentry=True,
    name="admin_reply_conversation" # Đổi tên cho nhất quán
)