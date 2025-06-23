# Tệp: bot.py (Đã sửa lỗi đăng ký handler)

import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

import config
import database
from handlers import core, transactions, promotions, sharing, admin, utils

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

async def post_init(application: Application) -> None:
    bot_info = await application.bot.get_me()
    config.BOT_USERNAME = bot_info.username
    logger.info(f"Bot username được đặt: {config.BOT_USERNAME}")

def main() -> None:
    if not config.BOT_TOKEN or 'YOUR_BOT_TOKEN_HERE' in config.BOT_TOKEN:
        logger.critical("BOT_TOKEN chưa được cấu hình. Vui lòng kiểm tra file config.py.")
        return

    database.init_db()

    application = Application.builder().token(config.BOT_TOKEN).post_init(post_init).build()
    application.add_error_handler(core.error_handler)

    # --- ĐĂNG KÝ CÁC CONVERSATION HANDLERS ---
    application.add_handler(transactions.deposit_conv_handler)
    application.add_handler(transactions.withdrawal_conv_handler)
    
    application.add_handler(promotions.kl001_conv_handler)
    application.add_handler(promotions.kl006_conv_handler)
    application.add_handler(promotions.kl007_conv_handler)
    application.add_handler(promotions.app_promo_conv_handler)
    
    application.add_handler(sharing.share_code_conv_handler)

    # --- ĐĂNG KÝ CÁC HANDLER CHO ADMIN (PHẦN ĐÃ SỬA LỖI) ---
    
    # SỬA LỖI: Bỏ các handler không tồn tại và đăng ký đúng các handler đã có trong admin.py
    
    # Handler chung cho KL001, KL007 và các KM đơn giản khác
    application.add_handler(CallbackQueryHandler(admin.handle_admin_response, pattern='^admin_response:'))
    
    # Handler riêng cho KL006
    application.add_handler(CallbackQueryHandler(admin.handle_admin_kl006_response, pattern='^admin_kl006:'))
    
    # Handler riêng cho KM Tải App
    application.add_handler(CallbackQueryHandler(admin.handle_admin_app_promo_response, pattern='^admin_app_promo:'))
    
    # Handler riêng cho Thưởng chia sẻ
    application.add_handler(CallbackQueryHandler(admin.handle_admin_share_code_response, pattern='^admin_share_resp:'))

    # Handler cho admin reply tin nhắn (để nhập điểm KL007)
    application.add_handler(MessageHandler(
        filters.Chat(chat_id=config.ID_GROUP_PROMO) & filters.REPLY & filters.TEXT & ~filters.COMMAND,
        admin.handle_admin_kl007_point_reply
    ))

    # --- ĐĂNG KÝ CÁC COMMAND HANDLERS VÀ CALLBACK HANDLERS ĐỘC LẬP ---
    application.add_handler(CommandHandler("start", core.start))
    application.add_handler(CommandHandler("cancel", core.cancel))

    application.add_handler(CommandHandler("id", utils.get_chat_id))
    application.add_handler(MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, utils.get_file_id_handler))

    application.add_handler(CallbackQueryHandler(core.back_to_menu_handler, pattern='^back_to_menu$'))
    application.add_handler(CallbackQueryHandler(promotions.khuyen_mai_callback, pattern='^khuyen_mai$'))

    logger.info("Bot đang chạy...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()