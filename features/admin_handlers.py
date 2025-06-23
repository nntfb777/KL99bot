# features/admin_handlers.py

import logging
import json
import re
from telegram import Update
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown
from telegram.constants import ParseMode

from core import database
from utils import helpers, keyboards
from texts import RESPONSE_MESSAGES
import config

logger = logging.getLogger(__name__)

async def handle_admin_promo_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles simple promo responses from admins (approve/reject)."""
    query = update.callback_query
    await query.answer()

    try:
        # admin_response:{claim_id}:{user_id}:{promo_code}:{action}
        _prefix, claim_id_str, user_id_str, promo_code, action = query.data.split(':', 4)
        claim_id = int(claim_id_str)
        user_id = int(user_id_str)
    except (ValueError, IndexError) as e:
        logger.error(f"Error parsing admin callback data: {query.data} - {e}")
        await query.edit_message_text(f"Lỗi callback data: {query.data}")
        return

    claim = database.get_promo_claim(claim_id)
    if not claim:
        await query.edit_message_text(f"Lỗi: Yêu cầu ID {claim_id} không còn trong hàng đợi hoặc đã được xử lý.", reply_markup=None)
        return

    admin_user = query.from_user
    admin_mention = f"[{escape_markdown(admin_user.first_name, version=2)}](tg://user?id={admin_user.id})"

    # Generate response message for the customer
    customer_message_template = RESPONSE_MESSAGES.get(action)
    if customer_message_template:
        customer_message = customer_message_template.format(
            customer_username=escape_markdown(claim.get('game_username', ''), version=2),
            promo_code=promo_code
        )
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=customer_message,
                reply_markup=keyboards.create_customer_response_keyboard(promo_code)
            )
        except Exception as e:
            logger.error(f"Failed to send admin response for claim {claim_id} to user {user_id}: {e}")

    # Edit the admin message to show it's processed
    original_text = query.message.text_markdown_v2
    processed_text = (
        f"{original_text}\n———\n"
        f"✅ Xử lý bởi {admin_mention} lúc {get_current_time_str()}\\."
        f"Hành động: *{action.replace('_', ' ').title()}*\\."
    )
    await query.edit_message_text(text=processed_text, reply_markup=None, parse_mode=ParseMode.MARKDOWN_V2)

    # Delete the claim from the queue
    database.delete_promo_claim(claim_id)
    logger.info(f"Admin {admin_user.id} processed promo claim {claim_id} with action '{action}'. Claim deleted.")

async def handle_admin_share_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles share reward responses from admins."""
    query = update.callback_query
    await query.answer()

    try:
        # admin_share_resp:{claim_id}:{user_id}:{milestone}:{action}
        _prefix, claim_id_str, user_id_str, milestone_str, action = query.data.split(':', 4)
        claim_id = int(claim_id_str)
        user_id = int(user_id_str)
        milestone = int(milestone_str)
    except (ValueError, IndexError) as e:
        logger.error(f"Error parsing admin share callback data: {query.data} - {e}")
        await query.edit_message_text(f"Lỗi callback data: {query.data}")
        return

    claim = database.get_share_claim(claim_id)
    if not claim:
        await query.edit_message_text(f"Lỗi: Yêu cầu chia sẻ ID {claim_id} không còn trong hàng đợi.", reply_markup=None)
        return

    admin_user = query.from_user
    admin_mention = f"[{escape_markdown(admin_user.first_name, version=2)}](tg://user?id={admin_user.id})"

    customer_message_key = f"share_reward_{action}" # e.g., "share_reward_approved"
    customer_message_template = RESPONSE_MESSAGES.get(customer_message_key, "Phản hồi cho yêu cầu của bạn đã được xử lý.")

    customer_message = customer_message_template.format(
        milestone=milestone,
        game_username=escape_markdown(claim.get('game_username', ''), version=2)
    )

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=customer_message,
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=keyboards.create_back_to_main_menu_markup()
        )
    except Exception as e:
        logger.error(f"Failed to send share response for claim {claim_id} to user {user_id}: {e}")

    # Edit admin message
    original_text = query.message.text_markdown_v2
    processed_text = (
        f"{original_text}\n———\n"
        f"✅ Xử lý bởi {admin_mention} lúc {config.get_current_time_str()}\\. "
        f"Hành động: *{action.replace('_', ' ').title()}*\\."
    )
    await query.edit_message_text(text=processed_text, reply_markup=None, parse_mode=ParseMode.MARKDOWN_V2)

    # Process or delete the claim
    if action == 'approved':
        database.process_approved_share_claim(claim_id)
    else: # sai_id, cskh, etc.
        database.delete_share_claim(claim_id)

    logger.info(f"Admin {admin_user.id} processed share claim {claim_id} with action '{action}'.")


# You would also add handle_admin_kl006_response and handle_admin_kl007_point_reply here
# following the same pattern: parse data, notify user, edit admin message, update DB.
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
    claim = database.get_promo_claim(claim_id)
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
            # Điền tên thành viên bị ảnh hưởng vào tin nhắn nếu cần
            customer_message = message_template.format(username=affected_username)
        except KeyError:
            customer_message = message_template
    else:
        customer_message = "Yêu cầu của bạn đã được xử lý."
        logger.warning(f"Không tìm thấy message template cho key: {customer_message_key}")

    # Gửi tin nhắn phản hồi cho người dùng
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=customer_message,
            reply_markup=keyboards.create_customer_response_keyboard('KL006')
        )
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

    # Xóa yêu cầu khỏi hàng đợi
    database.delete_promo_claim(claim_id)
    logger.info(f"Admin {admin_user.id} đã xử lý claim KL006 {claim_id}. Yêu cầu đã bị xóa.")


async def handle_admin_kl007_point_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin reply số điểm cho KL007 khi reply trực tiếp vào tin nhắn prompt."""
    message = update.message
    replied = message.reply_to_message
    if not replied or replied.from_user.id != context.bot.id or message.chat_id != config.ID_GROUP_PROMO:
        return  # Không phải reply admin prompt

    # Parse số điểm trong message.text
    text = message.text.strip()
    m = re.match(r'^\+?(\d+)$', text)
    if not m:
        await message.reply_text("Vui lòng reply chỉ với số điểm (ví dụ: 100 hoặc +100).")
        return
    delta = int(m.group(1))

    # Lấy user_id từ reply_to_message.caption/text (callback_data trong prompt)
    # Giả sử prompt caption chứa user_id như "Reply for ... (ID: 12345)"
    id_match = re.search(r'UID:\s*(\d+)', replied.text or replied.caption or "")
    if not id_match:
        await message.reply_text("Không xác định được User ID từ tin nhắn gốc.")
        return
    target_user_id = int(id_match.group(1))

    # Cập nhật điểm trong DB
    database.update_kl007_points(target_user_id, delta)

    # Thông báo cho user
    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text=RESPONSE_MESSAGES["kl007_points_added"].format(points=delta),
            reply_markup=keyboards.create_customer_response_keyboard("KL007")
        )
    except Exception as e:
        logger.error(f"KL007: lỗi gửi tin nhắn cộng điểm cho {target_user_id}: {e}")

    # Edit tin nhắn admin prompt để remove markup & ghi nhận
    admin_mention = f"[{escape_markdown(message.from_user.first_name, version=2)}]" \
                    f"(tg://user?id={message.from_user.id})"
    processed = (
        f"{replied.text or replied.caption}\n———\n"
        f"✅ {admin_mention} đã cộng *{delta} điểm* cho User ID {target_user_id}."
    )
    await replied.edit_text(processed, parse_mode=ParseMode.MARKDOWN_V2)

    logger.info(f"Admin {message.from_user.id} cộng {delta} điểm cho user {target_user_id}")

async def handle_admin_kl007_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Admin callback cho KL007: prompt admin reply số điểm.
    Callback data: 'admin_kl007:prompt:<claim_id>:<user_id>'
    """
    query = update.callback_query
    await query.answer()

    parts = query.data.split(':')  # ['admin_kl007', 'prompt', claim_id, user_id]
    if len(parts) != 4:
        await query.edit_message_text("Dữ liệu callback KL007 không hợp lệ.", reply_markup=None)
        return

    _, _, claim_id, user_id = parts
    # Chuẩn bị prompt
    original = query.message.text or query.message.caption or ""
    prompt_text = (f"{original}\n\n"
                   f"💬 Admin vui lòng reply tin nhắn này với số điểm muốn cộng cho User ID: {user_id}")
    await query.edit_message_text(prompt_text)
    logger.info("Admin %s prompt cộng điểm KL007 cho user %s (claim %s)", query.from_user.id, user_id, claim_id)

