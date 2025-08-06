# main.py

import asyncio
import logging
import sys
import os
import traceback
import html
import json
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# --- THIẾT LẬP ĐƯỜNG DẪN GỐC ---
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# --- CÁC IMPORT CHÍNH ---
import config
from core.database import init_db
from core.bot_setup import create_application
from core.telegram_logger import TelegramLogHandler
from core import request_limiter

# --- IMPORTS CHO HANDLERS ---
from features.common_handlers import (
    start, unified_cleanup_handler, show_promo_menu,
    show_main_menu, show_transaction_menu, show_cskh_warning,
    handle_stray_messages
)
from features.get_id_handlers import get_id_handler
from features.admin_handlers import (
    handle_admin_promo_response, handle_admin_share_response, handle_admin_kl006_response,
    handle_admin_kl007_point_reply, admin_reply_conv_handler, handle_admin_withdraw_response,
    handle_admin_deposit_response, share_add_command, delcid_command, resend_pending_claims_command
)
from features.promo_handlers.kl001 import kl001_conv_handler
from features.promo_handlers.kl006 import kl006_conv_handler
from features.promo_handlers.kl007 import kl007_conv_handler
from features.promo_handlers.app_promo import app_promo_conv_handler
from features.promo_handlers.sharing import sharing_conv_handler, share_code_entry_point
from features.transaction_handlers.deposit import deposit_conv_handler
from features.transaction_handlers.withdraw import withdraw_conv_handler
from features.game_link_handler import provide_game_link, report_link_conv_handler
from features.fallbacks import get_fallbacks

# --- CẤU HÌNH LOGGING VÀ ERROR HANDLER Ở PHẠM VI TOÀN CỤC ---
# Cấu hình logging cơ bản
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO # Đổi thành logging.DEBUG khi cần gỡ lỗi chi tiết
)
# Giảm bớt log thừa từ các thư viện
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("apscheduler").setLevel(logging.WARNING)
# Tạo logger cho file main
logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bắt tất cả các lỗi, ghi log và gửi thông báo chi tiết thành nhiều phần đến nhóm log."""
    logger.error("Exception while handling an update:", exc_info=context.error)

    # 1. Thu thập thông tin đầy đủ
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)
    update_str = update.to_dict() if isinstance(update, Update) else str(update)

    # 2. Tạo các phần của tin nhắn
    header = "<b>🚨 Lỗi nghiêm trọng xảy ra</b>"
    update_info = (
        f"<b>Update gây lỗi:</b>\n"
        f"<pre>{html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}</pre>"
    )
    traceback_info = f"<b>Traceback:</b>\n<pre>{html.escape(tb_string)}</pre>"

    # 3. Gửi các phần đi một cách an toàn
    if config.LOG_GROUP_CHAT_ID:
        try:
            # Gửi tin nhắn tiêu đề trước
            await context.bot.send_message(
                chat_id=config.LOG_GROUP_CHAT_ID,
                text=header,
                parse_mode=ParseMode.HTML
            )

            # Gửi thông tin Update, cắt nếu cần
            if len(update_info) > 4096:
                for i in range(0, len(update_info), 4096):
                    await context.bot.send_message(
                        chat_id=config.LOG_GROUP_CHAT_ID,
                        text=update_info[i:i+4096],
                        parse_mode=ParseMode.HTML
                    )
            else:
                await context.bot.send_message(
                    chat_id=config.LOG_GROUP_CHAT_ID,
                    text=update_info,
                    parse_mode=ParseMode.HTML
                )

            # Gửi thông tin Traceback, cắt nếu cần
            if len(traceback_info) > 4096:
                for i in range(0, len(traceback_info), 4096):
                    await context.bot.send_message(
                        chat_id=config.LOG_GROUP_CHAT_ID,
                        text=traceback_info[i:i+4096],
                        parse_mode=ParseMode.HTML
                    )
            else:
                await context.bot.send_message(
                    chat_id=config.LOG_GROUP_CHAT_ID,
                    text=traceback_info,
                    parse_mode=ParseMode.HTML
                )

        except Exception as e:
            logger.error(f"FATAL: Không thể gửi log lỗi đến Telegram: {e}")
            try:
                # Phương án dự phòng cuối cùng: gửi văn bản thuần
                fallback_message = f"Lỗi nghiêm trọng: {context.error}"
                await context.bot.send_message(
                    chat_id=config.LOG_GROUP_CHAT_ID,
                    text=fallback_message
                )
            except Exception as final_e:
                logger.critical(f"Không thể gửi cả tin nhắn log dự phòng: {final_e}")


# --- HÀM MAIN CHÍNH (BẤT ĐỒNG BỘ) ---
def main() -> None:
    """Khởi tạo và chạy bot."""
    logger.info("Starting bot initialization...")

    # BƯỚC 1: Tạo Application
    application = create_application()

    # BƯỚC 2: Đăng ký error handler NGAY LẬP TỨC
    application.add_error_handler(error_handler)


    # Các tác vụ đồng bộ khác
    request_limiter.start_background_flusher()
    request_limiter.schedule_daily_reset()

    # Thêm TelegramLogHandler sau khi đã có application
    #if config.LOG_GROUP_CHAT_ID:
    #    telegram_handler = TelegramLogHandler(application=application, chat_id=config.LOG_GROUP_CHAT_ID)
    #    telegram_handler.setLevel(logging.ERROR)
    #    logging.getLogger().addHandler(telegram_handler)

    # BƯỚC 4: Đăng ký các handler nghiệp vụ
    logger.info("Registering handlers...")

    conv_handlers = [
        kl001_conv_handler, kl006_conv_handler, kl007_conv_handler, app_promo_conv_handler,
        sharing_conv_handler, deposit_conv_handler, withdraw_conv_handler,
        admin_reply_conv_handler, report_link_conv_handler
    ]

    global_handlers = [
        CommandHandler("start", start),
        CommandHandler("id", get_id_handler),
        CommandHandler("shareadd", share_add_command),
        CommandHandler("delcid", delcid_command),
        CommandHandler("resendpending", resend_pending_claims_command),

        CallbackQueryHandler(show_promo_menu, pattern='^show_promo_menu$'),
        CallbackQueryHandler(show_transaction_menu, pattern='^transaction_entry_point$'),
        # Entry point của sharing_conv_handler đã được định nghĩa trong chính nó
        # không cần đăng ký lại ở đây nếu nó là entry_point của ConversationHandler
        # sharing_conv_handler.entry_points[0],
        CallbackQueryHandler(show_main_menu, pattern='^show_main_menu$'),
        CallbackQueryHandler(unified_cleanup_handler, pattern='^cleanup_now$'),
        CallbackQueryHandler(show_cskh_warning, pattern='^cskh_vpn_warning$'),
        CallbackQueryHandler(provide_game_link, pattern='^request_game_link$'),
    ]

    admin_handlers = [
        CallbackQueryHandler(handle_admin_promo_response, pattern='^admin_response:'),
        CallbackQueryHandler(handle_admin_share_response, pattern='^admin_share_resp:'),
        CallbackQueryHandler(handle_admin_kl006_response, pattern=r'^admin_kl006:'),
        CallbackQueryHandler(handle_admin_deposit_response, pattern='^admin_deposit:'),
        CallbackQueryHandler(handle_admin_withdraw_response, pattern='^admin_withdraw:'),
        MessageHandler(filters.Chat(chat_id=config.ID_GROUP_KL007) & filters.REPLY & filters.TEXT & ~filters.COMMAND, handle_admin_kl007_point_reply),
    ]

    stray_handlers = [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_stray_messages)]

    application.add_handlers(conv_handlers, group=0)
    application.add_handlers(global_handlers, group=1)
    application.add_handlers(admin_handlers, group=2)
    application.add_handlers(stray_handlers, group=10)
    logger.info("All handlers registered.")

    # BƯỚC 5: CHẠY BOT
    logger.info("Bot is running. Polling for updates...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)



# --- ĐIỂM KHỞI ĐỘNG CHƯƠNG TRÌNH ---
if __name__ == "__main__":
    main()