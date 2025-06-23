import sys
import telegram # Đảm bảo đã import
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ApplicationBuilder
)
import datetime
import pytz
import re
import json
import os
import uuid
import logging
import inspect # Thêm để lấy tên hàm cho logging
from telegram.helpers import escape_markdown



# In ra thông tin môi trường để gỡ lỗi
print(f"Running python-telegram-bot version: {telegram.__version__}")
print(f"Python executable: {sys.executable}")
print(f"sys.path: {sys.path}")

# Cấu hình logging cơ bản
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- START IMAGE CONFIGURATION ---


try:
    from KL99 import BOT_TOKEN, APP_DOWNLOAD_LINK, GAME_LINK, TELEGRAM_CHANNEL_LINK, FACEBOOK_LINK, ID_GROUP_PROMO, CSKH_LINK, DATA_FILE, BOT_USERNAME as BOT_USERNAME_CONFIG, SHARE_MILESTONES, START_IMAGE_FILE_ID
    BOT_USERNAME = BOT_USERNAME_CONFIG
except ImportError:
    logger.warning("Lỗi: Không thể nhập một số cấu hình từ KL99.py. Sử dụng giá trị mặc định.")
    BOT_TOKEN = 'YOUR_FALLBACK_BOT_TOKEN'
    APP_DOWNLOAD_LINK = 'https://example.com/download'
    GAME_LINK = 'https://example.com/game'
    TELEGRAM_CHANNEL_LINK = 'https://t.me/examplechannel'
    FACEBOOK_LINK = 'https://facebook.com/examplepage'
    CSKH_LINK = 'https://example.com/cskh'
    ID_GROUP_PROMO = -1001234567890
    DATA_FILE = 'bot_data.json'
    BOT_USERNAME = None
    SHARE_MILESTONES = [15, 30, 50, 100]
    START_IMAGE_FILE_ID = None # Fallback nếu không có trong KL99.py
    if BOT_TOKEN == 'YOUR_FALLBACK_BOT_TOKEN':
        logger.error("CRITICAL: BOT_TOKEN không được cấu hình!")


try:
    from texts import (
        RESPONSE_MESSAGES,
        PROMO_TEXT_KL001,
        PROMO_TEXT_KL006,
        PROMO_TEXT_KL007,
        PROMO_TEXT_APP_EXPERIENCE,
        YESTERDAY_DMY
    )
except ImportError:
    logger.error("CRITICAL: Không thể nhập các chuỗi văn bản từ texts.py. Bot có thể không hoạt động đúng.")
    # Fallback messages
    RESPONSE_MESSAGES = {
        "yeu_cau_dang_xu_ly": "Yêu cầu đang xử lý (lỗi texts.py)",
        "welcome_message": "Chào mừng (lỗi texts.py)",
        "khuyen_mai_button_text": "🎁 Nhận khuyến mãi (lỗi texts.py)",
        "share_code_button_text": "🤝 Chia sẻ nhận Code (lỗi texts.py)",
        "download_app_button_text": "📱 Tải ứng dụng (lỗi texts.py)",
        "homepage_button_text": "🎮 Trang chủ (lỗi texts.py)",
        "facebook_button_text": "👍 Facebook (lỗi texts.py)",
        "telegram_channel_button_text": "📣 Kênh thông báo (lỗi texts.py)",
        "cskh_button_text": "💬 CSKH trực tuyến (lỗi texts.py)",
        "cannot_refer_self": "Bạn không thể tự giới thiệu chính mình (lỗi texts.py)",
        "already_referred_error": "Tài khoản của bạn đã được ghi nhận là được giới thiệu trước đó (lỗi texts.py)",
        "referral_successful_notification_to_referrer": "Bạn có lượt chia sẻ mới! Tổng: {share_count} (lỗi texts.py)",
        "new_user_welcome_referred": "Chào mừng! Bạn được giới thiệu bởi {referrer_name} (lỗi texts.py)",
        "new_user_welcome_referred_generic": "Chào mừng bạn đến với chúng tôi qua một lời giới thiệu! (lỗi texts.py)",
        "promo_kl001_button": "Khuyến mãi nạp đầu - KL001 (lỗi texts.py)",
        "promo_kl006_button": "Khuyến mãi đội nhóm - KL006 (lỗi texts.py)",
        "promo_kl007_button": "Siêu tiền thưởng - KL007 (lỗi texts.py)",
        "promo_app_button": "KM Trải nghiệm Tải App (lỗi texts.py)",
        "back_to_menu_button": "⬅️ Quay lại Menu (lỗi texts.py)",
        "choose_promo_message": "Chọn khuyến mãi: (lỗi texts.py)",
        "agree_button_text": "✅ Đồng ý (lỗi texts.py)",
        "back_to_promo_menu_button_text": "⬅️ Quay lại Menu KM (lỗi texts.py)",
        "ask_username_kl001_after_agree": "Vui lòng nhập tên đăng nhập (username) của bạn: (lỗi texts.py)",
        "error_sending_request": "Đã xảy ra lỗi khi xử lý yêu cầu của bạn. Vui lòng thử lại sau. (lỗi texts.py)",
        "ask_username_kl007": "Vui lòng nhập tên đăng nhập (username) của bạn: (lỗi texts.py)",
        "kl006_agree_ask_group_size": "Vui lòng chọn số lượng thành viên trong nhóm của bạn: (lỗi texts.py)",
        "kl006_ask_usernames": "Cung cấp {group_size} tên: (lỗi texts.py)",
        "kl006_invalid_username_count": "Số lượng tên ({submitted_count}) không khớp ({expected_count}). (lỗi texts.py)",
        "ask_username_app_promo": "Vui lòng nhập tên đăng nhập (username) của bạn: (lỗi texts.py)",
        "app_promo_ask_image": "Có ảnh xác nhận không? (lỗi texts.py)",
        "app_promo_request_image": "Gửi ảnh vào đây: (lỗi texts.py)",
        "app_promo_image_sent_to_admin": "Đã gửi ảnh. (lỗi texts.py)",
        "app_promo_no_image_sent_to_admin": "Đã gửi yêu cầu (không ảnh). (lỗi texts.py)",
        "app_promo_yeu_cau_hinh_anh": "Admin yêu cầu bạn cung cấp hình ảnh xác nhận cho KM Tải App. Vui lòng bắt đầu lại quá trình đăng ký KM Tải App và gửi kèm hình ảnh. (lỗi texts.py)",
        "thanh_cong_kl007_points": "🎉 Chúc mừng {customer_username}! Bạn đã được cộng {points} điểm thưởng từ khuyến mãi KL007. Vui lòng kiểm tra tài khoản game. (lỗi texts.py)",
        "request_cancelled": "Yêu cầu đã được hủy bỏ. (lỗi texts.py)",
        "share_code_intro": "Bạn có {share_count} lượt chia sẻ. Mốc kế: {next_milestone}. Cần thêm: {needed_shares} lượt. (lỗi texts.py)",
        "share_code_intro_no_shares": "Hãy bắt đầu chia sẻ để nhận thưởng! (lỗi texts.py)",
        "all_milestones_achieved_text": "Đã hoàn thành tất cả (lỗi texts.py)",
        "check_reward_button_text": "Kiểm tra phần thưởng (lỗi texts.py)",
        "request_code_reward_button": "💰 Nhận Code thưởng (lỗi texts.py)",
        "get_my_share_link_button": "🔗 Link chia sẻ của tôi (lỗi texts.py)",
        "error_getting_bot_info": "Lỗi: Không thể lấy thông tin bot. Vui lòng thử lại sau. (lỗi texts.py)",
        "error_no_referral_code": "Lỗi: Không tìm thấy mã giới thiệu. Thử lại /start. (lỗi texts.py)",
        "my_share_link_message": "Link của bạn: {share_link} (lỗi texts.py)",
        "pending_claim_exists": "Yêu cầu trước đang xử lý cho mốc {milestone}... (lỗi texts.py)",
        "cancel_and_back_share_menu_button": "⬅️ Hủy & Quay lại (lỗi texts.py)",
        "ask_username_for_share_reward": "Nhập username cho mốc {milestone}: (lỗi texts.py)",
        "all_milestones_claimed_message": "Bạn đã nhận hết các mốc thưởng! (lỗi texts.py)",
        "no_new_milestone_message": "Cần {needed_more} lượt cho mốc {next_milestone}. (lỗi texts.py)",
        "no_milestones_available_at_moment": "Hiện tại bạn chưa đạt mốc thưởng mới hoặc đã nhận hết các mốc có thể. Hãy tiếp tục chia sẻ! (lỗi texts.py)",
        "error_no_milestone_info": "Lỗi không tìm thấy mốc thưởng. Thử lại. (lỗi texts.py)",
        "back_to_share_menu_button": "⬅️ Menu Chia Sẻ (lỗi texts.py)",
        "return_to_share_menu_prompt": "Vui lòng quay lại menu Chia sẻ: (lỗi texts.py)",
        "share_admin_request_text": "Y/c thưởng chia sẻ: Khách {user_first_name} (ID {user_id}), GameUser {game_username}, Mốc {milestone} (lỗi texts.py)",
        "share_reward_request_sent": "Đã gửi y/c cho mốc {milestone} với tên {game_username}. (lỗi texts.py)",
        "error_sending_to_admin": "Lỗi gửi yêu cầu đến admin. Thử lại sau. (lỗi texts.py)",
        "share_reward_approved": "Mốc {milestone} được duyệt cho {game_username}. (lỗi texts.py)",
        "share_reward_sai_id": "Mốc {milestone}, sai ID. (lỗi texts.py)",
        "share_reward_contact_cskh": "Mốc {milestone}, liên hệ CSKH. (lỗi texts.py)"
    }
    PROMO_TEXT_KL001 = "Nội dung KL001 (lỗi texts.py)"
    PROMO_TEXT_KL006 = "Nội dung KL006 (lỗi texts.py)"
    PROMO_TEXT_KL007 = "Nội dung KL007 (lỗi texts.py)"
    PROMO_TEXT_APP_EXPERIENCE = "Nội dung KM Tải App (lỗi texts.py)"
    YESTERDAY_DMY = datetime.datetime.now(pytz.timezone('Asia/Ho_Chi_Minh')).strftime('%d/%m/%Y')


def load_bot_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Lỗi giải mã JSON trong file {DATA_FILE}. Trả về dữ liệu rỗng.")
                return {"users": {}, "referral_code_to_user_id_map": {}}
    return {"users": {}, "referral_code_to_user_id_map": {}}

def save_bot_data(data):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Lỗi khi lưu dữ liệu vào {DATA_FILE}: {e}")

def get_user_data_from_json(user_id):
    data = load_bot_data()
    user_id_str = str(user_id)

    if user_id_str not in data["users"]:
        unique_ref_code = str(uuid.uuid4())[:8]
        while unique_ref_code in data["referral_code_to_user_id_map"]:
            unique_ref_code = str(uuid.uuid4())[:8]

        data["users"][user_id_str] = {
            "referral_code": unique_ref_code,
            "share_count": 0,
            "claimed_share_milestones": {},
            "pending_share_milestone_claim": None,
            "was_referred_by_user_id": None,
            "claimed_promos": {}
        }
        data["referral_code_to_user_id_map"][unique_ref_code] = user_id_str
        save_bot_data(data)
        logger.info(f"Khởi tạo dữ liệu cho người dùng mới: {user_id_str} với mã giới thiệu {unique_ref_code}")
    return data["users"][user_id_str]

# Định nghĩa các trạng thái cho ConversationHandler
RECEIVE_USERNAME_KL001 = 1
RECEIVE_USERNAME_KL007 = 2
KL006_CHOOSE_GROUP_SIZE = 3
RECEIVE_USERNAMES_KL006 = 4
RECEIVE_USERNAME_APP_PROMO = 5
AWAIT_IMAGE_CONFIRM_APP_PROMO = 6
RECEIVE_IMAGE_APP_PROMO = 7
AGREE_TERMS_KL001 = 101
AGREE_TERMS_KL007 = 102
AGREE_TERMS_KL006 = 103
AGREE_TERMS_APP_PROMO = 104
SHOW_SHARE_MENU, AWAIT_USERNAME_FOR_SHARE_REWARD = range(105, 107)


async def _remove_buttons_from_previous_message(query: CallbackQuery):
    """Hàm tiện ích để xóa nút khỏi tin nhắn của callback query."""
    if query and query.message:
        try:
            await query.edit_message_reply_markup(reply_markup=None)
            logger.info(f"Đã xóa nút từ tin nhắn {query.message.message_id} (callback: {query.data})")
        except telegram.error.BadRequest as e:
            if "message is not modified" in str(e).lower() or \
               "message to edit not found" in str(e).lower() or \
               "message can't be edited" in str(e).lower(): # Thêm "message can't be edited"
                logger.info(f"Tin nhắn {query.message.message_id} không có nút, không tìm thấy hoặc không thể sửa để xóa nút (callback: {query.data}). Lỗi: {e}")
            else:
                func_name = inspect.currentframe().f_back.f_code.co_name # Lấy tên hàm gọi _remove_buttons_from_previous_message
                logger.warning(f"Lỗi khi xóa nút từ tin nhắn {query.message.message_id} trong hàm '{func_name}' (callback: {query.data}): {e}")
        except Exception as e: # Bắt các lỗi khác
            func_name = inspect.currentframe().f_back.f_code.co_name
            logger.error(f"Lỗi không mong muốn khi xóa nút từ tin nhắn {query.message.message_id} trong hàm '{func_name}' (callback: {query.data}): {e}")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    global BOT_USERNAME
    if BOT_USERNAME is None and context.bot:
        try:
            bot_info = await context.bot.get_me()
            BOT_USERNAME = bot_info.username
            logger.info(f"Tên bot đã được đặt trong /start: {BOT_USERNAME}")
        except Exception as e:
            logger.error(f"Không thể lấy thông tin bot trong /start: {e}")

    user = update.effective_user
    chat_id = update.effective_chat.id # Lấy chat_id một cách nhất quán
    user_id_str = str(user.id)

    if update.message:
        logger.info(f"Lệnh /start từ user: {user.id} ({user.username}), Args: {context.args} trong chat {chat_id}")
    elif update.callback_query:
        query = update.callback_query
        logger.info(f"start function called from callback_query: {query.data} by user {query.from_user.id} trong chat {chat_id}")

    get_user_data_from_json(user.id)

    if context.args and len(context.args) > 0 and context.args[0].startswith('ref_') and update.message: # Chỉ xử lý referral khi là message /start mới
        referral_code_input = context.args[0][4:]
        all_data = load_bot_data()
        referrer_user_id_str = all_data["referral_code_to_user_id_map"].get(referral_code_input)

        if referrer_user_id_str:
            try:
                referrer_user_id_int = int(referrer_user_id_str)
                if user.id == referrer_user_id_int:
                    await update.message.reply_text(RESPONSE_MESSAGES.get("cannot_refer_self", "Bạn không thể tự giới thiệu chính mình."))
                else:
                    current_user_s_data = all_data["users"].get(user_id_str)
                    if current_user_s_data and current_user_s_data.get("was_referred_by_user_id"):
                        await update.message.reply_text(RESPONSE_MESSAGES.get("already_referred_error", "Tài khoản của bạn đã được ghi nhận là được giới thiệu trước đó."))
                    else:
                        all_data["users"][user_id_str]["was_referred_by_user_id"] = referrer_user_id_str
                        if referrer_user_id_str in all_data["users"]:
                            all_data["users"][referrer_user_id_str]["share_count"] = all_data["users"][referrer_user_id_str].get("share_count", 0) + 1
                            save_bot_data(all_data)
                            logger.info(f"User {user_id_str} được giới thiệu bởi {referrer_user_id_str}. Lượt chia sẻ của người giới thiệu tăng lên {all_data['users'][referrer_user_id_str]['share_count']}.")
                            try:
                                referrer_share_count = all_data["users"][referrer_user_id_str]["share_count"]
                                await context.bot.send_message(
                                    chat_id=referrer_user_id_int,
                                    text=RESPONSE_MESSAGES.get("referral_successful_notification_to_referrer", "Bạn có lượt chia sẻ mới! Tổng: {share_count}").format(share_count=referrer_share_count)
                                )
                            except Exception as e:
                                logger.error(f"Không thể thông báo cho người giới thiệu {referrer_user_id_str}: {e}")
                            try:
                                referrer_chat = await context.bot.get_chat(referrer_user_id_int)
                                referrer_display_name = referrer_chat.first_name or referrer_chat.username or f"User {referrer_user_id_str}"
                                await update.message.reply_text(
                                    RESPONSE_MESSAGES.get("new_user_welcome_referred", "Chào mừng! Bạn được giới thiệu bởi {referrer_name}.").format(referrer_name=referrer_display_name)
                                )
                            except Exception as e:
                                logger.error(f"Không thể lấy thông tin người giới thiệu {referrer_user_id_str}: {e}")
                                await update.message.reply_text(RESPONSE_MESSAGES.get("new_user_welcome_referred_generic", "Chào mừng bạn đến với chúng tôi qua một lời giới thiệu!"))
                        else:
                            logger.warning(f"ID người giới thiệu {referrer_user_id_str} không tìm thấy trong users dict sau khi giới thiệu.")
            except ValueError:
                 logger.error(f"Lỗi chuyển đổi ID người giới thiệu: {referrer_user_id_str}")
            except Exception as e:
                 logger.error(f"Lỗi không xác định trong quá trình xử lý giới thiệu: {e}")
        else:
            logger.info(f"Mã giới thiệu không hợp lệ hoặc không tìm thấy: {referral_code_input}")

    keyboard_buttons = [
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("khuyen_mai_button_text","🎁 Nhận khuyến mãi"), callback_data='khuyen_mai')],
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("share_code_button_text","🤝 Chia sẻ nhận Code"), callback_data='share_code_entry_point')],
        [
            InlineKeyboardButton(RESPONSE_MESSAGES.get("download_app_button_text","📱 Tải ứng dụng"), url=APP_DOWNLOAD_LINK),
            InlineKeyboardButton(RESPONSE_MESSAGES.get("homepage_button_text","🎮 Trang chủ"), url=GAME_LINK)
        ],
        [
            InlineKeyboardButton(RESPONSE_MESSAGES.get("facebook_button_text","👍 Facebook"), url=FACEBOOK_LINK),
            InlineKeyboardButton(RESPONSE_MESSAGES.get("telegram_channel_button_text","📣 Kênh thông báo"), url=TELEGRAM_CHANNEL_LINK)
        ],
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("cskh_button_text","💬 CSKH trực tuyến"), url=CSKH_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard_buttons)
    welcome_caption = RESPONSE_MESSAGES.get("welcome_message", "Chào mừng bạn!")

    # Sử dụng START_IMAGE_FILE_ID đã import
    current_start_image_file_id = START_IMAGE_FILE_ID

    if update.message and (not context.args or update.message.text == "/start"):
        if current_start_image_file_id:
            await update.message.reply_photo(
                photo=current_start_image_file_id,
                caption=welcome_caption,
                reply_markup=reply_markup
                # parse_mode='Markdown' # Nếu caption cần Markdown
            )
        else:
            await update.message.reply_text(welcome_caption, reply_markup=reply_markup)
    elif update.callback_query:
        query = update.callback_query
        await _remove_buttons_from_previous_message(query) # Xóa nút trên tin nhắn cũ

        if current_start_image_file_id:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=current_start_image_file_id,
                caption=welcome_caption,
                reply_markup=reply_markup
                # parse_mode='Markdown' # Nếu caption cần Markdown
            )
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=welcome_caption,
                reply_markup=reply_markup
            )
        logger.info(f"start: Đã gửi tin nhắn welcome mới tới chat {chat_id} sau callback.")

    return ConversationHandler.END


async def khuyen_mai_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: # Hoặc int nếu là state
    query = update.callback_query
    await query.answer()
    await _remove_buttons_from_previous_message(query)

    promotions_keyboard = [
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("promo_kl001_button", "Khuyến mãi nạp đầu - KL001"), callback_data='promo_KL001')],
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("promo_kl006_button", "Khuyến mãi đội nhóm - KL006"), callback_data='promo_KL006')],
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("promo_kl007_button", "Siêu tiền thưởng - KL007"), callback_data='promo_KL007')],
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("promo_app_button", "KM Trải nghiệm Tải App"), callback_data='promo_app_experience')],
        [
            InlineKeyboardButton(RESPONSE_MESSAGES.get("back_to_menu_button", "⬅️ Quay lại Menu"), callback_data='back_to_menu'),
            InlineKeyboardButton(RESPONSE_MESSAGES.get("cskh_button_text","💬 CSKH trực tuyến"), url=CSKH_LINK)
        ]
    ]
    promotions_reply_markup = InlineKeyboardMarkup(promotions_keyboard)
    
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=RESPONSE_MESSAGES.get("choose_promo_message", "Chọn khuyến mãi:"), 
        reply_markup=promotions_reply_markup
    )
    # Nếu đây là một state trong ConversationHandler, cần trả về state đó.
    # Nếu là fallback và muốn kết thúc conversation, trả về ConversationHandler.END
    # Nếu là handler độc lập, không cần trả về gì.


async def promo_KL001_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await _remove_buttons_from_previous_message(query)

    keyboard = [
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("agree_button_text", "✅ Đồng ý"), callback_data='agree_terms_kl001')],
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("back_to_promo_menu_button_text", "⬅️ Quay lại Menu KM"), callback_data='khuyen_mai')],
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("cskh_button_text","💬 CSKH trực tuyến"), url=CSKH_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=PROMO_TEXT_KL001, 
        reply_markup=reply_markup, 
        parse_mode='Markdown'
    )
    return AGREE_TERMS_KL001

async def handle_agree_kl001_terms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await _remove_buttons_from_previous_message(query)

    keyboard = [
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("back_to_promo_menu_button_text", "⬅️ Quay lại Menu KM"), callback_data='khuyen_mai')],
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("cskh_button_text","💬 CSKH trực tuyến"), url=CSKH_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    ask_username_text = RESPONSE_MESSAGES.get("ask_username_kl001_after_agree", "Vui lòng nhập tên đăng nhập (username) của bạn:")
    
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=ask_username_text, 
        reply_markup=reply_markup
    )
    return RECEIVE_USERNAME_KL001

# Hàm receive_username_kl001, receive_username_kl007, receive_usernames_kl006, receive_image_app_promo


async def promo_KL007_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await _remove_buttons_from_previous_message(query)
    keyboard = [
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("agree_button_text", "✅ Đồng ý"), callback_data='agree_terms_kl007')],
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("back_to_promo_menu_button_text", "⬅️ Quay lại Menu KM"), callback_data='khuyen_mai')],
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("cskh_button_text","💬 CSKH trực tuyến"), url=CSKH_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=PROMO_TEXT_KL007, 
        reply_markup=reply_markup, 
        parse_mode='Markdown'
    )
    return AGREE_TERMS_KL007

async def handle_agree_kl007_terms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await _remove_buttons_from_previous_message(query)
    keyboard = [
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("back_to_promo_menu_button_text", "⬅️ Quay lại Menu KM"), callback_data='khuyen_mai')],
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("cskh_button_text","💬 CSKH trực tuyến"), url=CSKH_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    ask_username_text = RESPONSE_MESSAGES.get("ask_username_kl007", "Vui lòng nhập tên đăng nhập (username) của bạn:")
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=ask_username_text, 
        reply_markup=reply_markup
    )
    return RECEIVE_USERNAME_KL007

async def promo_KL006_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await _remove_buttons_from_previous_message(query)
    keyboard = [
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("agree_button_text", "✅ Đồng ý"), callback_data='agree_terms_kl006')],
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("back_to_promo_menu_button_text", "⬅️ Quay lại Menu KM"), callback_data='khuyen_mai')],
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("cskh_button_text","💬 CSKH trực tuyến"), url=CSKH_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=PROMO_TEXT_KL006, 
        reply_markup=reply_markup, 
        parse_mode='Markdown'
    )
    return AGREE_TERMS_KL006

async def handle_agree_kl006_terms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await _remove_buttons_from_previous_message(query)
    keyboard = [
        [InlineKeyboardButton("Nhóm 3 thành viên", callback_data='kl006_select_group:3')],
        [InlineKeyboardButton("Nhóm 5 thành viên", callback_data='kl006_select_group:5')],
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("back_to_promo_menu_button_text", "⬅️ Quay lại Menu KM"), callback_data='khuyen_mai')],
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("cskh_button_text","💬 CSKH trực tuyến"), url=CSKH_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    ask_group_size_text = RESPONSE_MESSAGES.get("kl006_agree_ask_group_size", "Vui lòng chọn số lượng thành viên trong nhóm của bạn:")
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=ask_group_size_text, 
        reply_markup=reply_markup, 
        parse_mode='Markdown'
    )
    return KL006_CHOOSE_GROUP_SIZE

async def kl006_group_size_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await _remove_buttons_from_previous_message(query)
    group_size = int(query.data.split(':')[1])
    context.user_data['kl006_group_size'] = group_size
    keyboard = [
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("back_to_promo_menu_button_text", "⬅️ Quay lại Menu KM"), callback_data='khuyen_mai')],
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("cskh_button_text","💬 CSKH trực tuyến"), url=CSKH_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    ask_username_text = RESPONSE_MESSAGES.get("kl006_ask_usernames", "Cung cấp {group_size} tên:").format(group_size=group_size)
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=ask_username_text, 
        reply_markup=reply_markup
    )
    return RECEIVE_USERNAMES_KL006

async def kl006_reenter_usernames_after_agree_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await _remove_buttons_from_previous_message(query) # Xóa nút "Nhập lại..." trên tin nhắn báo lỗi
    group_size = int(query.data.split(':')[1])
    context.user_data['kl006_group_size'] = group_size
    keyboard = [
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("back_to_promo_menu_button_text", "⬅️ Quay lại Menu KM"), callback_data='khuyen_mai')],
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("cskh_button_text","💬 CSKH trực tuyến"), url=CSKH_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    ask_username_text = RESPONSE_MESSAGES.get("kl006_ask_usernames", "Cung cấp {group_size} tên:").format(group_size=group_size)
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=ask_username_text, 
        reply_markup=reply_markup
    )
    return RECEIVE_USERNAMES_KL006

async def promo_app_experience_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await _remove_buttons_from_previous_message(query)
    keyboard = [
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("agree_button_text", "✅ Đồng ý"), callback_data='agree_terms_app_promo')],
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("back_to_promo_menu_button_text", "⬅️ Quay lại Menu KM"), callback_data='khuyen_mai')],
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("cskh_button_text","💬 CSKH trực tuyến"), url=CSKH_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=PROMO_TEXT_APP_EXPERIENCE, 
        reply_markup=reply_markup, 
        parse_mode='Markdown'
    )
    return AGREE_TERMS_APP_PROMO

async def handle_agree_app_promo_terms(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await _remove_buttons_from_previous_message(query)
    keyboard = [
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("back_to_promo_menu_button_text", "⬅️ Quay lại Menu KM"), callback_data='khuyen_mai')],
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("cskh_button_text","💬 CSKH trực tuyến"), url=CSKH_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    ask_username_text = RESPONSE_MESSAGES.get("ask_username_app_promo", "Vui lòng nhập tên đăng nhập (username) của bạn:")
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=ask_username_text, 
        reply_markup=reply_markup
    )
    return RECEIVE_USERNAME_APP_PROMO

async def handle_image_confirm_app_promo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await _remove_buttons_from_previous_message(query) # Xóa nút "Có ảnh/Không có ảnh"
    
    choice = query.data.split(':')[1]
    if choice == 'yes':
        keyboard = [
            [InlineKeyboardButton(RESPONSE_MESSAGES.get("back_to_promo_menu_button_text", "⬅️ Quay lại Menu KM"), callback_data='khuyen_mai')],
            [InlineKeyboardButton(RESPONSE_MESSAGES.get("cskh_button_text","💬 CSKH trực tuyến"), url=CSKH_LINK)]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=RESPONSE_MESSAGES.get("app_promo_request_image", "Gửi ảnh vào đây:"), 
            reply_markup=reply_markup
        )
        return RECEIVE_IMAGE_APP_PROMO
    else: # choice == 'no'
        # Gọi no_image_app_promo, hàm này sẽ gửi tin nhắn mới
        return await no_image_app_promo(update, context) # update đã chứa query

async def no_image_app_promo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query 
    chat_id_to_reply = None
    user_id = None
    user_first_name = None

    if query:
        # await query.answer() # Đã answer ở handle_image_confirm_app_promo
        # await _remove_buttons_from_previous_message(query) # Đã xóa ở handle_image_confirm_app_promo
        
        user_id = query.from_user.id
        user_first_name = query.from_user.first_name
        chat_id_to_reply = query.message.chat_id
        
        # Gửi tin nhắn "Yêu cầu đang xử lý..." mới thay vì edit
        await context.bot.send_message(
            chat_id=chat_id_to_reply,
            text=RESPONSE_MESSAGES.get("yeu_cau_dang_xu_ly", "Yêu cầu đang xử lý...")
        )
    else: 
        logger.error("no_image_app_promo called without a callback_query unexpectedly.")
        return ConversationHandler.END

    customer_username = context.user_data.get('app_promo_username', 'N/A')
    promo_code = "APP_PROMO"
    admin_message_text_to_group = (
        f"Yêu cầu {promo_code} (KHÔNG có ảnh):\n"
        f"Khách: {user_first_name} (TG ID: {user_id})\n"
        f"Tên đăng nhập: {customer_username}"
    )
    admin_buttons = [ 
        [
            InlineKeyboardButton("Sai ID", callback_data=f"admin_response:{user_id}:sai_id:{promo_code}"),
            InlineKeyboardButton("✅ Thành Công", callback_data=f"admin_response:{user_id}:app_promo_thanh_cong:{promo_code}")
        ],
        [
            InlineKeyboardButton("Đã nhận KM Tải App", callback_data=f"admin_response:{user_id}:app_promo_da_nhan:{promo_code}"),
            InlineKeyboardButton("Y/c hình ảnh", callback_data=f"admin_response:{user_id}:app_promo_yeu_cau_hinh_anh:{promo_code}")
        ],
        [
            InlineKeyboardButton("Trùng IP (App)", callback_data=f"admin_response:{user_id}:app_promo_trung_ip:{promo_code}"),
            InlineKeyboardButton("Đã nạp/rút (App)", callback_data=f"admin_response:{user_id}:app_promo_da_nap_rut_nhieu:{promo_code}")
        ],
        [
            InlineKeyboardButton("Chưa LK NH", callback_data=f"admin_response:{user_id}:chua_lien_ket_ngan_hang:{promo_code}"),
            InlineKeyboardButton("Sai TT (CSKH)", callback_data=f"admin_response:{user_id}:sai_thong_tin_lien_he_cskh:{promo_code}")
        ]
    ]
    admin_reply_markup = InlineKeyboardMarkup(admin_buttons)
    customer_final_buttons = [[InlineKeyboardButton(RESPONSE_MESSAGES.get("cskh_button_text","💬 CSKH trực tuyến"), url=CSKH_LINK)], [InlineKeyboardButton(RESPONSE_MESSAGES.get("back_to_menu_button","⬅️ Quay lại Menu"), callback_data='back_to_menu')]]
    customer_final_markup = InlineKeyboardMarkup(customer_final_buttons)

    try:
        await context.bot.send_message(
            chat_id=ID_GROUP_PROMO,
            text=admin_message_text_to_group,
            reply_markup=admin_reply_markup
        )
        msg_to_customer = RESPONSE_MESSAGES.get("app_promo_no_image_sent_to_admin", "Đã gửi yêu cầu (không ảnh).")
        if chat_id_to_reply:
             await context.bot.send_message(chat_id=chat_id_to_reply, text=msg_to_customer, reply_markup=customer_final_markup)
    except Exception as e:
        logger.error(f"Lỗi khi gửi yêu cầu {promo_code} (không ảnh) đến nhóm: {e}")
        error_message_for_customer = RESPONSE_MESSAGES.get("error_sending_request", "Đã xảy ra lỗi khi xử lý yêu cầu của bạn. Vui lòng thử lại sau.")
        if chat_id_to_reply:
            await context.bot.send_message(chat_id=chat_id_to_reply, text=error_message_for_customer, reply_markup=customer_final_markup)

    if 'app_promo_username' in context.user_data: del context.user_data['app_promo_username']
    return ConversationHandler.END

async def re_enter_username_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    await _remove_buttons_from_previous_message(query) # Xóa nút "Đăng ký lại KM..."

    parts = query.data.split(':') 
    action_type = parts[0] 
    
    promo_code = ""
    next_state = ConversationHandler.END
    promo_text_key = ""
    text_format_params = {}

    if action_type == "re_enter_username": 
        promo_code = parts[1] 
        text_format_params['promo_code'] = promo_code
        if promo_code == "KL001":
            promo_text_key = "ask_username_kl001_after_agree"
            next_state = RECEIVE_USERNAME_KL001
        elif promo_code == "KL007":
            promo_text_key = "ask_username_kl007" 
            next_state = RECEIVE_USERNAME_KL007
        elif promo_code == "APP_PROMO":
            promo_text_key = "ask_username_app_promo"
            next_state = RECEIVE_USERNAME_APP_PROMO
        else:
            await context.bot.send_message(chat_id=query.message.chat_id, text="Mã khuyến mãi không hợp lệ để nhập lại. Vui lòng thử lại từ Menu Chính.")
            return ConversationHandler.END

    elif action_type == "kl006_reenter_usernames_after_agree": 
        promo_code = "KL006"
        group_size = int(parts[1]) 
        context.user_data['kl006_group_size'] = group_size
        promo_text_key = "kl006_ask_usernames"
        text_format_params['group_size'] = group_size
        next_state = RECEIVE_USERNAMES_KL006
    else: 
        await context.bot.send_message(chat_id=query.message.chat_id, text="Lỗi cấu trúc yêu cầu nhập lại. Vui lòng thử lại từ Menu Khuyến Mãi.")
        return ConversationHandler.END

    final_promo_text = RESPONSE_MESSAGES.get(promo_text_key, "Lỗi: Không tìm thấy nội dung yêu cầu. Vui lòng nhập thông tin được yêu cầu:")
    if text_format_params:
        try:
            final_promo_text = final_promo_text.format(**text_format_params)
        except KeyError:
            logger.warning(f"Lỗi format text cho re_enter_username: key='{promo_text_key}', params={text_format_params}")

    new_keyboard = [[InlineKeyboardButton(RESPONSE_MESSAGES.get("back_to_menu_button","⬅️ Quay lại Menu"), callback_data='back_to_menu')], 
                    [InlineKeyboardButton(RESPONSE_MESSAGES.get("cskh_button_text","💬 CSKH trực tuyến"), url=CSKH_LINK)]]
    new_reply_markup = InlineKeyboardMarkup(new_keyboard)

    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text=final_promo_text,
        reply_markup=new_reply_markup
    )
    return next_state

async def back_to_menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    logger.info(f"back_to_menu_handler called by user {update.effective_user.id}")
    keys_to_clear = ['kl006_group_size', 'app_promo_username', 'milestone_to_claim_share', 'share_reward_milestone']
    for key in keys_to_clear:
        if key in context.user_data:
            del context.user_data[key]
            logger.info(f"Cleared '{key}' from user_data for user {update.effective_user.id}")
    
    if update.callback_query:
        await update.callback_query.answer()
        # await _remove_buttons_from_previous_message(update.callback_query) # start sẽ làm việc này
    
    await start(update, context) # start sẽ xử lý việc xóa nút và gửi tin nhắn mới
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    cancel_message = RESPONSE_MESSAGES.get("request_cancelled", "Yêu cầu đã được hủy bỏ.")
    chat_id = update.effective_chat.id

    if update.message: # User gõ /cancel
        await update.message.reply_text(cancel_message) # Gửi tin nhắn cancel mới
    elif update.callback_query: # User bấm nút cancel (nếu có)
        query = update.callback_query
        await query.answer()
        await _remove_buttons_from_previous_message(query) # Xóa nút trên tin nhắn hiện tại
        await context.bot.send_message(chat_id=chat_id, text=cancel_message) # Gửi tin nhắn cancel mới

    keys_to_clear = ['kl006_group_size', 'app_promo_username', 'milestone_to_claim_share', 'share_reward_milestone']
    for key in keys_to_clear:
        if key in context.user_data:
            del context.user_data[key]
            logger.info(f"Cancel: Cleared '{key}' from user_data for user {update.effective_user.id}")
            
    await start(update, context) # start sẽ hiển thị menu chính mới
    return ConversationHandler.END

async def share_code_entry_point(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    chat_id = update.effective_chat.id
    if query: 
        await query.answer()
        await _remove_buttons_from_previous_message(query)

    user_id = update.effective_user.id
    user_s_data = get_user_data_from_json(user_id)
    share_count = user_s_data.get("share_count", 0)
    intro_text_key = "share_code_intro"
    format_params = {"share_count": share_count} 
    next_milestone_val = None
    for ms in SHARE_MILESTONES: 
        if str(ms) not in user_s_data.get("claimed_share_milestones", {}):
            if share_count < ms : 
                next_milestone_val = ms 
                break
    
    if next_milestone_val is None: 
        smallest_unclaimed_milestone = None
        for ms_check in sorted(SHARE_MILESTONES):
            if str(ms_check) not in user_s_data.get("claimed_share_milestones", {}):
                smallest_unclaimed_milestone = ms_check
                break
        if smallest_unclaimed_milestone is not None and share_count < smallest_unclaimed_milestone:
            next_milestone_val = smallest_unclaimed_milestone

    if share_count == 0:
        intro_text_key = "share_code_intro_no_shares"
        # Đảm bảo các placeholder được cung cấp nếu intro_text_key này cần
        if intro_text_key in RESPONSE_MESSAGES and "{next_milestone}" in RESPONSE_MESSAGES[intro_text_key]:
             format_params["next_milestone"] = str(SHARE_MILESTONES[0]) if SHARE_MILESTONES else "N/A"
        if intro_text_key in RESPONSE_MESSAGES and "{needed_shares}" in RESPONSE_MESSAGES[intro_text_key]:
             format_params["needed_shares"] = SHARE_MILESTONES[0] - share_count if SHARE_MILESTONES else 0

    elif next_milestone_val:
        format_params["next_milestone"] = str(next_milestone_val) 
        format_params["needed_shares"] = next_milestone_val - share_count 
    else: 
        all_milestones_claimed_check = all(str(ms_check) in user_s_data.get("claimed_share_milestones", {}) for ms_check in SHARE_MILESTONES)
        if all_milestones_claimed_check:
             format_params["next_milestone"] = RESPONSE_MESSAGES.get("all_milestones_achieved_text", "Đã hoàn thành tất cả") 
             format_params["needed_shares"] = 0 
        else: 
             format_params["next_milestone"] = RESPONSE_MESSAGES.get("check_reward_button_text", "Kiểm tra phần thưởng") 
             format_params["needed_shares"] = 0 

    intro_text_template = RESPONSE_MESSAGES.get(intro_text_key, "Chào mừng đến Chia sẻ nhận Code.")
    try:
        intro_text = intro_text_template.format(**format_params)
    except KeyError as e:
        logger.error(f"Lỗi KeyError khi format intro_text cho share_code: {e}. Params: {format_params}, Key: {intro_text_key}")
        intro_text = "Lỗi hiển thị thông tin chia sẻ. Vui lòng thử lại."


    keyboard = [
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("request_code_reward_button", "💰 Nhận Code thưởng"), callback_data='share_request_reward')],
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("get_my_share_link_button", "🔗 Link chia sẻ của tôi"), callback_data='share_get_link')],
        [
            InlineKeyboardButton(RESPONSE_MESSAGES.get("cskh_button_text","💬 CSKH trực tuyến"), url=CSKH_LINK), 
            InlineKeyboardButton(RESPONSE_MESSAGES.get("back_to_menu_button","⬅️ Quay lại Menu"), callback_data='back_to_menu')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=chat_id, 
        text=intro_text, 
        reply_markup=reply_markup, 
        parse_mode='Markdown'
    )
    return SHOW_SHARE_MENU

async def get_my_share_link_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    # Không xóa nút ở đây vì tin nhắn link sẽ là tin nhắn mới riêng biệt

    user_id = query.from_user.id 
    chat_id = query.message.chat_id

    global BOT_USERNAME
    if BOT_USERNAME is None: 
        try:
            bot_info = await context.bot.get_me()
            BOT_USERNAME = bot_info.username
            if BOT_USERNAME is None: 
                 await context.bot.send_message(chat_id=chat_id, text=RESPONSE_MESSAGES.get("error_getting_bot_info", "Lỗi: Không thể lấy thông tin bot. Vui lòng thử lại sau."))
                 return SHOW_SHARE_MENU 
            logger.info(f"Tên bot đã được đặt lại trong get_my_share_link_callback: {BOT_USERNAME}")
        except Exception as e:
            logger.error(f"Không thể lấy tên bot trong get_my_share_link_callback: {e}")
            await context.bot.send_message(chat_id=chat_id, text=RESPONSE_MESSAGES.get("error_getting_bot_info", "Lỗi: Không thể lấy thông tin bot. Vui lòng thử lại sau."))
            return SHOW_SHARE_MENU

    user_s_data = get_user_data_from_json(user_id)
    referral_code = user_s_data.get("referral_code")

    if not referral_code:
        await context.bot.send_message(chat_id=chat_id, text=RESPONSE_MESSAGES.get("error_no_referral_code", "Lỗi: Không tìm thấy mã giới thiệu. Thử lại /start."))
        return SHOW_SHARE_MENU

    share_link = f"https://t.me/{BOT_USERNAME}?start=ref_{referral_code}" 
    share_link_message_text = RESPONSE_MESSAGES.get("my_share_link_message", "Link của bạn: {share_link}").format(share_link=share_link)
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=share_link_message_text,
        parse_mode='Markdown' 
    )
    return SHOW_SHARE_MENU


async def request_code_reward_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await _remove_buttons_from_previous_message(query) # Xóa nút trên menu share code

    user_id = update.effective_user.id 
    user_data_local = get_user_data_from_json(user_id) 
    chat_id = query.message.chat_id

    current_share_count = user_data_local.get("share_count", 0)
    claimed_milestones_local = user_data_local.get("claimed_share_milestones", {})
    pending_claim_local = user_data_local.get("pending_share_milestone_claim")
    
    claimable_milestone = None
    for milestone_val in sorted(SHARE_MILESTONES):
        if current_share_count >= milestone_val and str(milestone_val) not in claimed_milestones_local:
            if not (pending_claim_local and pending_claim_local.get("milestone") == milestone_val):
                claimable_milestone = milestone_val
                break 

    message_text = ""
    keyboard_rows_for_new_message = [] # Sẽ build keyboard cho tin nhắn mới

    if claimable_milestone:
        context.user_data['milestone_to_claim_share'] = claimable_milestone
        ask_username_text_template = RESPONSE_MESSAGES.get("ask_username_for_share_reward", "Chúc mừng! Bạn đã đạt mốc **{milestone}** lượt chia sẻ. Vui lòng cung cấp tên đăng nhập game của bạn để nhận thưởng:")
        message_text = ask_username_text_template.format(milestone=claimable_milestone)
        keyboard_rows_for_new_message.append([InlineKeyboardButton(RESPONSE_MESSAGES.get("cancel_and_back_share_menu_button", "⬅️ Hủy & Quay lại Menu Chia Sẻ"), callback_data='share_code_entry_point_cancel')])
        
        reply_markup_new = InlineKeyboardMarkup(keyboard_rows_for_new_message)
        await context.bot.send_message(
            chat_id=chat_id, 
            text=message_text, 
            reply_markup=reply_markup_new, 
            parse_mode='Markdown'
        )
        return AWAIT_USERNAME_FOR_SHARE_REWARD 
    
    # Nếu không có mốc nào có thể nhận ngay
    elif pending_claim_local: 
        pending_milestone = pending_claim_local.get("milestone")
        message_text = RESPONSE_MESSAGES.get("pending_claim_exists", "Yêu cầu trước đang xử lý cho mốc {milestone}...").format(milestone=pending_milestone)
    else: 
        next_milestone_to_achieve = None
        needed_more_val = 0
        for m in sorted(SHARE_MILESTONES):
            if str(m) not in claimed_milestones_local: 
                if current_share_count < m:
                    next_milestone_to_achieve = m
                    needed_more_val = m - current_share_count
                    break
        
        if next_milestone_to_achieve:
            no_new_milestone_template = RESPONSE_MESSAGES.get("no_new_milestone_message", "Bạn có **{share_count}** lượt chia sẻ. Cần thêm **{needed_more}** lượt nữa để đạt mốc **{next_milestone}**. Cố gắng lên nhé!")
            message_text = no_new_milestone_template.format(
                share_count=current_share_count, 
                needed_more=needed_more_val, 
                next_milestone=next_milestone_to_achieve
            )
        else: 
            message_text = RESPONSE_MESSAGES.get("all_milestones_claimed_message", "Bạn đã nhận thưởng cho tất cả các mốc chia sẻ hiện có! Cảm ơn sự đóng góp tuyệt vời của bạn.")

    # Keyboard cho các trường hợp không chuyển state (gửi lại menu share)
    keyboard_rows_for_new_message.append([InlineKeyboardButton(RESPONSE_MESSAGES.get("get_my_share_link_button", "🔗 Link chia sẻ của tôi"), callback_data='share_get_link')])
    # Thêm lại nút "Nhận code thưởng" để user có thể bấm lại nếu muốn (ví dụ sau khi xem pending)
    keyboard_rows_for_new_message.append([InlineKeyboardButton(RESPONSE_MESSAGES.get("request_code_reward_button", "💰 Nhận Code thưởng"), callback_data='share_request_reward')])
    keyboard_rows_for_new_message.append([
        InlineKeyboardButton(RESPONSE_MESSAGES.get("cskh_button_text","💬 CSKH trực tuyến"), url=CSKH_LINK),
        InlineKeyboardButton(RESPONSE_MESSAGES.get("back_to_menu_button","⬅️ Quay lại Menu"), callback_data='back_to_menu')
    ])
    reply_markup_new = InlineKeyboardMarkup(keyboard_rows_for_new_message)
    await context.bot.send_message(
        chat_id=chat_id, 
        text=message_text, 
        reply_markup=reply_markup_new, 
        parse_mode='Markdown'
    )
    return SHOW_SHARE_MENU


async def share_code_entry_point_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    if query: # Hàm này chỉ nên được gọi từ callback
        logger.info(f"share_code_entry_point_cancel called by user {update.effective_user.id}")
        await query.answer()
        await _remove_buttons_from_previous_message(query) # Xóa nút trên tin nhắn "Nhập username..."

        if 'milestone_to_claim_share' in context.user_data:
            del context.user_data['milestone_to_claim_share'] 
    else:
        logger.warning("share_code_entry_point_cancel called without a callback query.")
        # Nếu không có query, thì không thể xóa nút, chỉ có thể quay về menu share
        # bằng cách gửi tin nhắn mới (share_code_entry_point sẽ làm điều này)

    # Gọi lại share_code_entry_point để hiển thị menu chia sẻ mới
    return await share_code_entry_point(update, context) # share_code_entry_point sẽ gửi tin nhắn mới


# ==========================================================================

async def receive_username_kl001(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    customer_username = update.message.text.strip() # Plain text
    user_id = update.effective_user.id
    user_first_name = update.effective_user.first_name # Plain text
    promo_code = "KL001"
    admin_response_keyboard_rows = [
        [
            InlineKeyboardButton("Sai ID", callback_data=f"admin_response:{user_id}:sai_id:{promo_code}"),
            InlineKeyboardButton("✅ Thành Công", callback_data=f"admin_response:{user_id}:thanh_cong:{promo_code}")
        ],
         [
            InlineKeyboardButton("Chưa LK NH", callback_data=f"admin_response:{user_id}:chua_lien_ket_ngan_hang:{promo_code}"),
            InlineKeyboardButton("Sai TT (CSKH)", callback_data=f"admin_response:{user_id}:sai_thong_tin_lien_he_cskh:{promo_code}")
        ],
        [
            InlineKeyboardButton("Đã nhận KM001", callback_data=f"admin_response:{user_id}:kl001_da_nhan:{promo_code}"),
            InlineKeyboardButton("Trùng IP", callback_data=f"admin_response:{user_id}:trung_ip:{promo_code}")
        ],
        [
            InlineKeyboardButton("Chưa nạp", callback_data=f"admin_response:{user_id}:chua_nap:{promo_code}"),
            InlineKeyboardButton("Nạp không đủ", callback_data=f"admin_response:{user_id}:khong_du:{promo_code}")
        ],
        [
            InlineKeyboardButton("Đã nạp nhiều lần", callback_data=f"admin_response:{user_id}:da_nap_nhieu:{promo_code}"),
            InlineKeyboardButton("Đã cược", callback_data=f"admin_response:{user_id}:da_cuoc:{promo_code}")
        ]
    ]
    admin_response_markup = InlineKeyboardMarkup(admin_response_keyboard_rows)
    admin_message_text_to_group = f"Yêu cầu {promo_code}:\nKhách: {user_first_name} (TG ID: {user_id})\nTên đăng nhập: {customer_username}"
    try:
        await context.bot.send_message(
            chat_id=ID_GROUP_PROMO,
            text=admin_message_text_to_group, 
            reply_markup=admin_response_markup
        )
    except Exception as e:
        logger.error(f"Lỗi khi gửi tin nhắn {promo_code} đến nhóm khuyến mãi: {e}")
        await update.message.reply_text(RESPONSE_MESSAGES.get("error_sending_request", "Đã xảy ra lỗi khi xử lý yêu cầu của bạn. Vui lòng thử lại sau."))
        return ConversationHandler.END

    customer_buttons = [[InlineKeyboardButton(RESPONSE_MESSAGES.get("cskh_button_text","💬 CSKH trực tuyến"), url=CSKH_LINK)], [InlineKeyboardButton(RESPONSE_MESSAGES.get("back_to_menu_button","⬅️ Quay lại Menu"), callback_data='back_to_menu')]]
    customer_markup = InlineKeyboardMarkup(customer_buttons)
    # Đây là reply_text, gửi tin nhắn mới. Nút 'back_to_menu' sẽ được xử lý bởi start() đã sửa.
    await update.message.reply_text(RESPONSE_MESSAGES.get("yeu_cau_dang_xu_ly", "Yêu cầu đang xử lý."), reply_markup=customer_markup)
    return ConversationHandler.END

async def receive_username_kl007(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    customer_username = update.message.text.strip() 
    user_id = update.effective_user.id
    user_first_name = update.effective_user.first_name 
    promo_code = "KL007"
    admin_message_text_to_group = (
        f"{promo_code} Request:\n"
        f"User: {user_first_name} (TG ID: {user_id})\n"
        f"Game User: {customer_username}\n"
    )
    admin_buttons = [
        [InlineKeyboardButton("Sai ID", callback_data=f"admin_response:{user_id}:sai_id:{promo_code}")],
        [InlineKeyboardButton("Không có vé cược", callback_data=f"admin_response:{user_id}:khong_co_ve_kl007:{promo_code}")],
        [InlineKeyboardButton("Đã nhận KM007 hôm nay", callback_data=f"admin_response:{user_id}:kl007_da_nhan:{promo_code}")],
        [InlineKeyboardButton("Cộng điểm (Reply số điểm)", callback_data=f"admin_response:{user_id}:kl007_reply_points_prompt:{promo_code}")]
    ]
    admin_reply_markup = InlineKeyboardMarkup(admin_buttons)
    try:
        await context.bot.send_message(
            chat_id=ID_GROUP_PROMO,
            text=admin_message_text_to_group, 
            reply_markup=admin_reply_markup
        )
    except Exception as e:
        logger.error(f"Lỗi khi gửi yêu cầu {promo_code} đến nhóm: {e}")
        await update.message.reply_text(RESPONSE_MESSAGES.get("error_sending_request", "Đã có lỗi xảy ra khi gửi yêu cầu của bạn. Vui lòng thử lại sau."))
        return ConversationHandler.END
    customer_reply_buttons = [
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("cskh_button_text","💬 CSKH trực tuyến"), url=CSKH_LINK)],
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("back_to_menu_button","⬅️ Quay lại Menu"), callback_data='back_to_menu')]
    ]
    customer_reply_markup = InlineKeyboardMarkup(customer_reply_buttons)
    await update.message.reply_text(RESPONSE_MESSAGES.get("yeu_cau_dang_xu_ly", "Yêu cầu đang xử lý."), reply_markup=customer_reply_markup)
    return ConversationHandler.END

async def receive_usernames_kl006(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_message_text = update.message.text 
    user_id = update.effective_user.id
    user_first_name = update.effective_user.first_name 
    promo_code = "KL006"
    group_size = context.user_data.get('kl006_group_size')
    if not group_size:
        await update.message.reply_text("Đã có lỗi, không tìm thấy quy mô nhóm. Vui lòng thử lại từ đầu bằng cách chọn lại khuyến mãi KL006.")
        menu_button = [[InlineKeyboardButton(RESPONSE_MESSAGES.get("back_to_menu_button","⬅️ Quay lại Menu"), callback_data='back_to_menu')]]
        await update.message.reply_text("Chọn một tùy chọn:", reply_markup=InlineKeyboardMarkup(menu_button))
        return ConversationHandler.END

    usernames = [u.strip() for u in re.split(r'[,\n\s]+', user_message_text) if u.strip()] 
    if len(usernames) != group_size:
        # Tin nhắn báo lỗi này sẽ có nút "Nhập lại..." và "Quay lại Menu KM"
        # Nút "Nhập lại..." gọi kl006_reenter_usernames_after_agree_callback (đã sửa để gửi mới)
        # Nút "Quay lại Menu KM" gọi khuyen_mai_callback (đã sửa để gửi mới)
        customer_buttons = [
             [InlineKeyboardButton(f"✍️ Nhập lại {group_size} tên", callback_data=f'kl006_reenter_usernames_after_agree:{group_size}')],
            [InlineKeyboardButton(RESPONSE_MESSAGES.get("back_to_promo_menu_button_text", "⬅️ Quay lại Menu KM"), callback_data='khuyen_mai')],
            [InlineKeyboardButton(RESPONSE_MESSAGES.get("cskh_button_text","💬 CSKH trực tuyến"), url=CSKH_LINK)]
        ]
        customer_markup = InlineKeyboardMarkup(customer_buttons)
        invalid_count_text = RESPONSE_MESSAGES.get("kl006_invalid_username_count", "Số lượng tên ({submitted_count}) không khớp ({expected_count}).")
        await update.message.reply_text(
            invalid_count_text.format(submitted_count=len(usernames), expected_count=group_size),
            reply_markup=customer_markup
        )
        return RECEIVE_USERNAMES_KL006

    usernames_formatted = "\n".join([f"- {name}" for name in usernames]) 
    admin_message_text_to_group = (
        f"Yêu cầu {promo_code} - Nhóm {group_size} thành viên:\n"
        f"Khách: {user_first_name} (TG ID: {user_id})\n"
        f"Tên đăng nhập cung cấp:\n{usernames_formatted}"
    )
    admin_buttons = []
    for idx, uname in enumerate(usernames):
        admin_buttons.append([
            InlineKeyboardButton(f"Sai ID: {uname}", callback_data=f"admin_kl006:{user_id}:{group_size}:{idx}:sai_id_user"),
            InlineKeyboardButton(f"Cược <3k: {uname}", callback_data=f"admin_kl006:{user_id}:{group_size}:{idx}:cuoc_khong_du_user")
        ])
    admin_buttons.append([InlineKeyboardButton("Tổng cược nhóm <20k", callback_data=f"admin_kl006:{user_id}:{group_size}:GROUP:khong_du_tong_diem")])
    admin_buttons.append([InlineKeyboardButton("Nhóm chưa ĐK KM006", callback_data=f"admin_kl006:{user_id}:{group_size}:GROUP:nhom_chua_dk")])
    admin_buttons.append([InlineKeyboardButton("Nhóm đã nhận KM006 h.nay", callback_data=f"admin_kl006:{user_id}:{group_size}:GROUP:da_nhan")])
    admin_buttons.append([InlineKeyboardButton("✅ Thành Công (KL006)", callback_data=f"admin_kl006:{user_id}:{group_size}:GROUP:thanh_cong")])
    admin_reply_markup = InlineKeyboardMarkup(admin_buttons)
    try:
        await context.bot.send_message(
            chat_id=ID_GROUP_PROMO,
            text=admin_message_text_to_group, 
            reply_markup=admin_reply_markup
        )
    except Exception as e:
        logger.error(f"Lỗi khi gửi yêu cầu {promo_code} đến nhóm: {e}")
        await update.message.reply_text(RESPONSE_MESSAGES.get("error_sending_request", "Đã xảy ra lỗi khi xử lý yêu cầu của bạn. Vui lòng thử lại sau."))
        return ConversationHandler.END
    customer_buttons = [[InlineKeyboardButton(RESPONSE_MESSAGES.get("cskh_button_text","💬 CSKH trực tuyến"), url=CSKH_LINK)], [InlineKeyboardButton(RESPONSE_MESSAGES.get("back_to_menu_button","⬅️ Quay lại Menu"), callback_data='back_to_menu')]]
    customer_markup = InlineKeyboardMarkup(customer_buttons)
    await update.message.reply_text(RESPONSE_MESSAGES.get("yeu_cau_dang_xu_ly", "Yêu cầu đang xử lý."), reply_markup=customer_markup)
    if 'kl006_group_size' in context.user_data: del context.user_data['kl006_group_size']
    return ConversationHandler.END

async def receive_username_app_promo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    customer_username = update.message.text.strip() 
    context.user_data['app_promo_username'] = customer_username
    # Tin nhắn này ("Có ảnh xác nhận không?") là reply_text, gửi mới.
    # Nút bấm trên đó ("Có ảnh"/"Không có ảnh") sẽ gọi handle_image_confirm_app_promo
    # handle_image_confirm_app_promo đã được sửa để xóa nút và gửi mới.
    keyboard = [
        [
            InlineKeyboardButton("✅ Có ảnh", callback_data='app_promo_has_image:yes'),
            InlineKeyboardButton("❌ Không có ảnh", callback_data='app_promo_has_image:no')
        ],
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("back_to_promo_menu_button_text", "⬅️ Quay lại Menu KM"), callback_data='khuyen_mai')], # Gọi khuyen_mai_callback (đã sửa)
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("cskh_button_text","💬 CSKH trực tuyến"), url=CSKH_LINK)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(RESPONSE_MESSAGES.get("app_promo_ask_image", "Có ảnh xác nhận không?"), reply_markup=reply_markup)
    return AWAIT_IMAGE_CONFIRM_APP_PROMO

async def receive_image_app_promo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message
    user_id = update.effective_user.id
    user_first_name = update.effective_user.first_name 
    customer_username = context.user_data.get('app_promo_username', 'N/A') 
    promo_code = "APP_PROMO"
    if not message.photo:
        # Tin nhắn này cũng là reply_text (mới)
        await message.reply_text("Vui lòng gửi một hình ảnh. Nếu không có hình ảnh, bạn có thể quay lại và chọn 'Không có ảnh'.")
        return RECEIVE_IMAGE_APP_PROMO

    photo_file_id = message.photo[-1].file_id
    admin_caption_text = (
        f"Yêu cầu {promo_code} (Có ảnh):\n"
        f"Khách: {user_first_name} (TG ID: {user_id})\n"
        f"Tên đăng nhập: {customer_username}"
    )
    admin_buttons = [
        [
            InlineKeyboardButton("Sai ID", callback_data=f"admin_response:{user_id}:sai_id:{promo_code}"),
            InlineKeyboardButton("✅ Thành Công", callback_data=f"admin_response:{user_id}:app_promo_thanh_cong:{promo_code}")
        ],
        [
            InlineKeyboardButton("Đã nhận KM Tải App", callback_data=f"admin_response:{user_id}:app_promo_da_nhan:{promo_code}"),
            InlineKeyboardButton("Y/c hình ảnh", callback_data=f"admin_response:{user_id}:app_promo_yeu_cau_hinh_anh:{promo_code}")
        ],
        [
            InlineKeyboardButton("Trùng IP (App)", callback_data=f"admin_response:{user_id}:app_promo_trung_ip:{promo_code}"),
            InlineKeyboardButton("Đã nạp/rút (App)", callback_data=f"admin_response:{user_id}:app_promo_da_nap_rut_nhieu:{promo_code}")
        ],
        [
            InlineKeyboardButton("Chưa LK NH", callback_data=f"admin_response:{user_id}:chua_lien_ket_ngan_hang:{promo_code}"),
            InlineKeyboardButton("Sai TT (CSKH)", callback_data=f"admin_response:{user_id}:sai_thong_tin_lien_he_cskh:{promo_code}")
        ]
    ]
    admin_reply_markup = InlineKeyboardMarkup(admin_buttons)
    try:
        await context.bot.send_photo(
            chat_id=ID_GROUP_PROMO,
            photo=photo_file_id,
            caption=admin_caption_text, 
            reply_markup=admin_reply_markup
        )
        customer_buttons = [[InlineKeyboardButton(RESPONSE_MESSAGES.get("cskh_button_text","💬 CSKH trực tuyến"), url=CSKH_LINK)], [InlineKeyboardButton(RESPONSE_MESSAGES.get("back_to_menu_button","⬅️ Quay lại Menu"), callback_data='back_to_menu')]]
        customer_markup = InlineKeyboardMarkup(customer_buttons)
        await update.message.reply_text(RESPONSE_MESSAGES.get("app_promo_image_sent_to_admin", "Đã gửi ảnh."), reply_markup=customer_markup)
    except Exception as e:
        logger.error(f"Lỗi khi gửi yêu cầu {promo_code} (có ảnh) đến nhóm: {e}")
        await update.message.reply_text(RESPONSE_MESSAGES.get("error_sending_request", "Đã xảy ra lỗi khi xử lý yêu cầu của bạn. Vui lòng thử lại sau."))
    if 'app_promo_username' in context.user_data: del context.user_data['app_promo_username']
    return ConversationHandler.END

# Hàm handle_admin_response và các hàm handle_admin_kl00X_response
# gửi tin nhắn mới cho khách hàng, nên các nút trên đó (ví dụ back_to_menu)
# sẽ được xử lý bởi `start()` đã sửa (xóa nút cũ, gửi menu welcome mới).
# Không cần thay đổi lớn ở đây. Chỉ cần đảm bảo `parse_mode='Markdown'` được dùng đúng chỗ.

async def handle_admin_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    original_bot_message_text = query.message.text if query.message.text else query.message.caption
    if not original_bot_message_text:
        logger.error(f"Lỗi: Không thể lấy nội dung tin nhắn admin gốc. Callback data: {query.data}")
        # Không gửi gì cho user, chỉ edit tin nhắn admin
        try:
            await query.edit_message_text("Lỗi: Không thể xử lý yêu cầu do thiếu nội dung tin nhắn gốc của admin.", reply_markup=None)
        except Exception as e:
            logger.error(f"Error editing admin message in handle_admin_response (no original text): {e}")
        return

    customer_username = "N/A_PARSE_ERR"
    username_match_login = re.search(r"Tên đăng nhập: (\S+)", original_bot_message_text, re.IGNORECASE)
    if username_match_login:
        customer_username = username_match_login.group(1)
    else:
        username_match_game = re.search(r"Game User: (\S+)", original_bot_message_text, re.IGNORECASE)
        if username_match_game:
            customer_username = username_match_game.group(1)

    try:
        _prefix, user_id_str, response_key, promo_code = query.data.split(':', 3)
        if response_key == "kl007_reply_points_prompt":
            # Edit tin nhắn admin để yêu cầu reply (đã có escape markdown)
            escaped_original_text = escape_markdown(original_bot_message_text, version=1)
            escaped_customer_username = escape_markdown(customer_username, version=1)
            await query.edit_message_text(
                f"{escaped_original_text}\n---\nℹ️ Admin, vui lòng reply (trả lời) trực tiếp vào tin nhắn này với số điểm cần cộng cho user {escaped_customer_username} (TG ID: {user_id_str}). Ví dụ: +100 hoặc 100.", 
                reply_markup=None,
                parse_mode='Markdown' # Vì text đã được escape
            )
            return
    except ValueError:
        logger.error(f"Lỗi parsing callback_data (chung): {query.data}")
        await query.edit_message_text(f"Lỗi callback data: {query.data}. Vui lòng báo admin.", reply_markup=None)
        return

    target_user_id = int(user_id_str)
    admin_user = query.from_user
    admin_mention = f"@{admin_user.username}" if admin_user.username else admin_user.first_name
    customer_response_markup = None
    response_message_to_customer = None
    
    # Tin nhắn admin đã được escape trước đó
    escaped_original_text_admin = escape_markdown(original_bot_message_text, version=1)
    escaped_admin_mention_admin = escape_markdown(admin_mention, version=1)
    escaped_customer_username_admin = escape_markdown(customer_username, version=1)
    escaped_response_reason_admin = escape_markdown(response_key.replace('_', ' ').title(), version=1)

    processed_text_for_admin = (f"{escaped_original_text_admin}\n---\n"
                                f"✅ Xử lý bởi {escaped_admin_mention_admin} cho User: {escaped_customer_username_admin} (ID: {target_user_id}), Lý do: {escaped_response_reason_admin}")


    if response_key == "app_promo_yeu_cau_hinh_anh":
        response_message_to_customer = RESPONSE_MESSAGES.get("app_promo_yeu_cau_hinh_anh")
        # Nút "Đăng ký lại KM Tải App" sẽ gọi promo_app_experience_callback (đã sửa để gửi mới)
        customer_resend_image_button_rows = [
            [InlineKeyboardButton("🎁 Đăng ký lại KM Tải App (kèm ảnh)", callback_data='promo_app_experience')],
            [InlineKeyboardButton(RESPONSE_MESSAGES.get("cskh_button_text","💬 CSKH trực tuyến"), url=CSKH_LINK)],
            [InlineKeyboardButton(RESPONSE_MESSAGES.get("back_to_menu_button","⬅️ Quay lại Menu"), callback_data='back_to_menu')]
        ]
        customer_response_markup = InlineKeyboardMarkup(customer_resend_image_button_rows)
    else:
        response_message_template = RESPONSE_MESSAGES.get(response_key)
        if not response_message_template:
            response_message_to_customer = "Đã xảy ra lỗi không xác định từ phản hồi của quản trị viên. Vui lòng liên hệ CSKH."
            logger.warning(f"Không tìm thấy response_key: {response_key} cho promo {promo_code}")
        else:
            try:
                current_format_params_for_customer = {}
                # Các giá trị này cần được escape nếu tin nhắn tới user là Markdown và chúng chứa ký tự đặc biệt
                if "{customer_username}" in response_message_template:
                    current_format_params_for_customer["customer_username"] = escape_markdown(customer_username, version=1)
                if "{promo_code}" in response_message_template: # promo_code thường an toàn (KL001, etc)
                    current_format_params_for_customer["promo_code"] = promo_code
                if "{YESTERDAY_DMY}" in response_message_template: # YESTERDAY_DMY là ngày, an toàn
                    current_format_params_for_customer["YESTERDAY_DMY"] = YESTERDAY_DMY
                response_message_to_customer = response_message_template.format(**current_format_params_for_customer)
            except KeyError as e:
                logger.error(f"Lỗi KeyError khi format tin nhắn cho khách ({response_key}): {e}. Dùng template gốc.")
                response_message_to_customer = response_message_template 

        customer_response_keyboard_rows = []
        re_entry_callback_data = None
        re_entry_text = None

        # Nút "Đăng ký lại KM" sẽ gọi các hàm promo_X_callback (đã được sửa để gửi mới)
        if promo_code == "KL001" and response_key in ["sai_id", "chua_lien_ket_ngan_hang", "sai_thong_tin_lien_he_cskh", "kl001_da_nhan", "trung_ip", "chua_nap", "khong_du", "da_nap_nhieu", "da_cuoc"]:
            re_entry_text = f"✍️ Đăng ký lại KM {promo_code}"
            re_entry_callback_data = f"promo_{promo_code}" # Sẽ gọi promo_KL001_callback
        elif promo_code == "KL007" and response_key in ["sai_id", "khong_co_ve_kl007", "kl007_da_nhan"]:
            re_entry_text = f"✍️ Đăng ký lại KM {promo_code}"
            re_entry_callback_data = f"promo_{promo_code}" # Sẽ gọi promo_KL007_callback
        elif promo_code == "APP_PROMO" and response_key in ["sai_id", "app_promo_da_nhan", "app_promo_trung_ip", "app_promo_da_nap_rut_nhieu", "chua_lien_ket_ngan_hang", "sai_thong_tin_lien_he_cskh"]:
            re_entry_text = "✍️ Đăng ký lại KM Tải App"
            re_entry_callback_data = 'promo_app_experience' # Sẽ gọi promo_app_experience_callback

        if re_entry_text and re_entry_callback_data:
            customer_response_keyboard_rows.append(
                [InlineKeyboardButton(re_entry_text, callback_data=re_entry_callback_data)]
            )
        common_buttons_row = [
            InlineKeyboardButton(RESPONSE_MESSAGES.get("cskh_button_text","💬 CSKH trực tuyến"), url=CSKH_LINK),
            InlineKeyboardButton(RESPONSE_MESSAGES.get("back_to_menu_button","⬅️ Quay lại Menu"), callback_data='back_to_menu') # Gọi back_to_menu_handler (đã sửa)
        ]
        customer_response_keyboard_rows.append(common_buttons_row)
        if customer_response_keyboard_rows:
            customer_response_markup = InlineKeyboardMarkup(customer_response_keyboard_rows)

    try:
        if response_message_to_customer:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=response_message_to_customer,
                reply_markup=customer_response_markup,
                parse_mode='Markdown' # Vì response_message_to_customer có thể chứa Markdown
            )
        
        # Edit tin nhắn admin group (đã escape)
        if query.message.text is not None:
            await query.edit_message_text(text=processed_text_for_admin, reply_markup=None, parse_mode='Markdown')
        elif query.message.caption is not None: 
            await query.edit_message_caption(caption=processed_text_for_admin, reply_markup=None, parse_mode='Markdown')
        else: # Nếu không có text và caption, chỉ xóa nút
             await query.edit_message_reply_markup(reply_markup=None)

    except telegram.error.BadRequest as e_edit:
        if any(err_msg in str(e_edit).lower() for err_msg in ["message to edit not found", "message is not modified", "there is no text in the message to edit", "message can't be edited"]):
            logger.warning(f"Không thể sửa tin nhắn admin (chung - lỗi đã biết): {e_edit}")
            try: await query.edit_message_reply_markup(reply_markup=None) 
            except Exception as e_markup: logger.warning(f"Cũng không thể xóa markup (chung): {e_markup}")
        else: 
            logger.error(f"Lỗi lạ khi sửa tin nhắn admin (chung): {e_edit} - Data: {query.data} - Processed Text: '{processed_text_for_admin}'")
    except Exception as e:
        logger.error(f"Lỗi khi gửi phản hồi (chung) hoặc xử lý tin nhắn admin: {e}")

async def handle_admin_kl007_point_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message 
    replied_to_message = message.reply_to_message 
    if not (replied_to_message and replied_to_message.from_user.is_bot and replied_to_message.from_user.id == context.bot.id and message.chat_id == ID_GROUP_PROMO):
        return

    original_bot_text = replied_to_message.text 
    if not original_bot_text or "KL007 Request:" not in original_bot_text:
        return 

    admin_reply_text = message.text.strip() 
    admin_user = message.from_user
    admin_mention = f"@{admin_user.username}" if admin_user.username else admin_user.first_name 

    tg_id_match = re.search(r"TG ID: (\d+)", original_bot_text)
    game_user_match = re.search(r"Game User: (\S+)", original_bot_text, re.IGNORECASE)

    if not (tg_id_match and game_user_match):
        logger.warning("Không thể trích xuất TG ID hoặc Game User từ tin nhắn KL007 gốc khi admin reply điểm.")
        await message.reply_text("Lỗi: Không tìm thấy thông tin user trong tin nhắn gốc để cộng điểm KL007.")
        return

    target_user_id = int(tg_id_match.group(1))
    customer_username = game_user_match.group(1) 
    points_to_add = None

    if admin_reply_text.startswith('+') and admin_reply_text[1:].isdigit():
        points_to_add = int(admin_reply_text[1:])
    elif admin_reply_text.isdigit():
        points_to_add = int(admin_reply_text)

    if points_to_add is not None and points_to_add > 0 :
        success_message_template = RESPONSE_MESSAGES.get("thanh_cong_kl007_points", "...")
        escaped_customer_username_for_customer = escape_markdown(customer_username, version=1)
        message_to_customer = success_message_template.format(points=points_to_add, customer_username=escaped_customer_username_for_customer)

        customer_buttons = [[InlineKeyboardButton(RESPONSE_MESSAGES.get("cskh_button_text","💬 CSKH trực tuyến"), url=CSKH_LINK)], [InlineKeyboardButton(RESPONSE_MESSAGES.get("back_to_menu_button","⬅️ Quay lại Menu"), callback_data='back_to_menu')]]
        customer_markup = InlineKeyboardMarkup(customer_buttons)
        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=message_to_customer,
                reply_markup=customer_markup
                # parse_mode='Markdown' # Thêm nếu template có Markdown, hiện tại không cần vì đã escape
            )

            escaped_original_bot_text = escape_markdown(original_bot_text, version=1)
            escaped_admin_mention_for_admin = escape_markdown(admin_mention, version=1)
            escaped_customer_username_for_admin = escape_markdown(customer_username, version=1)

            new_admin_text_processed = (
                f"{escaped_original_bot_text}\n--------------------\n"
                f"✅ ĐÃ XỬ LÝ bởi {escaped_admin_mention_for_admin}: Cộng {points_to_add} điểm cho {escaped_customer_username_for_admin}."
            )
            await context.bot.edit_message_text(
                text=new_admin_text_processed,
                chat_id=ID_GROUP_PROMO,
                message_id=replied_to_message.message_id,
                reply_markup=None,
                parse_mode='Markdown' 
            )
            await message.reply_text(f"Đã thông báo cộng {points_to_add} điểm KL007 cho user {customer_username} (TG ID: {target_user_id}).")
        except Exception as e:
            logger.error(f"Lỗi khi gửi tin nhắn cộng điểm KL007 cho khách hoặc sửa tin nhắn admin: {e}")
            await message.reply_text(f"Lỗi khi xử lý cộng điểm KL007 cho {customer_username}: {e}")
    else: 
        if not admin_reply_text.startswith("admin_response:"): 
            logger.info(f"Admin {admin_mention} đã reply bằng văn bản không hợp lệ ('{admin_reply_text}') cho yêu cầu KL007 của {customer_username}. Bot không xử lý.")

async def handle_admin_kl006_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    original_bot_message_text = query.message.text if query.message.text else query.message.caption 
    if not original_bot_message_text:
        logger.error(f"Lỗi: Không thể lấy nội dung tin nhắn admin gốc cho KL006. Callback data: {query.data}")
        await query.edit_message_text("Lỗi: Không thể xử lý yêu cầu KL006 do thiếu nội dung tin nhắn gốc.", reply_markup=None)
        return

    parsed_usernames_from_message = []
    usernames_block_match = re.search(r"Tên đăng nhập cung cấp:\s*\n((?:- \S+\s*(?:\n|$))+)", original_bot_message_text, re.MULTILINE | re.IGNORECASE)
    if usernames_block_match:
        parsed_usernames_from_message = [name.strip() for name in re.findall(r"-\s*(\S+)", usernames_block_match.group(1))] 

    try:
        _prefix, user_id_str, group_size_str, affected_item_specifier, response_key_suffix = query.data.split(':', 4)
        response_key = f"kl006_{response_key_suffix}"
    except ValueError:
        logger.error(f"Lỗi parsing callback_data (KL006): {query.data}")
        await query.edit_message_text(f"Lỗi callback data KL006: {query.data}. Vui lòng báo admin.", reply_markup=None)
        return

    target_user_id = int(user_id_str)
    group_size_from_callback = int(group_size_str)
    admin_user = query.from_user
    admin_mention = f"@{admin_user.username}" if admin_user.username else admin_user.first_name 
    affected_username_for_message = "một thành viên trong nhóm" 
    action_taken_detail = response_key_suffix.replace('_', ' ').title() 

    if affected_item_specifier != "GROUP":
        try:
            user_idx = int(affected_item_specifier)
            if 0 <= user_idx < len(parsed_usernames_from_message):
                affected_username_for_message = parsed_usernames_from_message[user_idx] 
                action_taken_detail += f" (User: {affected_username_for_message})"
            else:
                action_taken_detail += f" (User Index {user_idx} - Lỗi không tìm thấy trong list)"
                logger.warning(f"KL006 Admin Response: User index {user_idx} out of bounds for parsed_usernames ({len(parsed_usernames_from_message)}): {parsed_usernames_from_message}")
        except ValueError:
            action_taken_detail += f" (Item: {affected_item_specifier} - Lỗi ID item)"
            logger.warning(f"KL006 Admin Response: Invalid affected_item_specifier {affected_item_specifier}")

    escaped_original_text_kl006 = escape_markdown(original_bot_message_text, version=1)
    escaped_admin_mention_kl006 = escape_markdown(admin_mention, version=1)
    escaped_action_taken_detail_for_admin = escape_markdown(action_taken_detail, version=1)
    processed_text_for_admin_kl006 = f"{escaped_original_text_kl006}\n---\n✅ Xử lý bởi {escaped_admin_mention_kl006}: {escaped_action_taken_detail_for_admin}"

    response_message_template = RESPONSE_MESSAGES.get(response_key)
    response_message_to_customer = f"Phản hồi cho yêu cầu KL006 của bạn: {action_taken_detail} (lỗi template: {response_key})" 

    if response_message_template:
        format_params_for_customer_kl006 = {}
        if "{date}" in response_message_template: 
             format_params_for_customer_kl006["date"] = YESTERDAY_DMY 
        if "{username}" in response_message_template :
            format_params_for_customer_kl006["username"] = escape_markdown(affected_username_for_message, version=1)
        if "{group_size}" in response_message_template:
            format_params_for_customer_kl006["group_size"] = group_size_from_callback 
        try:
            response_message_to_customer = response_message_template.format(**format_params_for_customer_kl006)
        except KeyError as e:
            logger.error(f"Lỗi format KL006, key: {e}, template: '{response_message_template}', params: {format_params_for_customer_kl006}")
            if "{username}" in format_params_for_customer_kl006: 
                format_params_for_customer_kl006["username"] = affected_username_for_message 
                try:
                    response_message_to_customer = response_message_template.format(**format_params_for_customer_kl006)
                except: response_message_to_customer = response_message_template 
            else: response_message_to_customer = response_message_template
    else:
         logger.warning(f"Không tìm thấy template cho response_key KL006: {response_key}")

    customer_response_keyboard_rows = []
    if response_key_suffix in ["sai_id_user", "cuoc_khong_du_user", "khong_du_tong_diem", "nhom_chua_dk", "da_nhan", "thanh_cong"]:
        customer_response_keyboard_rows.append(
            [InlineKeyboardButton(f"✍️ Đăng ký lại KM KL006", callback_data=f'promo_KL006')] # Gọi promo_KL006_callback (đã sửa)
        )
    common_buttons_row_kl006 = [
        InlineKeyboardButton(RESPONSE_MESSAGES.get("cskh_button_text","💬 CSKH trực tuyến"), url=CSKH_LINK),
        InlineKeyboardButton(RESPONSE_MESSAGES.get("back_to_menu_button","⬅️ Quay lại Menu"), callback_data='back_to_menu') # Gọi back_to_menu_handler (đã sửa)
    ]
    customer_response_keyboard_rows.append(common_buttons_row_kl006)
    customer_response_markup = InlineKeyboardMarkup(customer_response_keyboard_rows)

    try:
        await context.bot.send_message(
            chat_id=target_user_id,
            text=response_message_to_customer,
            reply_markup=customer_response_markup,
            parse_mode='Markdown'
        )
        if query.message.text is not None:
            await query.edit_message_text(text=processed_text_for_admin_kl006, reply_markup=None, parse_mode='Markdown')
        elif query.message.caption is not None:
            await query.edit_message_caption(caption=processed_text_for_admin_kl006, reply_markup=None, parse_mode='Markdown')
        else: await query.edit_message_reply_markup(reply_markup=None) 

    except telegram.error.BadRequest as e_edit:
        if any(err_msg in str(e_edit).lower() for err_msg in ["message to edit not found", "message is not modified", "there is no text in the message to edit", "message can't be edited"]):
            logger.warning(f"Không thể sửa tin nhắn admin (KL006 - lỗi đã biết): {e_edit}")
            try: await query.edit_message_reply_markup(reply_markup=None)
            except Exception as e_markup: logger.warning(f"Cũng không thể xóa markup (KL006): {e_markup}")
        else: logger.error(f"Lỗi lạ khi sửa tin nhắn admin (KL006): {e_edit} - Data: {query.data} - Processed Text: '{processed_text_for_admin_kl006}'")
    except Exception as e:
        logger.error(f"Lỗi khi gửi phản hồi KL006 hoặc xử lý tin nhắn admin: {e}")

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    escaped_chat_id = escape_markdown(str(chat_id), version=2) 
    await update.message.reply_text(f"ID của nhóm chat này là: `{escaped_chat_id}`", parse_mode='MarkdownV2')

async def receive_username_for_share_reward(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    game_username = update.message.text.strip() 
    user_id = update.effective_user.id
    user_first_name = update.effective_user.first_name 
    milestone_to_claim = context.user_data.get('milestone_to_claim_share')

    if not milestone_to_claim:
        # Tin nhắn này là reply_text (mới)
        await update.message.reply_text(RESPONSE_MESSAGES.get("error_no_milestone_info", "Lỗi không tìm thấy mốc thưởng. Thử lại."))
        # Nút "Menu Chia Sẻ" gọi share_code_entry_point (đã sửa để gửi mới)
        share_menu_button = InlineKeyboardMarkup([[InlineKeyboardButton(RESPONSE_MESSAGES.get("back_to_share_menu_button", "⬅️ Menu Chia Sẻ"), callback_data='share_code_entry_point')]])
        await update.message.reply_text(RESPONSE_MESSAGES.get("return_to_share_menu_prompt","Vui lòng quay lại menu Chia sẻ:"), reply_markup=share_menu_button)
        return AWAIT_USERNAME_FOR_SHARE_REWARD # User cần bấm nút để quay lại

    admin_text = RESPONSE_MESSAGES.get("share_admin_request_text", "Y/c thưởng chia sẻ: Khách {user_first_name} (ID {user_id}), GameUser {game_username}, Mốc {milestone}").format(
        user_first_name=user_first_name, user_id=user_id, game_username=game_username, milestone=milestone_to_claim
    )
    admin_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Sai ID", callback_data=f"admin_share_resp:{user_id}:{milestone_to_claim}:sai_id"),
            InlineKeyboardButton("✅ Thành Công", callback_data=f"admin_share_resp:{user_id}:{milestone_to_claim}:thanh_cong")
        ],
        [InlineKeyboardButton("💬 Liên hệ CSKH", callback_data=f"admin_share_resp:{user_id}:{milestone_to_claim}:cskh")]
    ])

    try:
        sent_admin_message = await context.bot.send_message(chat_id=ID_GROUP_PROMO, text=admin_text, reply_markup=admin_keyboard) 
        pending_claim_data = {
            "milestone": milestone_to_claim, "game_username": game_username,
            "admin_message_id": sent_admin_message.message_id,
            "submission_time": datetime.datetime.now(pytz.utc).isoformat()
        }
        bot_data_loaded = load_bot_data()
        user_id_str = str(user_id)
        if user_id_str not in bot_data_loaded["users"]: get_user_data_from_json(user_id); bot_data_loaded = load_bot_data() 
        bot_data_loaded["users"][user_id_str]["pending_share_milestone_claim"] = pending_claim_data
        save_bot_data(bot_data_loaded)
        
        message_to_user_template = RESPONSE_MESSAGES.get("share_reward_request_sent", "Đã gửi y/c cho mốc {milestone} với tên {game_username}.")
        message_to_user = message_to_user_template.format(milestone=milestone_to_claim, game_username=escape_markdown(game_username, version=1))

        main_menu_button = InlineKeyboardMarkup([[InlineKeyboardButton(RESPONSE_MESSAGES.get("back_to_menu_button","⬅️ Quay lại Menu"), callback_data='back_to_menu')]])
        await update.message.reply_text(message_to_user, reply_markup=main_menu_button, parse_mode='Markdown') # Đã là reply_text (mới)

    except Exception as e:
        logger.error(f"Lỗi gửi y/c thưởng chia sẻ đến admin: {e}")
        await update.message.reply_text(RESPONSE_MESSAGES.get("error_sending_to_admin", "Lỗi gửi yêu cầu đến admin. Thử lại sau."))

    if 'milestone_to_claim_share' in context.user_data: del context.user_data['milestone_to_claim_share']
    return ConversationHandler.END 

async def handle_admin_share_code_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    try:
        _prefix, target_user_id_str, milestone_str, action = query.data.split(':')
        target_user_id = int(target_user_id_str); milestone_val = int(milestone_str)
    except ValueError:
        logger.error(f"Lỗi parse callback data admin_share_resp: {query.data}")
        await query.edit_message_text(f"Lỗi callback data: {query.data}. Không thể xử lý.", reply_markup=None)
        return

    admin_user = query.from_user
    admin_mention = f"@{admin_user.username}" if admin_user.username else admin_user.first_name 
    bot_data_all = load_bot_data()
    target_user_s_data_json = bot_data_all["users"].get(str(target_user_id))

    if not target_user_s_data_json:
        logger.warning(f"Không tìm thấy dữ liệu người dùng {target_user_id} cho admin_share_resp.")
        await query.edit_message_text(f"Không tìm thấy dữ liệu người dùng {target_user_id}. Yêu cầu có thể đã cũ hoặc lỗi.", reply_markup=None)
        return

    pending_claim_json = target_user_s_data_json.get("pending_share_milestone_claim")
    original_admin_message_text = query.message.text if query.message.text else "" # Lấy text gốc, nếu là caption thì sẽ không có ở đây.
    
    if not pending_claim_json or pending_claim_json.get("milestone") != milestone_val:
        if str(milestone_val) in target_user_s_data_json.get("claimed_share_milestones", {}):
             escaped_original_admin_text = escape_markdown(original_admin_message_text, version=1)
             processed_text_already = f"{escaped_original_admin_text}\n---\n⚠️ Yêu cầu này cho mốc {milestone_val} dường như đã được duyệt trước đó."
             await query.edit_message_text(text=processed_text_already, reply_markup=None, parse_mode='Markdown')
        else: 
            await query.edit_message_text(f"Không tìm thấy yêu cầu đang chờ xử lý cho user {target_user_id} mốc {milestone_val}, hoặc thông tin không khớp.", reply_markup=None)
        return

    game_username_from_json = pending_claim_json.get("game_username", "N/A") 
    user_message_text = "";
    
    escaped_original_admin_text_share = escape_markdown(original_admin_message_text, version=1) 
    escaped_admin_mention_share = escape_markdown(admin_mention, version=1)
    escaped_game_username_for_admin_share = escape_markdown(game_username_from_json, version=1)
    admin_processed_text_share = f"{escaped_original_admin_text_share}\n---\n"

    if action == "thanh_cong":
        if "claimed_share_milestones" not in bot_data_all["users"][str(target_user_id)]:
            bot_data_all["users"][str(target_user_id)]["claimed_share_milestones"] = {}
        bot_data_all["users"][str(target_user_id)]["claimed_share_milestones"][str(milestone_val)] = datetime.datetime.now(pytz.utc).isoformat()
        
        user_message_text = RESPONSE_MESSAGES.get("share_reward_approved", "...").format(milestone=milestone_val, game_username=escape_markdown(game_username_from_json, version=1))
        admin_processed_text_share += f"✅ Đã duyệt bởi {escaped_admin_mention_share} cho mốc {milestone_val} (User: {escaped_game_username_for_admin_share})."
    elif action == "sai_id":
        user_message_text = RESPONSE_MESSAGES.get("share_reward_sai_id", "...").format(milestone=milestone_val) 
        admin_processed_text_share += f"🚫 ID Không Đúng - Xử lý bởi {escaped_admin_mention_share} (User: {escaped_game_username_for_admin_share})."
    elif action == "cskh":
        user_message_text = RESPONSE_MESSAGES.get("share_reward_contact_cskh", "...").format(milestone=milestone_val) 
        admin_processed_text_share += f"ℹ️ Yêu cầu CSKH - Xử lý bởi {escaped_admin_mention_share} (User: {escaped_game_username_for_admin_share})."

    bot_data_all["users"][str(target_user_id)]["pending_share_milestone_claim"] = None 
    save_bot_data(bot_data_all)
    customer_buttons_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("cskh_button_text","💬 CSKH trực tuyến"), url=CSKH_LINK)],
        [InlineKeyboardButton(RESPONSE_MESSAGES.get("back_to_menu_button","⬅️ Quay lại Menu"), callback_data='back_to_menu')]
    ])
    try:
        await context.bot.send_message(chat_id=target_user_id, text=user_message_text, reply_markup=customer_buttons_markup, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Không thể gửi phản hồi thưởng chia sẻ cho user {target_user_id}: {e}")
    try:
        await query.edit_message_text(text=admin_processed_text_share, reply_markup=None, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Không thể edit tin nhắn admin cho phản hồi thưởng chia sẻ: {e}")


async def post_init_actions(application: Application) -> None:
    """Lấy username của bot sau khi Application được khởi tạo."""
    global BOT_USERNAME
    try:
        bot_info = await application.bot.get_me()
        BOT_USERNAME = bot_info.username
        logger.info(f"Bot username được đặt khi khởi động: {BOT_USERNAME}")
    except Exception as e:
        logger.error(f"Không thể lấy username của bot khi khởi động: {e}. Bot có thể không tạo link chia sẻ đúng.")


async def get_file_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message and update.message.photo:
        photo_id = update.message.photo[-1].file_id
        file_size = update.message.photo[-1].file_size
        logger.info(f"Received photo. File ID: {photo_id}, Size: {file_size} bytes")

        # THAY ĐỔI DÒNG NÀY (sử dụng escape_markdown)
        escaped_photo_id = escape_markdown(photo_id, version=2) # Thoát các ký tự đặc biệt cho MarkdownV2
        await update.message.reply_text(
            f"File ID của ảnh này là:\n`{escaped_photo_id}`\n\nBạn có thể copy ID này để sử dụng trong code.",
            parse_mode=telegram.constants.ParseMode.MARKDOWN_V2
        )

def main() -> None:
    telegram_long_poll_timeout_seconds = 50 
    read_timeout_buffer_seconds = 10 

    application_builder = (
        Application.builder()
        .token(BOT_TOKEN)
        .connect_timeout(30) 
        .read_timeout(30)    
        .write_timeout(30)   
        .pool_timeout(60)    
        .connection_pool_size(10) 
        .get_updates_connect_timeout(10)
        .get_updates_read_timeout(telegram_long_poll_timeout_seconds + read_timeout_buffer_seconds) 
        .post_init(post_init_actions) 
    )
    application = application_builder.build()

    application.add_error_handler(error_handler)

    common_fallbacks = [
        CommandHandler('cancel', cancel), 
        CallbackQueryHandler(back_to_menu_handler, pattern='^back_to_menu$'), 
        CallbackQueryHandler(khuyen_mai_callback, pattern='^khuyen_mai$') 
    ]

    kl001_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(promo_KL001_callback, pattern='^promo_KL001$')],
        states={
            AGREE_TERMS_KL001: [CallbackQueryHandler(handle_agree_kl001_terms, pattern='^agree_terms_kl001$')],
            RECEIVE_USERNAME_KL001: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_username_kl001)],
        },
        fallbacks=common_fallbacks + [CallbackQueryHandler(re_enter_username_callback, pattern='^re_enter_username:KL001$')],
    )

    kl007_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(promo_KL007_callback, pattern='^promo_KL007$')],
        states={
            AGREE_TERMS_KL007: [CallbackQueryHandler(handle_agree_kl007_terms, pattern='^agree_terms_kl007$')],
            RECEIVE_USERNAME_KL007: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_username_kl007)],
        },
        fallbacks=common_fallbacks + [CallbackQueryHandler(re_enter_username_callback, pattern='^re_enter_username:KL007$')],
    )

    kl006_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(promo_KL006_callback, pattern='^promo_KL006$')],
        states={
            AGREE_TERMS_KL006: [CallbackQueryHandler(handle_agree_kl006_terms, pattern='^agree_terms_kl006$')],
            KL006_CHOOSE_GROUP_SIZE: [
                CallbackQueryHandler(kl006_group_size_selected, pattern=r'^kl006_select_group:\d+$')
            ],
            RECEIVE_USERNAMES_KL006: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_usernames_kl006),
                CallbackQueryHandler(kl006_reenter_usernames_after_agree_callback, pattern=r'^kl006_reenter_usernames_after_agree:\d+$')
            ],
        },
        fallbacks=common_fallbacks, 
    )

    app_promo_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(promo_app_experience_callback, pattern='^promo_app_experience$')],
        states={
            AGREE_TERMS_APP_PROMO: [CallbackQueryHandler(handle_agree_app_promo_terms, pattern='^agree_terms_app_promo$')],
            RECEIVE_USERNAME_APP_PROMO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_username_app_promo)],
            AWAIT_IMAGE_CONFIRM_APP_PROMO: [CallbackQueryHandler(handle_image_confirm_app_promo, pattern=r'^app_promo_has_image:(yes|no)$')],
            RECEIVE_IMAGE_APP_PROMO: [MessageHandler(filters.PHOTO, receive_image_app_promo)],
        },
        fallbacks=common_fallbacks + [CallbackQueryHandler(re_enter_username_callback, pattern='^re_enter_username:APP_PROMO$')],
    )

    share_code_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(share_code_entry_point, pattern='^share_code_entry_point$')
        ],
        states={
            SHOW_SHARE_MENU: [ 
                CallbackQueryHandler(get_my_share_link_callback, pattern='^share_get_link$'),
                CallbackQueryHandler(request_code_reward_callback, pattern='^share_request_reward$'),
                CallbackQueryHandler(share_code_entry_point_cancel, pattern='^share_code_entry_point_cancel$') 
            ],
            AWAIT_USERNAME_FOR_SHARE_REWARD: [ 
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_username_for_share_reward),
                CallbackQueryHandler(share_code_entry_point_cancel, pattern='^share_code_entry_point_cancel$') 
            ],
        },
        fallbacks=common_fallbacks, 
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("id", get_chat_id)) 
    application.add_handler(CallbackQueryHandler(khuyen_mai_callback, pattern='^khuyen_mai$')) 

    application.add_handler(kl001_conv_handler)
    application.add_handler(kl007_conv_handler)
    application.add_handler(kl006_conv_handler)
    application.add_handler(app_promo_conv_handler)
    application.add_handler(share_code_conv_handler)

    application.add_handler(CallbackQueryHandler(handle_admin_response, pattern='^admin_response:'))
    application.add_handler(CallbackQueryHandler(handle_admin_kl006_response, pattern='^admin_kl006:'))
    application.add_handler(MessageHandler(
        filters.Chat(chat_id=ID_GROUP_PROMO) & filters.REPLY & filters.TEXT & ~filters.COMMAND,
        handle_admin_kl007_point_reply 
    ))
    application.add_handler(CallbackQueryHandler(handle_admin_share_code_response, pattern='^admin_share_resp:'))
    application.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, get_file_id_handler))

    logger.info("Bot đang chạy...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)



if __name__ == "__main__":
    if not os.path.exists(DATA_FILE):
        save_bot_data({"users": {}, "referral_code_to_user_id_map": {}})
        logger.info(f"Đã khởi tạo file dữ liệu rỗng: {DATA_FILE}")
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot đã dừng bởi người dùng.")
    except Exception as e:
        logger.critical(f"Lỗi nghiêm trọng khi chạy bot: {e}", exc_info=True)