# features/game_link_handler.py

"""
Module này xử lý tất cả logic liên quan đến việc cung cấp, làm mới,
và báo cáo lỗi cho các link truy cập game.
"""
import logging
import random
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters
)
import config
from texts import RESPONSE_MESSAGES
from features.fallbacks import get_fallbacks
from utils import helpers, keyboards
from telegram.helpers import escape_markdown
import telegram

logger = logging.getLogger(__name__)

ASK_FOR_IMAGE, AWAITING_IMAGE, AWAITING_VPN_CONFIRMATION  = range(3)

def _escape_url_for_markdownv2(url: str) -> str:
    """Escape các ký tự đặc biệt trong URL cho MarkdownV2 một cách an toàn."""
    # Danh sách các ký tự cần escape trong MarkdownV2
    # Dấu ` và \ là các ký tự escape đặc biệt
    reserved_chars = r'_*[]()~`>#+-=|{}.!'
    # Thay thế ký tự \ trước, sau đó là `
    escaped_url = url.replace('\\', '\\\\').replace('`', '\\`')
    # Escape các ký tự còn lại
    for char in reserved_chars:
        if char not in ['\\', '`']:
            escaped_url = escaped_url.replace(char, f'\\{char}')
    return escaped_url

async def provide_game_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Xử lý callback 'request_game_link'.
    XÓA tin nhắn cũ (nếu có) và GỬI một tin nhắn mới với link ngẫu nhiên.
    """
    query = update.callback_query
    try:
        await query.answer()
    except telegram.error.BadRequest as e:
        if "Query is too old" in str(e):
            logger.info(f"Bỏ qua query đã cũ trong provide_game_link.")
            return # Dừng lại nếu là double-click
        else:
            raise e

    chat_id = update.effective_chat.id




    # 1. Chọn link ngẫu nhiên
    random_link = random.choice(config.GAME_LINKS)
    safe_link = _escape_url_for_markdownv2(random_link)

    # 2. Tạo nội dung tin nhắn
    text = (
        f"{RESPONSE_MESSAGES['provide_game_link_header']}\n"
        f"{RESPONSE_MESSAGES['provide_game_link_body']}\n\n"
        f"**{safe_link}**\n\n"
        f"_{RESPONSE_MESSAGES['provide_game_link_instruction']}_"
    )

    # 3. Tạo bàn phím mới
    keyboard = keyboards.create_game_link_options_keyboard(current_link=random_link)

    # 4. GỬI tin nhắn hoàn toàn mới
    sent_message = await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=keyboard,
        parse_mode='MarkdownV2'
    )
    helpers.add_message_to_cleanup_list(context, sent_message)
    if query:
        await helpers.delete_message_safely(context.bot, chat_id, query.message.message_id)

async def start_report_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Bắt đầu luồng báo cáo lỗi, hỏi người dùng có ảnh không."""
    query = update.callback_query
    await query.answer()

    try:
        # Lấy link hỏng từ callback_data
        broken_link = query.data.split(':', 1)[1]
        context.user_data['broken_link_to_report'] = broken_link
    except IndexError:
        await query.edit_message_text("Đã xảy ra lỗi, không tìm thấy link để báo cáo.")
        return ConversationHandler.END

    # Sử dụng các hàm từ file texts.py và keyboards.py
    text = RESPONSE_MESSAGES["ask_for_error_image"]
    keyboard = keyboards.create_ask_image_proof_keyboard()
    await helpers.edit_message_safely(query=query, new_text=text, new_reply_markup=keyboard)

    # Chuyển sang trạng thái hỏi có ảnh hay không
    return ASK_FOR_IMAGE

async def request_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Người dùng chọn 'Có', yêu cầu họ gửi ảnh."""
    query = update.callback_query
    await query.answer()

    # Lưu lại query này để có thể xóa tin nhắn "Vui lòng gửi ảnh..." sau
    context.user_data['original_query_message_id'] = query.message.message_id

    text = RESPONSE_MESSAGES["please_send_image"]
    await helpers.edit_message_safely(query=query, new_text=text,new_reply_markup=keyboards.create_back_to_main_menu_markup()) # Xóa bàn phím đi

    # Chuyển sang trạng thái chờ nhận ảnh
    return AWAITING_IMAGE

async def ask_for_vpn_confirmation_no_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Người dùng chọn không gửi ảnh, chuyển sang hỏi về VPN."""
    query = update.callback_query
    await query.answer()

    await helpers.edit_message_safely(
        query=query,
        new_text=RESPONSE_MESSAGES["ask_about_vpnn"],
        new_reply_markup=keyboards.get_vpn_confirmation_keyboard()
    )
    # Chuyển sang trạng thái chờ xác nhận VPN
    return AWAITING_VPN_CONFIRMATION

async def ask_for_vpn_confirmation_with_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Nhận ảnh, lưu lại thông tin và hỏi về VPN."""
    # LƯU Ý: Hàm này được kích hoạt bởi MessageHandler, không có query.

    # 1. Lưu file_id của ảnh vào context để dùng ở bước cuối
    photo_id = update.message.photo[-1].file_id
    context.user_data['report_photo_id'] = photo_id

    # 2. Xóa tin nhắn "Vui lòng gửi ảnh..."
    original_message_id = context.user_data.get('original_query_message_id')
    if original_message_id:
        await helpers.delete_message_safely(context.bot, update.effective_chat.id, original_message_id)

    # 3. Xóa tin nhắn chứa ảnh của người dùng để giữ chat gọn gàng
    await helpers.delete_message_safely(context.bot, update.effective_chat.id, update.message.message_id)

    # 4. Gửi một tin nhắn MỚI để hỏi về VPN
    await update.effective_chat.send_message(
        text=RESPONSE_MESSAGES["ask_about_vpn"],
        reply_markup=keyboards.get_vpn_confirmation_keyboard()
    )
    # Chuyển sang trạng thái chờ xác nhận VPN
    return AWAITING_VPN_CONFIRMATION

async def finalize_and_send_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Thu thập câu trả lời về VPN, tổng hợp và gửi báo cáo cuối cùng."""
    query = update.callback_query

    # Lấy thông tin đã lưu từ các bước trước
    user = update.effective_user
    broken_link = context.user_data.get('broken_link_to_report', 'Không xác định')
    photo_id = context.user_data.get('report_photo_id')  # Sẽ là None nếu không có ảnh
    vpn_choice = query.data  # Sẽ là 'vpn_yes' hoặc 'vpn_no'

    uses_vpn = "Có" if vpn_choice == 'vpn_yes' else "Không"

    report_caption = (
        f"⚠️ **BÁO CÁO LINK HỎNG** ⚠️\n\n"
        f"👤 **Người dùng:** [{escape_markdown(user.first_name, version=2)}](tg://user?id={user.id})\n"
        f"🔗 **Link lỗi:** `{_escape_url_for_markdownv2(broken_link)}`\n"
        f"📱 **Sử dụng VPN:** {uses_vpn}"
    )

    if config.ID_GROUP_LINK:
        try:
            if photo_id:
                await context.bot.send_photo(
                    chat_id=config.ID_GROUP_LINK,
                    photo=photo_id,
                    caption=report_caption,
                    parse_mode='MarkdownV2'
                )
            else:
                await context.bot.send_message(
                    chat_id=config.ID_GROUP_LINK,
                    text=report_caption,
                    parse_mode='MarkdownV2'
                )
        except Exception as e:
            logger.error(f"Không thể gửi báo cáo cho admin: {e}")

    # ===== GỬI POP-UP THÀNH CÔNG =====
    # Vì hàm này được kích hoạt bởi CallbackQuery, pop-up sẽ hoạt động.
    await query.answer(
        RESPONSE_MESSAGES["report_link_success_alert"],
        show_alert=True
    )

    # Xóa tin nhắn hỏi về VPN (chính là tin nhắn chứa nút vừa bấm)
    await query.delete_message()

    # Dọn dẹp context
    context.user_data.clear()

    # Cung cấp link game mới và kết thúc
    await provide_game_link(update, context)
    return ConversationHandler.END


async def invalid_message_in_report_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý tin nhắn không hợp lệ trong luồng báo cáo."""
    await update.message.reply_text(RESPONSE_MESSAGES["invalid_message_in_report_flow"])


# =================================================================
# === ĐỊNH NGHĨA CONVERSATION HANDLER =============================
# =================================================================

report_link_conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_report_flow, pattern='^report_broken_link:')],
    states={
        ASK_FOR_IMAGE: [
            CallbackQueryHandler(request_image, pattern='^report_error_with_image$'),
            CallbackQueryHandler(ask_for_vpn_confirmation_no_image, pattern='^report_error_without_image$')
        ],
        AWAITING_IMAGE: [
            MessageHandler(filters.PHOTO, ask_for_vpn_confirmation_with_image),
            # Thêm handler để nhắc người dùng nếu họ gửi văn bản thay vì ảnh
            MessageHandler(filters.TEXT & ~filters.COMMAND, invalid_message_in_report_flow)
        ],
        AWAITING_VPN_CONFIRMATION: [
            CallbackQueryHandler(finalize_and_send_report, pattern=r'^vpn_(yes|no)$')
        ]
    },
    fallbacks=get_fallbacks(),
    block=False,
    name="report_link_conversation"
)