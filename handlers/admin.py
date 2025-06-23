import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown
import database, config
from texts import RESPONSE_MESSAGES # Đảm bảo file texts.py có các khóa cần thiết
import re # Cần thiết cho KL007 point reply

logger = logging.getLogger(__name__)

# Hàm hỗ trợ để escape markdown trong trường hợp extra_info là None
def _escape_if_not_none(text):
    return escape_markdown(str(text), version=2) if text is not None else "N/A"

# Hàm xử lý phản hồi từ admin (Duyệt/Từ chối) cho Nạp/Rút/Khuyến mãi chung (KL001, KL007, App Promo)
async def handle_admin_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # Phân tích dữ liệu callback_data: admin_response:{user_id}:{request_type}:{action}:{extra_info}
    parts = query.data.split(':')
    # Đảm bảo có đủ phần, nếu không thì gán None cho extra_info
    if len(parts) >= 5:
        _, target_user_id_str, request_type, action, extra_info = parts
    else: # Trường hợp extra_info không có (ví dụ: callback_data chỉ có 4 phần)
        _, target_user_id_str, request_type, action = parts
        extra_info = None # Gán None nếu không có

    target_user_id = int(target_user_id_str)
    
    # Lấy thông tin người dùng từ database
    user_data = database.get_user_data(target_user_id)
    if not user_data:
        logger.warning(f"Không tìm thấy dữ liệu cho người dùng {target_user_id} khi xử lý admin response.")
        await query.message.reply_text("Không tìm thấy dữ liệu người dùng. Yêu cầu có thể đã hết hạn hoặc bị xóa.")
        return

    # Lấy message_id và chat_id của tin nhắn yêu cầu gốc trong nhóm admin
    # Đây là tin nhắn mà admin đã bấm vào, cần được chỉnh sửa
    admin_message_id = query.message.message_id
    admin_chat_id = query.message.chat_id

    # Lấy tin nhắn hiện tại của admin để cập nhật
    # Dùng .caption cho ảnh, .text cho tin nhắn text
    current_admin_content = query.message.caption if query.message.photo else query.message.text
    if not current_admin_content:
        current_admin_content = "Yêu cầu: " # Fallback nếu không có nội dung ban đầu

    # Loại bỏ các nút khỏi tin nhắn admin sau khi xử lý
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception as e:
        logger.warning(f"Không thể xóa nút khỏi tin nhắn admin {admin_message_id}: {e}")

    # Xây dựng tin nhắn phản hồi cho người dùng và cập nhật cho admin
    response_message_for_user = ""
    updated_admin_message_suffix = "" # Phần thêm vào tin nhắn admin

    # Xử lý các loại yêu cầu
    if request_type == 'deposit':
        amount = _escape_if_not_none(extra_info)
        if action == 'approve':
            response_message_for_user = RESPONSE_MESSAGES["deposit_approved"].format(amount=amount)
            updated_admin_message_suffix = f"\n\n*Trạng thái: ✅ Duyệt bởi Admin {escape_markdown(query.from_user.first_name, version=2)}*"
        else: # Từ chối
            reason_key = f"deposit_rejected_{action}"
            response_message_for_user = RESPONSE_MESSAGES.get(reason_key, RESPONSE_MESSAGES["deposit_rejected_generic"])
            updated_admin_message_suffix = f"\n\n*Trạng thái: ❌ Từ chối bởi Admin {escape_markdown(query.from_user.first_name, version=2)}* (Lý do: {RESPONSE_MESSAGES.get(reason_key, 'Lý do khác')})"

    elif request_type == 'withdrawal':
        amount = _escape_if_not_none(extra_info)
        if action == 'approve':
            response_message_for_user = RESPONSE_MESSAGES["withdrawal_approved"].format(amount=amount)
            updated_admin_message_suffix = f"\n\n*Trạng thái: ✅ Duyệt bởi Admin {escape_markdown(query.from_user.first_name, version=2)}*"
        else: # Từ chối
            reason_key = f"withdrawal_rejected_{action}"
            response_message_for_user = RESPONSE_MESSAGES.get(reason_key, RESPONSE_MESSAGES["withdrawal_rejected_generic"])
            updated_admin_message_suffix = f"\n\n*Trạng thái: ❌ Từ chối bởi Admin {escape_markdown(query.from_user.first_name, version=2)}* (Lý do: {RESPONSE_MESSAGES.get(reason_key, 'Lý do khác')})"

    elif request_type in ['KL001', 'KL007', 'app_promo']:
        game_username = _escape_if_not_none(extra_info)
        promo_code_display = _escape_if_not_none(request_type) # Để hiển thị trong tin nhắn

        if action == 'approve':
            response_message_for_user = RESPONSE_MESSAGES["promo_approved_message"].format(promo_code=promo_code_display)
            updated_admin_message_suffix = f"\n\n*Trạng thái: ✅ Duyệt bởi Admin {escape_markdown(query.from_user.first_name, version=2)}*"
            # Xóa trạng thái pending khỏi database nếu có (logic này hiện tại đã được handle bởi các hàm riêng)
            # Đối với KL001/KL007/App Promo, không nhất thiết phải có 'pending_share_milestones'.
            # Logic xóa pending thường nằm ở chỗ gọi hàm này.
            user_s_data = database.get_user_data(target_user_id)
            if 'pending_share_milestones' in user_s_data and str(promo_code_display) in user_s_data['pending_share_milestones']:
                pending_milestones = user_s_data['pending_share_milestones']
                del pending_milestones[str(promo_code_display)]
                database.update_user_data(target_user_id, {'pending_share_milestones': pending_milestones})

        else: # Từ chối
            reason_key = f"promo_rejected_{action}"
            # Lấy lý do cụ thể hoặc lý do chung, thay thế placeholder nếu có
            reason_message = RESPONSE_MESSAGES.get(reason_key, RESPONSE_MESSAGES["promo_rejected_generic"])
            if "{promo_code}" in reason_message:
                reason_message = reason_message.format(promo_code=promo_code_display)
            
            response_message_for_user = reason_message
            updated_admin_message_suffix = f"\n\n*Trạng thái: ❌ Từ chối bởi Admin {escape_markdown(query.from_user.first_name, version=2)}* (Lý do: {reason_message})"

            # Xóa trạng thái pending khỏi database nếu bị từ chối
            user_s_data = database.get_user_data(target_user_id)
            if 'pending_share_milestones' in user_s_data and str(promo_code_display) in user_s_data['pending_share_milestones']:
                pending_milestones = user_s_data['pending_share_milestones']
                del pending_milestones[str(promo_code_display)]
                database.update_user_data(target_user_id, {'pending_share_milestones': pending_milestones})

    # Cập nhật tin nhắn trong nhóm admin
    try:
        updated_text = current_admin_content + updated_admin_message_suffix
        if query.message.photo: # Nếu tin nhắn gốc có ảnh (ví dụ: yêu cầu nạp tiền hoặc app promo)
            await context.bot.edit_message_caption(
                chat_id=admin_chat_id,
                message_id=admin_message_id,
                caption=updated_text,
                parse_mode=ParseMode.MARKDOWN_V2
            )
        else: # Nếu tin nhắn gốc chỉ có text
            await context.bot.edit_message_text(
                chat_id=admin_chat_id,
                message_id=admin_message_id,
                text=updated_text,
                parse_mode=ParseMode.MARKDOWN_V2
            )
    except Exception as e:
        logger.error(f"Không thể chỉnh sửa tin nhắn admin {admin_message_id} trong chat {admin_chat_id}: {e}")

    # Gửi tin nhắn phản hồi cho người dùng
    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text=response_message_for_user,
            parse_mode=ParseMode.MARKDOWN_V2
        )
    except Exception as e:
        logger.error(f"Không thể gửi tin nhắn phản hồi cho người dùng {target_user_id}: {e}. Có thể người dùng đã chặn bot.")


# Hàm xử lý phản hồi từ admin cho KL006 (thưởng nhóm, có xử lý riêng)
async def handle_admin_kl006_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # admin_kl006:{user.id}:approve:{group_size}:{','.join(game_usernames)}
    parts = query.data.split(':')
    if len(parts) < 5:
        logger.error(f"Dữ liệu callback admin_kl006 không hợp lệ: {query.data}")
        await query.message.reply_text("Lỗi dữ liệu yêu cầu KL006.")
        return

    _, target_user_id_str, action, group_size_str, game_usernames_str = parts

    target_user_id = int(target_user_id_str)
    group_size = int(group_size_str)
    game_usernames = game_usernames_str.split(',') # danh sách tên game

    user_data = database.get_user_data(target_user_id)
    if not user_data:
        logger.warning(f"Không tìm thấy dữ liệu cho người dùng {target_user_id} khi xử lý KL006 response.")
        await query.message.reply_text("Không tìm thấy dữ liệu người dùng. Yêu cầu có thể đã hết hạn hoặc bị xóa.")
        return

    admin_message_id = query.message.message_id
    admin_chat_id = query.message.chat_id
    current_admin_text = query.message.text if query.message.text else "Yêu cầu KL006:" # KL006 là tin nhắn text

    # Loại bỏ các nút
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception as e:
        logger.warning(f"Không thể xóa nút khỏi tin nhắn admin KL006 {admin_message_id}: {e}")

    response_message_for_user = ""
    updated_admin_message_suffix = ""

    # Cập nhật trạng thái pending và claimed trong database
    user_s_data = database.get_user_data(target_user_id)
    pending_milestones = user_s_data.get("pending_share_milestones", {})
    claimed_milestones = user_s_data.get("claimed_share_milestones", {})


    if action == 'approve':
        response_message_for_user = RESPONSE_MESSAGES["kl006_approved_message"].format(group_size=group_size)
        updated_admin_message_suffix = f"\n\n*Trạng thái: ✅ Duyệt bởi Admin {escape_markdown(query.from_user.first_name, version=2)}*"
        
        # Di chuyển từ pending sang claimed
        if f"KL006_{group_size}" in pending_milestones: # Sử dụng định dạng KL006_{group_size} để xác định mốc
            del pending_milestones[f"KL006_{group_size}"]
        claimed_milestones[f"KL006_{group_size}"] = True # Đánh dấu là đã nhận
        database.update_user_data(target_user_id, {
            'pending_share_milestones': pending_milestones,
            'claimed_share_milestones': claimed_milestones
        })
        # Thêm logic tăng share_count nếu KL006 cũng là một loại share
        # current_share_count = user_s_data.get("share_count", 0)
        # database.update_user_data(target_user_id, {"share_count": current_share_count + group_size})
        
    else: # Từ chối
        reason_key = f"kl006_rejected_{action}"
        reason_message = RESPONSE_MESSAGES.get(reason_key, RESPONSE_MESSAGES["kl006_rejected_generic"])
        if "{group_size}" in reason_message:
            reason_message = reason_message.format(group_size=group_size)

        response_message_for_user = reason_message
        updated_admin_message_suffix = f"\n\n*Trạng thái: ❌ Từ chối bởi Admin {escape_markdown(query.from_user.first_name, version=2)}* (Lý do: {reason_message})"
        
        # Xóa khỏi pending nếu bị từ chối
        if f"KL006_{group_size}" in pending_milestones:
            del pending_milestones[f"KL006_{group_size}"]
            database.update_user_data(target_user_id, {'pending_share_milestones': pending_milestones})


    # Cập nhật tin nhắn trong nhóm admin
    try:
        updated_text = current_admin_text + updated_admin_message_suffix
        await context.bot.edit_message_text(
            chat_id=admin_chat_id,
            message_id=admin_message_id,
            text=updated_text,
            parse_mode=ParseMode.MARKDOWN_V2
        )
    except Exception as e:
        logger.error(f"Không thể chỉnh sửa tin nhắn admin KL006 {admin_message_id} trong chat {admin_chat_id}: {e}")

    # Gửi tin nhắn phản hồi cho người dùng
    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text=response_message_for_user,
            parse_mode=ParseMode.MARKDOWN_V2
        )
    except Exception as e:
        logger.error(f"Không thể gửi tin nhắn phản hồi KL006 cho người dùng {target_user_id}: {e}.")


# Hàm xử lý phản hồi từ admin cho yêu cầu Chia sẻ (Share Reward)
async def handle_admin_share_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # admin_share_resp:{user_id}:approve:{milestone}:{game_username}
    parts = query.data.split(':')
    if len(parts) < 5:
        logger.error(f"Dữ liệu callback admin_share_resp không hợp lệ: {query.data}")
        await query.message.reply_text("Lỗi dữ liệu yêu cầu thưởng chia sẻ.")
        return

    _, target_user_id_str, action, milestone_str, game_username = parts

    target_user_id = int(target_user_id_str)
    milestone = int(milestone_str)

    user_data = database.get_user_data(target_user_id)
    if not user_data:
        logger.warning(f"Không tìm thấy dữ liệu cho người dùng {target_user_id} khi xử lý Share response.")
        await query.message.reply_text("Không tìm thấy dữ liệu người dùng. Yêu cầu có thể đã hết hạn hoặc bị xóa.")
        return

    admin_message_id = query.message.message_id
    admin_chat_id = query.message.chat_id
    current_admin_text = query.message.text if query.message.text else "Yêu cầu thưởng chia sẻ:"

    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception as e:
        logger.warning(f"Không thể xóa nút khỏi tin nhắn admin Share {admin_message_id}: {e}")

    response_message_for_user = ""
    updated_admin_message_suffix = ""
    
    # Cập nhật trạng thái pending và claimed trong database
    user_s_data = database.get_user_data(target_user_id)
    pending_milestones = user_s_data.get("pending_share_milestones", {})
    claimed_milestones = user_s_data.get("claimed_share_milestones", {})

    if action == 'approve':
        response_message_for_user = RESPONSE_MESSAGES["share_reward_approved"].format(milestone=milestone)
        updated_admin_message_suffix = f"\n\n*Trạng thái: ✅ Duyệt bởi Admin {escape_markdown(query.from_user.first_name, version=2)}*"
        
        # Di chuyển từ pending sang claimed
        if str(milestone) in pending_milestones:
            del pending_milestones[str(milestone)]
        claimed_milestones[str(milestone)] = True
        database.update_user_data(target_user_id, {
            'pending_share_milestones': pending_milestones,
            'claimed_share_milestones': claimed_milestones
        })

    elif action == 'contact_cskh': # Admin bấm CSKH
        response_message_for_user = RESPONSE_MESSAGES["share_reward_contact_cskh"].format(milestone=milestone)
        updated_admin_message_suffix = f"\n\n*Trạng thái: ℹ️ Chuyển CSKH bởi Admin {escape_markdown(query.from_user.first_name, version=2)}*"
        # Vẫn giữ pending để user liên hệ CSKH và xử lý sau (hoặc có thể xóa pending nếu CSKH sẽ tạo yêu cầu mới)
        # Tùy thuộc vào quy trình của bạn. Hiện tại, tôi sẽ không xóa pending ở đây.
        
    else: # Các lý do từ chối khác (sai ID, v.v.)
        reason_key = f"share_reward_rejected_{action}"
        reason_message = RESPONSE_MESSAGES.get(reason_key, RESPONSE_MESSAGES["share_reward_rejected_generic"])
        if "{milestone}" in reason_message:
            reason_message = reason_message.format(milestone=milestone)

        response_message_for_user = reason_message
        updated_admin_message_suffix = f"\n\n*Trạng thái: ❌ Từ chối bởi Admin {escape_markdown(query.from_user.first_name, version=2)}* (Lý do: {reason_message})"

        # Xóa khỏi pending nếu bị từ chối
        if str(milestone) in pending_milestones:
            del pending_milestones[str(milestone)]
            database.update_user_data(target_user_id, {'pending_share_milestones': pending_milestones})

    # Cập nhật tin nhắn trong nhóm admin
    try:
        updated_text = current_admin_text + updated_admin_message_suffix
        await context.bot.edit_message_text(
            chat_id=admin_chat_id,
            message_id=admin_message_id,
            text=updated_text,
            parse_mode=ParseMode.MARKDOWN_V2
        )
    except Exception as e:
        logger.error(f"Không thể chỉnh sửa tin nhắn admin Share {admin_message_id} trong chat {admin_chat_id}: {e}")

    # Gửi tin nhắn phản hồi cho người dùng
    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text=response_message_for_user,
            parse_mode=ParseMode.MARKDOWN_V2
        )
    except Exception as e:
        logger.error(f"Không thể gửi tin nhắn phản hồi Share cho người dùng {target_user_id}: {e}.")


# Hàm xử lý việc admin reply tin nhắn yêu cầu KL007 để nhập điểm
# Lưu ý: Hàm này xử lý MessageHandler (reply), không phải CallbackQueryHandler
async def handle_admin_kl007_point_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.reply_to_message:
        await update.message.reply_text("Vui lòng trả lời tin nhắn yêu cầu KL007 bằng số điểm bạn muốn cộng.")
        return # Không phải tin nhắn trả lời hoặc không có tin nhắn

    original_message = update.message.reply_to_message
    admin_response_text = update.message.text.strip() # Nội dung admin trả lời

    # Kiểm tra xem tin nhắn gốc có phải là tin nhắn yêu cầu KL007 của bot không
    # Đây là điểm mấu chốt để xác định đúng tin nhắn cần xử lý
    is_kl007_request_message = False
    if original_message.from_user.is_bot:
        if original_message.caption and "YÊU CẦU KHUYẾN MÃI KL007 MỚI" in original_message.caption:
            is_kl007_request_message = True
        elif original_message.text and "YÊU CẦU KHUYẾN MÃI KL007 MỚI" in original_message.text:
            is_kl007_request_message = True
        
        # Thêm kiểm tra callback_data nếu tin nhắn gốc là từ một callback
        # (Tin nhắn yêu cầu thường không có callback_data trực tiếp, nhưng để an toàn)
        if original_message.reply_markup and original_message.reply_markup.inline_keyboard:
            for row in original_message.reply_markup.inline_keyboard:
                for button in row:
                    if button.callback_data and "promo_start:KL007" in button.callback_data: # Hoặc mẫu tương tự
                         is_kl007_request_message = True
                         break
                if is_kl007_request_message:
                    break

    if not is_kl007_request_message:
        await update.message.reply_text("Đây không phải là tin nhắn yêu cầu KL007 hợp lệ để phản hồi điểm.")
        return

    # Cố gắng trích xuất target_user_id và game_username từ tin nhắn gốc
    target_user_id = None
    game_username = "N/A" # Default value

    # Regex để tìm ID người dùng
    user_id_match = re.search(r'\((\d+)\)', original_message.caption or original_message.text)
    if user_id_match:
        target_user_id = int(user_id_match.group(1))

    # Regex để tìm tên game
    game_username_match = re.search(r'Tên game: `(.*?)`', original_message.caption or original_message.text)
    if game_username_match:
        game_username = game_username_match.group(1)

    if not target_user_id:
        logger.error(f"Không thể xác định user_id từ tin nhắn gốc KL007: {original_message.caption or original_message.text}")
        await update.message.reply_text("Lỗi: Không thể xác định người dùng để gửi điểm.")
        return
    
    # Kiểm tra xem phản hồi của admin có phải là số không
    if not admin_response_text.isdigit():
        await update.message.reply_text("Số điểm không hợp lệ\\. Vui lòng chỉ nhập số nguyên dương\\.")
        return

    admin_name = escape_markdown(update.effective_user.first_name, version=2)
    
    # Thông báo cho người dùng
    response_message_to_user = RESPONSE_MESSAGES.get("kl007_point_response", "Bạn đã nhận được điểm hoàn trả: {point}").format(point=admin_response_text)
    escaped_response_message_to_user = escape_markdown(response_message_to_user, version=2)

    # Cập nhật tin nhắn gốc trong nhóm admin
    updated_admin_message_text = (original_message.caption or original_message.text) + \
                                f"\n\n*Phản hồi Admin {admin_name}:* Đã cộng `{reply_text_by_admin}` điểm\\. "

    try:
        if original_message.photo:
            await context.bot.edit_message_caption(
                chat_id=original_message.chat.id,
                message_id=original_message.message_id,
                caption=updated_admin_message_text,
                parse_mode=ParseMode.MARKDOWN_V2
            )
        else:
            await context.bot.edit_message_text(
                chat_id=original_message.chat.id,
                message_id=original_message.message_id,
                text=updated_admin_message_text,
                parse_mode=ParseMode.MARKDOWN_V2
            )
        
        # Xóa tin nhắn reply của admin để giữ nhóm gọn gàng
        await update.message.delete()

        # Cập nhật trạng thái pending cho KL007 trong database nếu có
        user_s_data = database.get_user_data(target_user_id)
        pending_milestones = user_s_data.get("pending_share_milestones", {})
        if "KL007" in pending_milestones: # Giả sử mốc KL007 được lưu là "KL007"
            del pending_milestones["KL007"]
            database.update_user_data(target_user_id, {'pending_share_milestones': pending_milestones})

    except Exception as e:
        logger.error(f"Lỗi khi chỉnh sửa tin nhắn gốc KL007 hoặc xóa tin nhắn của admin: {e}")
        await update.message.reply_text("Đã xảy ra lỗi khi cập nhật trạng thái trong nhóm admin.")

    # Gửi tin nhắn phản hồi cho người dùng
    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text=escaped_response_message_to_user,
            parse_mode=ParseMode.MARKDOWN_V2
        )
    except Exception as e:
        logger.error(f"Lỗi khi gửi điểm KL007 cho user {target_user_id}: {e}.")
        # Fallback to plain text if markdown fails
        try:
            await context.bot.send_message(chat_id=target_user_id, text=response_message_to_user)
        except Exception as e_plain:
            logger.error(f"Lỗi khi gửi điểm KL007 (dự phòng văn bản thuần túy) đến user {target_user_id}: {e_plain}")