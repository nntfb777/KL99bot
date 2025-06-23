# core/bot_setup.py

import logging
from telegram import Update
from telegram.ext import Application
import config  # Giả định bạn có file config.py như kế hoạch đã vạch ra

# Cấu hình logging
logger = logging.getLogger(__name__)

async def post_init(application: Application) -> None:
    """
    Hàm chạy sau khi bot được khởi tạo để lấy thông tin bot.
    """
    try:
        bot_info = await application.bot.get_me()
        config.BOT_USERNAME = bot_info.username
        logger.info(f"Tên người dùng của bot đã được đặt: {config.BOT_USERNAME}")
    except Exception as e:
        logger.error(f"Không thể lấy tên người dùng của bot khi khởi động: {e}")

async def error_handler(update: object, context) -> None:
    """
    Xử lý các lỗi phát sinh trong quá trình bot hoạt động.
    """
    logger.error(f"Lỗi không mong muốn: {context.error}", exc_info=context.error)

def create_application() -> Application:
    """
    Xây dựng và cấu hình đối tượng Application cho bot.
    """
    logger.info("Đang xây dựng Application...")
    application = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .connect_timeout(30)
        .read_timeout(30)
        .write_timeout(30)
        .post_init(post_init)
        .build()
    )
    application.add_error_handler(error_handler)
    logger.info("Application đã được tạo thành công.")
    return application