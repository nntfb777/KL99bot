# core/bot_setup.py
from core.database import init_db
import asyncio
import logging
from telegram import Update
from telegram.ext import Application, Defaults, PicklePersistence, ContextTypes
from telegram.constants import ParseMode
from telegram.request import HTTPXRequest # <<-- Thêm import còn thiếu
import config
from core.database import init_db
from core.referral_processor import referral_processor_worker, REFERRAL_QUEUE

logger = logging.getLogger(__name__)


async def persistence_saver_worker(application: Application):
    """
    "Công nhân" chạy nền, có nhiệm vụ duy nhất là lưu dữ liệu persistence
    xuống đĩa một cách định kỳ và bất đồng bộ.
    """
    logger.info("Persistence Saver worker started.")
    while True:
        try:
            # Đợi một khoảng thời gian. 5-10 giây là một lựa chọn tốt.
            await asyncio.sleep(5)

            # Thực hiện việc lưu bất đồng bộ.
            # Lệnh này sẽ không "đóng băng" bot.
            await application.update_persistence()
            logger.debug("Persistence data flushed to disk by worker.")

        except asyncio.CancelledError:
            # Khi bot tắt, thực hiện một lần lưu cuối cùng
            logger.info("Persistence Saver worker is shutting down. Performing final save...")
            await application.flush_persistence()
            break # Thoát khỏi vòng lặp
        except Exception as e:
            logger.error(f"Error in Persistence Saver worker: {e}", exc_info=True)
            # Nghỉ một lúc nếu có lỗi để tránh spam log
            await asyncio.sleep(30)


async def post_init(application: Application) -> None:
    """
    Hàm chạy một lần sau khi bot khởi động để:
    1. Khởi tạo cơ sở dữ liệu (quan trọng nhất).
    2. Lấy username của bot.
    """
    # 1. KHỞI TẠO CƠ SỞ DỮ LIỆU
    try:
        logger.info("Đang khởi tạo CSDL (từ post_init)...")
        await init_db()
        logger.info("CSDL đã được khởi tạo thành công.")
    except Exception as e:
        logger.critical(f"Không thể khởi tạo CSDL trong post_init! Lỗi: {e}", exc_info=True)

    # 2. Lấy và lưu trữ username
    try:
        if not config.BOT_USERNAME:
            bot_info = await application.bot.get_me()
            config.BOT_USERNAME = bot_info.username
            logger.info(f"Username của bot đã được lấy và lưu: {config.BOT_USERNAME}")
    except Exception as e:
        logger.error(f"Không thể lấy username của bot khi khởi động: {e}", exc_info=True)
    logger.info("Starting background workers...")
    application.background_tasks = {
        'persistence_saver': asyncio.create_task(persistence_saver_worker(application)),
        'referral_processor': asyncio.create_task(referral_processor_worker(application))
    }

    logger.info(f"{len(application.background_tasks)} background workers have been started.")

async def post_shutdown(application: Application) -> None:
    """Chạy trước khi bot tắt hẳn để dọn dẹp các tác vụ nền."""
    logger.info("Running post_shutdown tasks...")

    background_tasks = getattr(application, 'background_tasks', {})
    if not background_tasks:
        logger.info("No background tasks to shut down.")
        return

    # Hủy bỏ các tác vụ nền
    logger.info("Cancelling background tasks...")
    for task_name, task in background_tasks.items():
        task.cancel()
        logger.debug(f"Task '{task_name}' cancelled.")

    # Chờ cho các tác vụ nền thực sự kết thúc (chúng sẽ lưu lần cuối)
    await asyncio.gather(*background_tasks.values(), return_exceptions=True)

    logger.info("Background tasks shutdown complete.")

def create_application() -> Application:
    """Tạo và cấu hình Application object với Persistence và timeout."""
    logger.info("Đang xây dựng Application...")

    persistence = PicklePersistence(filepath="bot_persistence")

    custom_request = HTTPXRequest(
        connect_timeout=20.0,
        read_timeout=60.0,
        pool_timeout=20.0
    )

    application = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .persistence(persistence)
        .request(custom_request)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # Đặt parse_mode mặc định. Đổi thành MARKDOWN_V2 nếu bạn dùng nó nhiều hơn.
    application.defaults = Defaults(parse_mode=ParseMode.MARKDOWN_V2)

    logger.info("Application đã được tạo thành công.")
    return application