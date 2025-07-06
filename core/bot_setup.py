# core/bot_setup.py

import logging
from telegram import Update
from telegram.ext import Application, Defaults, PicklePersistence, ContextTypes
import config
from telegram.constants import ParseMode
# Cấu hình logging
logger = logging.getLogger(__name__)


async def error_handler(update: object, context) -> None:
    """
    Xử lý các lỗi phát sinh trong quá trình bot hoạt động.
    """
    logger.error(f"Lỗi không mong muốn: {context.error}", exc_info=context.error)

# Dán hàm này vào file core/bot_setup.py, phía trên hàm create_application

async def post_init(context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Hàm chạy một lần sau khi bot khởi động để:
    1. Lấy username của bot và lưu vào config.
    2. Đặt tên hiển thị cho bot.
    """
    application = context.application

    # 1. Lấy và lưu trữ username
    try:
        if not config.BOT_USERNAME: # Chỉ lấy nếu chưa được đặt
            bot_info = await application.bot.get_me()
            config.BOT_USERNAME = bot_info.username
            logger.info(f"Username của bot đã được lấy và lưu: {config.BOT_USERNAME}")
    except Exception as e:
        logger.error(f"Không thể lấy username của bot khi khởi động: {e}")

    # 2. Đặt tên hiển thị cho bot
    try:
        if config.BOT_DISPLAY_NAME: # Chỉ đặt nếu tên được định nghĩa trong config
            await application.bot.set_my_name(config.BOT_DISPLAY_NAME)
            logger.info(f"Tên hiển thị của bot đã được đặt thành: {config.BOT_DISPLAY_NAME}")
    except Exception as e:
        logger.error(f"Lỗi khi đặt tên hiển thị cho bot: {e}")

def create_application() -> Application:
    """Tạo và cấu hình Application object với Persistence."""
    logger.info("Đang xây dựng Application...")

    # 1. Tạo đối tượng Persistence
    # Dữ liệu sẽ được lưu vào file có tên là 'bot_persistence'
    # Bạn có thể đổi tên file nếu muốn
    persistence = PicklePersistence(filepath="bot_persistence")

    # 2. Xây dựng Application và truyền persistence vào
    application = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .defaults(Defaults(parse_mode=ParseMode.HTML))
        .persistence(persistence) # <--- DÒNG QUAN TRỌNG
        .build()
    )

    application.job_queue.run_once(post_init, 0)

    logger.info("Application đã được tạo thành công.")
    return application
