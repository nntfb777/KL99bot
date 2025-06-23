# Tệp: handlers/promotions.py
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, CallbackQueryHandler, filters, CommandHandler # Thêm CommandHandler
from telegram.constants import ParseMode
from telegram.helpers import escape_markdown
from texts import RESPONSE_MESSAGES, PROMO_TEXT_KL001, PROMO_TEXT_KL006, PROMO_TEXT_KL007, PROMO_TEXT_APP_PROMO
import database, config
from .core import back_to_menu_handler, _remove_buttons, cancel # Import cancel từ core
import time # Để tạo timestamp
import uuid # Để tạo request_id duy nhất

logger = logging.getLogger(__name__)

# Định nghĩa các trạng thái cho ConversationHandler
(AWAIT_AGREEMENT, AWAIT_USERNAME_KL001, AWAIT_GROUP_SIZE_KL006, AWAIT_USERNAMES_KL006, AWAIT_USERNAME_KL007, AWAIT_USERNAME_APP_PROMO, AWAIT_IMAGE_APP_PROMO) = range(7)


async def khuyen_mai_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.message: await _remove_buttons(query)

    keyboard = [
        [InlineKeyboardButton(RESPONSE_MESSAGES["promo_kl001_button"], callback_data='promo_start:KL001')],
        [InlineKeyboardButton(RESPONSE_MESSAGES["promo_kl006_button"], callback_data='promo_start:KL006')],
        [InlineKeyboardButton(RESPONSE_MESSAGES["promo_kl007_button"], callback_data='promo_start:KL007')],
        [InlineKeyboardButton(RESPONSE_MESSAGES["promo_app_promo_button"], callback_data='promo_start:APP_PROMO')],
        [InlineKeyboardButton(RESPONSE_MESSAGES["back_to_menu_button"], callback_data='back_to_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=RESPONSE_MESSAGES["main_promo_menu_intro"], # Đảm bảo key này có trong texts.py
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN_V2
    )
    # Kết thúc ConversationHandler hiện tại và chuyển sang handler khác nếu khuyen_mai_callback là entry_point của một ConversationHandler khác
    # Hoặc nếu nó chỉ là một callback độc lập, thì ConversationHandler.END là phù hợp.
    return ConversationHandler.END 

async def promo_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.message: await _remove_buttons(query)

    # Lấy promo_code từ callback_data (ví dụ: 'promo_start:KL001')
    promo_code = query.data.split(':')[1]
    context.user_data['current_promo'] = promo_code # Lưu vào user_data để dùng trong các bước tiếp theo

    promo_text = ""
    agreement_callback_data = ""
    promo_info_message_key = ""

    if promo_code == "KL001":
        promo_text = PROMO_TEXT_KL001
        agreement_callback_data = 'agree_promo:KL001'
        promo_info_message_key = "kl001_promo_info"
    elif promo_code == "KL006":
        promo_text = PROMO_TEXT_KL006
        agreement_callback_data = 'agree_promo:KL006'
        promo_info_message_key = "kl006_promo_info"
    elif promo_code == "KL007":
        promo_text = PROMO_TEXT_KL007
        agreement_callback_data = 'agree_promo:KL007'
        promo_info_message_key = "kl007_promo_info"
    elif promo_code == "APP_PROMO":
        promo_text = PROMO_TEXT_APP_PROMO
        agreement_callback_data = 'agree_promo:APP_PROMO'
        promo_info_message_key = "app_promo_info"
    else:
        await query.message.reply_text(RESPONSE_MESSAGES["error_invalid_promo"])
        return ConversationHandler.END # Hoặc quay về menu chính

    keyboard = [
        [InlineKeyboardButton(RESPONSE_MESSAGES["agree_button"], callback_data=agreement_callback_data)],
        [InlineKeyboardButton(RESPONSE_MESSAGES["back_to_promo_menu_button"], callback_data='back_to_promo_menu')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Sử dụng promo_info_message_key để lấy tin nhắn giới thiệu khuyến mãi từ RESPONSE_MESSAGES
    intro_message = RESPONSE_MESSAGES.get(promo_info_message_key, "Thông tin khuyến mãi:").format(
        promo_info=promo_text
    )

    await query.message.reply_text(
        intro_message,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN_V2
    )
    return AWAIT_AGREEMENT

async def agree_promo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.message: await _remove_buttons(query)

    promo_code = query.data.split(':')[1]
    user_id = update.effective_user.id

    # Lấy dữ liệu người dùng để kiểm tra trạng thái pending/đã nhận
    user_data = database.get_user_data(user_id)

    if promo_code == "KL001":
        if user_data.get("kl001_claimed"): # Kiểm tra đã nhận chưa
            await query.message.reply_text(RESPONSE_MESSAGES["kl001_already_claimed"], parse_mode=ParseMode.MARKDOWN_V2)
            return ConversationHandler.END 
        if user_data.get("kl001_pending_request"): # Kiểm tra đang pending chưa
            await query.message.reply_text(RESPONSE_MESSAGES["kl001_pending_exists"], parse_mode=ParseMode.MARKDOWN_V2)
            return ConversationHandler.END
        
        await query.message.reply_text(RESPONSE_MESSAGES["kl001_ask_username"], parse_mode=ParseMode.MARKDOWN_V2)
        return AWAIT_USERNAME_KL001
    
    elif promo_code == "KL006":
        if user_data.get("kl006_claimed"):
            await query.message.reply_text(RESPONSE_MESSAGES["kl006_already_claimed"], parse_mode=ParseMode.MARKDOWN_V2)
            return ConversationHandler.END
        if user_data.get("kl006_pending_request"):
            await query.message.reply_text(RESPONSE_MESSAGES["kl006_pending_exists"], parse_mode=ParseMode.MARKDOWN_V2)
            return ConversationHandler.END

        await query.message.reply_text(RESPONSE_MESSAGES["kl006_ask_group_size"], parse_mode=ParseMode.MARKDOWN_V2)
        return AWAIT_GROUP_SIZE_KL006

    elif promo_code == "KL007":
        if user_data.get("kl007_claimed"):
            await query.message.reply_text(RESPONSE_MESSAGES["kl007_already_claimed"], parse_mode=ParseMode.MARKDOWN_V2)
            return ConversationHandler.END
        if user_data.get("kl007_pending_request"):
            await query.message.reply_text(RESPONSE_MESSAGES["kl007_pending_exists"], parse_mode=ParseMode.MARKDOWN_V2)
            return ConversationHandler.END

        await query.message.reply_text(RESPONSE_MESSAGES["kl007_ask_username"], parse_mode=ParseMode.MARKDOWN_V2)
        return AWAIT_USERNAME_KL007

    elif promo_code == "APP_PROMO":
        if user_data.get("app_promo_claimed"):
            await query.message.reply_text(RESPONSE_MESSAGES["app_promo_already_claimed"], parse_mode=ParseMode.MARKDOWN_V2)
            return ConversationHandler.END
        if user_data.get("app_promo_pending_request"):
            await query.message.reply_text(RESPONSE_MESSAGES["app_promo_pending_exists"], parse_mode=ParseMode.MARKDOWN_V2)
            return ConversationHandler.END

        await query.message.reply_text(RESPONSE_MESSAGES["app_promo_ask_username"], parse_mode=ParseMode.MARKDOWN_V2)
        return AWAIT_USERNAME_APP_PROMO

    else:
        await query.message.reply_text(RESPONSE_MESSAGES["error_generic"], parse_mode=ParseMode.MARKDOWN_V2)
        return ConversationHandler.END


async def process_kl001_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    game_username = escape_markdown(update.message.text.strip(), version=2)

    # Đã kiểm tra pending ở agree_promo_callback, nhưng kiểm tra lại ở đây là tốt
    # Đảm bảo logic kiểm tra và cập nhật trạng thái pending đồng bộ giữa database và user_data.
    # user_data (từ database) phản ánh trạng thái chính xác nhất.
    user_data = database.get_user_data(user_id)
    if user_data.get("kl001_pending_request") or user_data.get("kl001_claimed"):
        # Trường hợp này hiếm xảy ra nếu logic agree_promo_callback đúng, nhưng là một lớp bảo vệ.
        await update.message.reply_text(RESPONSE_MESSAGES["kl001_pending_exists"], parse_mode=ParseMode.MARKDOWN_V2)
        return ConversationHandler.END

    # Tạo một request_id duy nhất cho yêu cầu này
    request_id = str(uuid.uuid4())

    try:
        # Ghi yêu cầu ban đầu vào database
        database.create_promotion_request(
            request_id=request_id,
            promo_code="KL001",
            user_id=user_id,
            username=game_username,
            status="pending",
            timestamp=int(time.time()),
            # Thêm trường để lưu admin_message_id và admin_chat_id, ban đầu là None
            admin_message_id=None,
            admin_chat_id=None
        )
        logger.info(f"Đã tạo yêu cầu KL001 {request_id} của user {user_id} trong DB.")

        # Gửi yêu cầu đến nhóm admin
        admin_message = (
            f"*YÊU CẦU KHUYẾN MÃI MỚI - KL001*\n"
            f"👤 Khách: [{escape_markdown(update.effective_user.first_name, version=2)}](tg://user?id={user_id}) (`{user_id}`)\n"
            f"Tên game: `{game_username}`\n"
            f"⏳ Trạng thái: Đang chờ xử lý\n"
            f"ID yêu cầu: `{request_id}`"
        )

        keyboard = [
            [
                InlineKeyboardButton("✅ Duyệt", callback_data=f"admin_promo_resp:{request_id}:KL001:approve"),
                InlineKeyboardButton("❌ Từ chối", callback_data=f"admin_promo_resp:{request_id}:KL001:reject"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        sent_message = await context.bot.send_message(
            chat_id=config.ID_GROUP_PROMO,
            text=admin_message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN_V2
        )
        logger.info(f"Yêu cầu KL001 của user {user_id} đã được gửi tới admin: {sent_message.message_id}")

        # Cập nhật message_id và chat_id của tin nhắn admin vào database
        database.update_promotion_request(
            request_id=request_id,
            update_data={
                "admin_message_id": sent_message.message_id,
                "admin_chat_id": sent_message.chat_id
            }
        )
        logger.info(f"Đã cập nhật message_id admin ({sent_message.message_id}) cho yêu cầu KL001 {request_id}.")

        # Đặt cờ pending trong user_data của database
        # Điều này giúp ngăn người dùng gửi nhiều yêu cầu liên tiếp cho cùng một khuyến mãi.
        database.update_user_data(user_id, {"kl001_pending_request": True})

        await update.message.reply_text(RESPONSE_MESSAGES["kl001_request_sent"], parse_mode=ParseMode.MARKDOWN_V2)

    except Exception as e:
        logger.error(f"Lỗi khi gửi yêu cầu khuyến mãi KL001 tới nhóm admin cho user {user_id}: {e}", exc_info=True)
        await update.message.reply_text(RESPONSE_MESSAGES["error_sending_request"], parse_mode=ParseMode.MARKDOWN_V2)

    return ConversationHandler.END


# KL006 handlers
async def process_kl006_group_size(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        group_size = int(update.message.text.strip())
        if group_size <= 0:
            raise ValueError
        context.user_data['kl006_group_size'] = group_size
        await update.message.reply_text(RESPONSE_MESSAGES["kl006_ask_usernames"], parse_mode=ParseMode.MARKDOWN_V2)
        return AWAIT_USERNAMES_KL006
    except ValueError:
        await update.message.reply_text(RESPONSE_MESSAGES["kl006_invalid_group_size"], parse_mode=ParseMode.MARKDOWN_V2)
        return AWAIT_GROUP_SIZE_KL006

async def process_kl006_usernames(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    usernames_input = update.message.text.strip()
    group_size = context.user_data.get('kl006_group_size')

    if not group_size: # Đảm bảo group_size vẫn còn trong context.user_data
        await update.message.reply_text(RESPONSE_MESSAGES["error_generic"], parse_mode=ParseMode.MARKDOWN_V2)
        return ConversationHandler.END

    usernames_list = [escape_markdown(u.strip(), version=2) for u in usernames_input.split('\n') if u.strip()]

    if len(usernames_list) != group_size:
        await update.message.reply_text(RESPONSE_MESSAGES["kl006_username_count_mismatch"].format(expected=group_size, actual=len(usernames_list)), parse_mode=ParseMode.MARKDOWN_V2)
        return AWAIT_USERNAMES_KL006

    # Tạo một request_id duy nhất
    request_id = str(uuid.uuid4())

    try:
        # Ghi yêu cầu KL006 vào database
        database.create_promotion_request(
            request_id=request_id,
            promo_code="KL006",
            user_id=user_id,
            group_size=group_size,
            usernames=usernames_list,
            status="pending",
            timestamp=int(time.time()),
            admin_message_id=None,
            admin_chat_id=None
        )
        logger.info(f"Đã tạo yêu cầu KL006 {request_id} của user {user_id} trong DB.")

        # Gửi yêu cầu đến nhóm admin
        admin_message = (
            f"*YÊU CẦU KHUYẾN MÃI MỚI - KL006*\n"
            f"👤 Khách: [{escape_markdown(update.effective_user.first_name, version=2)}](tg://user?id={user_id}) (`{user_id}`)\n"
            f"Số lượng thành viên: `{group_size}`\n"
            f"Tên game thành viên:\n`{', '.join(usernames_list)}`\n"
            f"⏳ Trạng thái: Đang chờ xử lý\n"
            f"ID yêu cầu: `{request_id}`"
        )

        keyboard = [
            [
                InlineKeyboardButton("✅ Duyệt", callback_data=f"admin_promo_resp:{request_id}:KL006:approve"),
                InlineKeyboardButton("❌ Từ chối", callback_data=f"admin_promo_resp:{request_id}:KL006:reject"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        sent_message = await context.bot.send_message(
            chat_id=config.ID_GROUP_PROMO,
            text=admin_message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN_V2
        )
        logger.info(f"Yêu cầu KL006 của user {user_id} đã được gửi tới admin: {sent_message.message_id}")

        # Cập nhật message_id và chat_id của tin nhắn admin vào database
        database.update_promotion_request(
            request_id=request_id,
            update_data={
                "admin_message_id": sent_message.message_id,
                "admin_chat_id": sent_message.chat_id
            }
        )
        logger.info(f"Đã cập nhật message_id admin ({sent_message.message_id}) cho yêu cầu KL006 {request_id}.")

        database.update_user_data(user_id, {"kl006_pending_request": True})

        await update.message.reply_text(RESPONSE_MESSAGES["kl006_request_sent"], parse_mode=ParseMode.MARKDOWN_V2)

    except Exception as e:
        logger.error(f"Lỗi khi gửi yêu cầu khuyến mãi KL006 tới nhóm admin cho user {user_id}: {e}", exc_info=True)
        await update.message.reply_text(RESPONSE_MESSAGES["error_sending_request"], parse_mode=ParseMode.MARKDOWN_V2)

    # Xóa dữ liệu tạm thời trong context.user_data sau khi hoàn tất yêu cầu
    context.user_data.pop('kl006_group_size', None)

    return ConversationHandler.END


# KL007 handler
async def process_kl007_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    game_username = escape_markdown(update.message.text.strip(), version=2)

    user_data = database.get_user_data(user_id)
    if user_data.get("kl007_pending_request") or user_data.get("kl007_claimed"):
        await update.message.reply_text(RESPONSE_MESSAGES["kl007_pending_exists"], parse_mode=ParseMode.MARKDOWN_V2)
        return ConversationHandler.END

    # Tạo một request_id duy nhất
    request_id = str(uuid.uuid4())

    try:
        # Ghi yêu cầu ban đầu vào database
        database.create_promotion_request(
            request_id=request_id,
            promo_code="KL007",
            user_id=user_id,
            username=game_username,
            status="pending",
            timestamp=int(time.time()),
            admin_message_id=None,
            admin_chat_id=None
        )
        logger.info(f"Đã tạo yêu cầu KL007 {request_id} của user {user_id} trong DB.")

        # Gửi yêu cầu đến nhóm admin
        admin_message = (
            f"*YÊU CẦU KHUYẾN MÃI MỚI - KL007*\n"
            f"👤 Khách: [{escape_markdown(update.effective_user.first_name, version=2)}](tg://user?id={user_id}) (`{user_id}`)\n"
            f"Tên game: `{game_username}`\n"
            f"⏳ Trạng thái: Đang chờ xử lý\n"
            f"ID yêu cầu: `{request_id}`"
        )

        keyboard = [
            [
                InlineKeyboardButton("✅ Duyệt", callback_data=f"admin_promo_resp:{request_id}:KL007:approve"),
                InlineKeyboardButton("❌ Từ chối", callback_data=f"admin_promo_resp:{request_id}:KL007:reject"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        sent_message = await context.bot.send_message(
            chat_id=config.ID_GROUP_PROMO,
            text=admin_message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN_V2
        )
        logger.info(f"Yêu cầu KL007 của user {user_id} đã được gửi tới admin: {sent_message.message_id}")

        # Cập nhật message_id và chat_id của tin nhắn admin vào database
        database.update_promotion_request(
            request_id=request_id,
            update_data={
                "admin_message_id": sent_message.message_id,
                "admin_chat_id": sent_message.chat_id
            }
        )
        logger.info(f"Đã cập nhật message_id admin ({sent_message.message_id}) cho yêu cầu KL007 {request_id}.")

        database.update_user_data(user_id, {"kl007_pending_request": True})

        await update.message.reply_text(RESPONSE_MESSAGES["kl007_request_sent"], parse_mode=ParseMode.MARKDOWN_V2)

    except Exception as e:
        logger.error(f"Lỗi khi gửi yêu cầu khuyến mãi KL007 tới nhóm admin cho user {user_id}: {e}", exc_info=True)
        await update.message.reply_text(RESPONSE_MESSAGES["error_sending_request"], parse_mode=ParseMode.MARKDOWN_V2)

    return ConversationHandler.END


# APP_PROMO handlers
async def process_app_promo_username(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    game_username = escape_markdown(update.message.text.strip(), version=2)
    context.user_data['app_promo_username'] = game_username # Lưu tạm vào context.user_data

    user_data = database.get_user_data(user_id)
    if user_data.get("app_promo_pending_request") or user_data.get("app_promo_claimed"):
        await update.message.reply_text(RESPONSE_MESSAGES["app_promo_pending_exists"], parse_mode=ParseMode.MARKDOWN_V2)
        return ConversationHandler.END

    await update.message.reply_text(RESPONSE_MESSAGES["app_promo_ask_image"], parse_mode=ParseMode.MARKDOWN_V2)
    return AWAIT_IMAGE_APP_PROMO

async def process_app_promo_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    
    if not update.message.photo:
        await update.message.reply_text(RESPONSE_MESSAGES["no_image_provided"], parse_mode=ParseMode.MARKDOWN_V2)
        return AWAIT_IMAGE_APP_PROMO

    photo_file_id = update.message.photo[-1].file_id # Lấy ID của ảnh chất lượng cao nhất
    app_promo_username = context.user_data.get('app_promo_username', 'N/A')

    # Tạo một request_id duy nhất
    request_id = str(uuid.uuid4())

    try:
        # Ghi yêu cầu ban đầu vào database
        database.create_promotion_request(
            request_id=request_id,
            promo_code="APP_PROMO",
            user_id=user_id,
            username=app_promo_username,
            photo_file_id=photo_file_id,
            status="pending",
            timestamp=int(time.time()),
            admin_message_id=None,
            admin_chat_id=None
        )
        logger.info(f"Đã tạo yêu cầu APP_PROMO {request_id} của user {user_id} trong DB.")

        # Gửi yêu cầu đến nhóm admin
        admin_message = (
            f"*YÊU CẦU KHUYẾN MÃI MỚI - APP PROMO*\n"
            f"👤 Khách: [{escape_markdown(update.effective_user.first_name, version=2)}](tg://user?id={user_id}) (`{user_id}`)\n"
            f"Tên game: `{app_promo_username}`\n"
            f"⏳ Trạng thái: Đang chờ xử lý\n"
            f"ID yêu cầu: `{request_id}`"
        )

        keyboard = [
            [
                InlineKeyboardButton("✅ Duyệt", callback_data=f"admin_promo_resp:{request_id}:APP_PROMO:approve"),
                InlineKeyboardButton("❌ Từ chối", callback_data=f"admin_promo_resp:{request_id}:APP_PROMO:reject"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        sent_message = await context.bot.send_photo(
            chat_id=config.ID_GROUP_PROMO,
            photo=photo_file_id,
            caption=admin_message,
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN_V2
        )
        logger.info(f"Yêu cầu APP_PROMO của user {user_id} đã được gửi tới admin: {sent_message.message_id}")

        # Cập nhật message_id và chat_id của tin nhắn admin vào database
        database.update_promotion_request(
            request_id=request_id,
            update_data={
                "admin_message_id": sent_message.message_id,
                "admin_chat_id": sent_message.chat_id
            }
        )
        logger.info(f"Đã cập nhật message_id admin ({sent_message.message_id}) cho yêu cầu APP_PROMO {request_id}.")

        database.update_user_data(user_id, {"app_promo_pending_request": True})

        await update.message.reply_text(RESPONSE_MESSAGES["app_promo_request_sent"], parse_mode=ParseMode.MARKDOWN_V2)

    except Exception as e:
        logger.error(f"Lỗi khi gửi yêu cầu khuyến mãi APP_PROMO tới nhóm admin cho user {user_id}: {e}", exc_info=True)
        await update.message.reply_text(RESPONSE_MESSAGES["error_sending_request"], parse_mode=ParseMode.MARKDOWN_V2)

    # Xóa dữ liệu tạm thời trong context.user_data sau khi hoàn tất yêu cầu
    context.user_data.pop('app_promo_username', None)

    return ConversationHandler.END


# Fallback để quay lại menu khuyến mãi chính
async def back_to_promo_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    if query.message: await _remove_buttons(query) # Xóa các nút cũ

    # Xóa dữ liệu tạm thời từ context.user_data nếu có từ bất kỳ cuộc hội thoại nào
    # Điều này quan trọng để tránh dữ liệu cũ ảnh hưởng đến các cuộc hội thoại mới
    context.user_data.pop('current_promo', None)
    context.user_data.pop('kl006_group_size', None)
    context.user_data.pop('app_promo_username', None)

    # Quay lại menu khuyến mãi chính
    # Vì khuyen_mai_callback cũng là một CallbackQueryHandler, chúng ta cần tạo một update giả
    # Hoặc gọi trực tiếp khuyen_mai_callback nếu nó được thiết kế để hoạt động mà không cần query.
    # Cách tốt nhất là gọi trực tiếp hàm khuyen_mai_callback và truyền update/context hiện có.
    return await khuyen_mai_callback(update, context)


# --- Conversation Handlers ---
# Lưu ý: entry_points của ConversationHandler thường là một CallbackQueryHandler hoặc CommandHandler.
# Pattern 'promo_start:([A-Za-z0-9_]+)' sẽ bắt được KL001, KL006, KL007, APP_PROMO

kl001_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(promo_start_callback, pattern='^promo_start:KL001$')],
    states={
        AWAIT_AGREEMENT: [CallbackQueryHandler(agree_promo_callback, pattern='^agree_promo:KL001$')],
        AWAIT_USERNAME_KL001: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_kl001_username)],
    },
    fallbacks=[
        CallbackQueryHandler(back_to_menu_handler, pattern='^back_to_menu$'),
        CallbackQueryHandler(back_to_promo_menu_handler, pattern='^back_to_promo_menu$'),
        CommandHandler('cancel', cancel) # Thêm CommandHandler cho /cancel
    ]
)

kl006_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(promo_start_callback, pattern='^promo_start:KL006$')],
    states={
        AWAIT_AGREEMENT: [CallbackQueryHandler(agree_promo_callback, pattern='^agree_promo:KL006$')],
        AWAIT_GROUP_SIZE_KL006: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_kl006_group_size)],
        AWAIT_USERNAMES_KL006: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_kl006_usernames)],
    },
    fallbacks=[
        CallbackQueryHandler(back_to_menu_handler, pattern='^back_to_menu$'),
        CallbackQueryHandler(back_to_promo_menu_handler, pattern='^back_to_promo_menu$'),
        CommandHandler('cancel', cancel) # Thêm CommandHandler cho /cancel
    ]
)

kl007_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(promo_start_callback, pattern='^promo_start:KL007$')],
    states={
        AWAIT_AGREEMENT: [CallbackQueryHandler(agree_promo_callback, pattern='^agree_promo:KL007$')],
        AWAIT_USERNAME_KL007: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_kl007_username)],
    },
    fallbacks=[
        CallbackQueryHandler(back_to_menu_handler, pattern='^back_to_menu$'),
        CallbackQueryHandler(back_to_promo_menu_handler, pattern='^back_to_promo_menu$'),
        CommandHandler('cancel', cancel) # Thêm CommandHandler cho /cancel
    ]
)

app_promo_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(promo_start_callback, pattern='^promo_start:APP_PROMO$')],
    states={
        AWAIT_AGREEMENT: [CallbackQueryHandler(agree_promo_callback, pattern='^agree_promo:APP_PROMO$')],
        AWAIT_USERNAME_APP_PROMO: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_app_promo_username)],
        AWAIT_IMAGE_APP_PROMO: [MessageHandler(filters.PHOTO & ~filters.COMMAND, process_app_promo_image)],
    },
    fallbacks=[
        CallbackQueryHandler(back_to_menu_handler, pattern='^back_to_menu$'),
        CallbackQueryHandler(back_to_promo_menu_handler, pattern='^back_to_promo_menu$'),
        CommandHandler('cancel', cancel) # Thêm CommandHandler cho /cancel
    ]
)