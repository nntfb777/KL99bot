# core/referral_processor.py
import asyncio
import logging
from telegram.ext import Application

# Import các thành phần cần thiết
from . import database
from texts import RESPONSE_MESSAGES
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)

# Hàng đợi chuyên dụng CHỈ cho các tác vụ xử lý giới thiệu
REFERRAL_QUEUE = asyncio.Queue()

async def referral_processor_worker(application: Application):
    """
    (Nâng cấp) "Công nhân" chạy nền, xử lý TOÀN BỘ logic database của lệnh /start.
    """
    logger.info("Start Command Processor worker started.")
    while True:
        try:
            # Lấy gói công việc từ hàng đợi
            task_type, data = await REFERRAL_QUEUE.get()

            if task_type == 'CREATE_USER_AND_PROCESS_REF':
                # Đây là tác vụ chính từ /start
                user_dict = data.get('user')
                context_args = data.get('context_args')

                # 1. Luôn tạo user (hành động ghi)
                await database.get_or_create_user(
                    user_id=user_dict['id'],
                    first_name=user_dict.get('first_name'),
                    username=user_dict.get('username')
                )

                # 2. Xử lý giới thiệu (hành động ghi)
                if context_args and context_args[0].startswith('ref_'):
                    referral_code = context_args[0][4:]
                    # Đọc referrer là nhanh, có thể làm ở đây
                    referrer = await database.get_user_by_referral_code(referral_code)

                    if referrer and referrer['user_id'] != user_dict['id']:
                        success = await database.set_referrer(user_dict['id'], referrer['user_id'])
                        referrer_user_id = referrer['user_id']
                        if success:
                # 2. GỬI THÔNG BÁO CHO NGƯỜI GIỚI THIỆU
                            try:
                                referrer_data = await database.get_user_by_id(referrer_user_id)
                                if referrer_data:
                                    share_count = referrer_data.get('share_count', 0)
                                    await application.bot.send_message(
                                        chat_id=referrer_user_id,
                                        text=RESPONSE_MESSAGES["referral_successful_notification_to_referrer"].format(share_count=share_count),
                                        parse_mode=ParseMode.MARKDOWN_V2
                                    )
                            except Exception as e:
                                logger.error(f"Referral worker failed to notify referrer {referrer_user_id}: {e}")

            REFERRAL_QUEUE.task_done()
            await asyncio.sleep(0.3) # Vẫn nghỉ để nhường đường

        except Exception as e:
            logger.error(f"Error in Start Processor worker: {e}", exc_info=True)
            if REFERRAL_QUEUE.empty() is False:
                 REFERRAL_QUEUE.task_done()
