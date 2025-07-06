# main.py

import logging
import sys
import os

# --- THIẾT LẬP ĐƯỜNG DẪN GỐC ---
# Thêm thư mục gốc của dự án vào sys.path để có thể dùng absolute import
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# --- CÁC IMPORT CHÍNH ---
import config
from core.database import init_db
from core.bot_setup import create_application
from core.telegram_logger import TelegramLogHandler

# --- IMPORTS CHO HANDLERS ---
# Common Handlers (Điều hướng chung)
from features.common_handlers import start, cancel, show_promo_menu, show_main_menu, show_transaction_menu
# Utility Handlers
from features.get_id_handlers import get_id_handler
# Admin Handlers
from features.admin_handlers import (
    handle_admin_promo_response,
    handle_admin_share_response,
    handle_admin_kl006_response,
    handle_admin_kl007_point_reply,
    handle_admin_deposit_response, # Handler cho các nút admin deposit đơn giản
    admin_reply_conv_handler,
    handle_admin_withdraw_response,
    share_add_command
)
# Conversation Handlers
from features.promo_handlers.kl001 import kl001_conv_handler
from features.promo_handlers.kl006 import kl006_conv_handler
from features.promo_handlers.kl007 import kl007_conv_handler
from features.promo_handlers.app_promo import app_promo_conv_handler
from features.promo_handlers.sharing import sharing_conv_handler
from features.transaction_handlers.deposit import deposit_conv_handler
from features.transaction_handlers.withdraw import withdraw_conv_handler

# Import các lớp handler từ thư viện
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters


def main() -> None:
    """Khởi tạo và chạy bot."""

    # --- BƯỚC 1: KHỞI TẠO CÁC THÀNH PHẦN CƠ BẢN ---
    init_db()
    application = create_application()
    logger = logging.getLogger(__name__) # Tạo logger sau khi Application được tạo
    logger.info("Starting bot initialization...")

    # --- BƯỚC 2: CẤU HÌNH LOGGING NÂNG CAO ---
    log_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    root_logger = logging.getLogger()

    # Xóa các handler cũ để tránh log bị lặp nếu hàm main được gọi lại
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.setLevel(logging.INFO) # Đặt cấp độ chung

    # Handler để in ra console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    # Handler để gửi log lỗi đến Telegram
    if config.LOG_GROUP_CHAT_ID:
        telegram_handler = TelegramLogHandler(application=application, chat_id=config.LOG_GROUP_CHAT_ID)
        telegram_handler.setLevel(logging.ERROR) # Chỉ gửi lỗi ERROR và CRITICAL
        telegram_handler.setFormatter(log_formatter)
        root_logger.addHandler(telegram_handler)

    # Giảm bớt log thừa từ các thư viện
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)

    logger.info("Logging configured.")

    # --- BƯỚC 3: ĐĂNG KÝ HANDLER THEO NHÓM ƯU TIÊN ---
    logger.info("Registering handlers...")

    # GROUP 0: Các handler điều hướng toàn cục, ưu tiên cao nhất
    navigation_handlers = [
        CallbackQueryHandler(show_main_menu, pattern='^back_to_main_menu$'),
        CallbackQueryHandler(show_promo_menu, pattern='^show_promo_menu$'),
        CallbackQueryHandler(show_transaction_menu, pattern='^transaction_entry_point$'),
        CallbackQueryHandler(cancel, pattern='^cancel$'),
        CommandHandler("cancel", cancel)
    ]
    application.add_handlers(navigation_handlers, group=0)

    # GROUP 1: Các ConversationHandler cho các luồng chính
    conv_handlers = [
        kl001_conv_handler,
        kl006_conv_handler,
        kl007_conv_handler,
        app_promo_conv_handler,
        sharing_conv_handler,
        deposit_conv_handler,
        withdraw_conv_handler,
        admin_reply_conv_handler
    ]
    application.add_handlers(conv_handlers, group=1)

    # GROUP 2: Các handler admin và lệnh thông thường
    other_handlers = [
        # Admin handlers (các nút đơn giản)
        CallbackQueryHandler(handle_admin_promo_response, pattern='^admin_response:'),
        CallbackQueryHandler(handle_admin_share_response, pattern='^admin_share_resp:'),
        CallbackQueryHandler(handle_admin_kl006_response, pattern=r'^admin_kl006:'),
        CallbackQueryHandler(handle_admin_deposit_response, pattern='^admin_deposit:'),
        CallbackQueryHandler(handle_admin_withdraw_response, pattern='^admin_withdraw:'),

        # Admin message handlers
        MessageHandler(
            filters.Chat(chat_id=config.ID_GROUP_KL007) & filters.REPLY & filters.TEXT & ~filters.COMMAND,
            handle_admin_kl007_point_reply
        ),

        # Lệnh thông thường
        CommandHandler("start", start),
        CommandHandler("id", get_id_handler),
        CommandHandler("shareadd", share_add_command),

    ]
    application.add_handlers(other_handlers, group=2)

    # --- BƯỚC 4: CHẠY BOT ---
    logger.info("Bot is running. Polling for updates...")
    application.run_polling()


if __name__ == "__main__":
    main()