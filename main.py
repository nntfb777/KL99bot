# main.py

import logging
import sys

# Add project root to path to allow absolute imports
# sys.path.insert(0, '/path/to/your/klbot_project') # Adjust if needed

# --- Core and Utils Imports ---
import config
from core.database import init_db
from core.bot_setup import create_application

# --- Feature Handlers Imports ---
from features.common_handlers import start, cancel, show_promo_menu, show_main_menu
from features.get_id_handlers import get_chat_id_handler, get_file_id_handler
from features.admin_handlers import (
    handle_admin_promo_response,
    handle_admin_kl007_point_reply,
    handle_admin_share_response,
    handle_admin_kl007_prompt,
    handle_admin_kl006_response
    # Add other admin handlers here, e.g.,
)
from features.promo_handlers.kl001 import kl001_conv_handler
from features.promo_handlers.kl006 import kl006_conv_handler
from features.promo_handlers.kl007 import kl007_conv_handler
from features.promo_handlers.app_promo import app_promo_conv_handler
from features.promo_handlers.sharing import sharing_conv_handler

from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters

# --- Basic Logging Configuration ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

def main() -> None:
    """Start the bot."""
    logger.info("Starting bot initialization...")

    # 1. Initialize the database
    init_db()

    # 2. Create the Telegram Application object
    application = create_application()

    # 3. Register all handlers
    logger.info("Registering handlers...")

    # --- Conversation Handlers (for multi-step interactions) ---
    application.add_handler(kl001_conv_handler)
    application.add_handler(kl006_conv_handler)
    application.add_handler(kl007_conv_handler)
    application.add_handler(app_promo_conv_handler)
    application.add_handler(sharing_conv_handler)

    # --- Admin Response Handlers ---
    # These handlers process callbacks from buttons admins click
    application.add_handler(CallbackQueryHandler(handle_admin_promo_response, pattern='^admin_response:'))
    application.add_handler(CallbackQueryHandler(handle_admin_share_response, pattern='^admin_share_resp:'))
    application.add_handler(CallbackQueryHandler(handle_admin_kl006_response, pattern=r'^admin_kl006:'))
    application.add_handler(CallbackQueryHandler(handle_admin_kl007_prompt, pattern='^admin_kl007_prompt_reply:'))
    # This handler processes text replies from admins (specifically for KL007 points)
    application.add_handler(MessageHandler(
        filters.Chat(chat_id=config.ID_GROUP_PROMO) & filters.REPLY & filters.TEXT & ~filters.COMMAND,
        handle_admin_kl007_point_reply
    ))

    # --- Command Handlers ---
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("id", get_chat_id_handler))
    # A generic cancel command that can be used outside conversations
    application.add_handler(CommandHandler("cancel", cancel))

    # --- General Callback Handlers (for menu navigation) ---
    application.add_handler(CallbackQueryHandler(show_main_menu, pattern='^back_to_main_menu$'))
    application.add_handler(CallbackQueryHandler(show_promo_menu, pattern='^show_promo_menu$'))
    # A generic cancel button that can be used inside conversations (but is handled by fallbacks)
    application.add_handler(CallbackQueryHandler(cancel, pattern='^cancel$'))

    # --- Utility Handlers ---
    # This handler gets the file ID of any photo sent to the bot
    application.add_handler(MessageHandler(filters.PHOTO & ~filters.COMMAND, get_file_id_handler))


    # 4. Run the bot
    logger.info("Bot is running. Polling for updates...")
    application.run_polling()


if __name__ == "__main__":
    main()