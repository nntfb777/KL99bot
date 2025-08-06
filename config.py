# Tệp: config.py
import os
from dotenv import load_dotenv
import logging
logger = logging.getLogger(__name__)

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("Không tìm thấy BOT_TOKEN trong biến môi trường!")
ADMIN_IDS_STR = os.getenv("ADMIN_IDS")

# Xử lý để chuyển chuỗi thành một danh sách các số nguyên
if ADMIN_IDS_STR:
    try:
        # Tách chuỗi bằng dấu phẩy và chuyển từng phần tử thành số nguyên
        ADMIN_IDS = [int(admin_id.strip()) for admin_id in ADMIN_IDS_STR.split(',')]
    except ValueError:
        # Ghi log và đặt danh sách rỗng nếu có lỗi (ví dụ: có chữ trong chuỗi)
        logger.error("Lỗi: ADMIN_IDS trong file .env chứa giá trị không phải là số.")
        ADMIN_IDS = []
else:
    # Ghi log và đặt danh sách rỗng nếu biến không tồn tại
    logger.warning("Cảnh báo: Biến ADMIN_IDS không được đặt trong file .env.")
    ADMIN_IDS = []
# Các liên kết chính của bot
APP_DOWNLOAD_LINK = 'https://99kl.app/DownloadApp/'
# Danh sách các link trang chủ ngẫu nhiên
GAME_LINKS = [
    "https://kl99.immo/",
    "https://kl99.love",
    "https://kl99.me",
    "https://kl99.meme",
    "https://kl99.men",
    "https://kl99.mobi",
    # Thêm các link khác của bạn vào đây
]
TELEGRAM_CHANNEL_LINK = 'https://t.me/bet_kl99'
FACEBOOK_LINK = 'https://www.facebook.com/KL99GiaiTriDinhCaoChauA/'
CSKH_LINK = 'https://umyq3uemgd.we2vub70.com/chatwindow.aspx?siteId=65002300&planId=88c557f5-5a2c-4ea3-b364-9cda2464fa7b&chatgroup=3&_=1748177033765'

# --- DATABASE ---
DB_NAME = 'klbot.db'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, DB_NAME)

# Tên người dùng của bot (sẽ được cập nhật tự động khi bot khởi tạo từ Telegram API)
BOT_USERNAME = None

BOT_DISPLAY_NAME = "KL99 - Đẳng Cấp Hàng Đầu Châu Á!"

SHARE_MILESTONES_REWARDS = {
    15: 8,
    30: 18,
    50: 28,
    100: 38,
    200: 58,
    500: 88,
    1000:138
}

SHARE_MILESTONES = list(SHARE_MILESTONES_REWARDS.keys())


START_IMAGE_FILE_ID = "AgACAgUAAxkBAAOlaHCwMAOf5hdNF-nW3Ldk4-49hZ8AAm_PMRvQLIlXjDylPEEdof4BAAMCAAN4AAM2BA"
PROMO_KL001_IMAGE_ID = "AgACAgUAAxkBAAOraHCwlrKeuXkGu4n60zjmA31pBR8AAnDPMRvQLIlXvyZZxbm_Ti0BAAMCAAN4AAM2BA"
PROMO_KL006_IMAGE_ID = "AgACAgUAAxkBAAOuaHCwyIWTjNfPFf6xkgtKmrRtYmIAAnHPMRvQLIlXttqdWGwGakMBAAMCAAN4AAM2BA"
PROMO_KL007_IMAGE_ID = "AgACAgUAAxkBAAOxaHCxmVnniBDAT0UYQZ0GfYvMvZkAAnXPMRvQLIlXPLJ5NNG7iDwBAAMCAAN4AAM2BA"
PROMO_IMAGE_ID = "AgACAgUAAxkBAAO0aHCxr1PudDghuCLKEgVGtO_8tQUAAnbPMRvQLIlXSJN9Mz7Jt9oBAAMCAAN4AAM2BA"
TRANS_IMAGE_ID = "AgACAgUAAxkBAAO3aHC0RiRhUhSI1o-kZNPsm5qQz5MAAnjPMRvQLIlX0Tc55ynPV2sBAAMCAAN4AAM2BA"
SHARING_IMAGE_ID = "AgACAgUAAxkBAAO6aHC0YWh62zyI-VxPVHFT6j1txfIAAnnPMRvQLIlXOdg7-3V4uPIBAAMCAAN5AAM2BA"

try:
    ID_GROUP_PROMO = int(os.getenv("ID_GROUP_PROMO"))
except (ValueError, TypeError):
    logger.error("Lỗi: ID_GROUP_PROMO không được đặt hoặc không phải là số trong file .env. Đặt giá trị mặc định là 0.")
    ID_GROUP_PROMO = 0 # Đặt một giá trị mặc định an toàn để bot không crash

try:
    ID_GROUP_LINK = int(os.getenv("ID_GROUP_LINK"))
except (ValueError, TypeError):
    logger.error("Lỗi: ID_GROUP_PROMO không được đặt hoặc không phải là số trong file .env. Đặt giá trị mặc định là 0.")
    ID_GROUP_ADMIN = 0


try:
    # Đọc ID của nhóm log lỗi từ biến môi trường
    LOG_GROUP_CHAT_ID = int(os.getenv("LOG_GROUP_CHAT_ID"))
    print(f"[DEBUG-CONFIG] LOG_GROUP_CHAT_ID has been set to: {LOG_GROUP_CHAT_ID}")
except (ValueError, TypeError):
    # Nếu không có, đặt về 0 và cảnh báo. Bot sẽ không gửi log lỗi.
    logger.warning("Cảnh báo: LOG_GROUP_CHAT_ID không được đặt trong file .env. Bot sẽ không gửi log lỗi đến Telegram.")
    LOG_GROUP_CHAT_ID = 0
    print(f"[DEBUG-CONFIG] lỗi LOG_GROUP_CHAT_ID has been set to: {LOG_GROUP_CHAT_ID}")

try:
    ID_GROUP_TRANSACTION = int(os.getenv("ID_GROUP_TRANSACTION"))
except (ValueError, TypeError):
    logger.warning("ID_GROUP_TRANSACTION không được đặt trong .env.")
    ID_GROUP_TRANSACTION = 0

try:
    ID_GROUP_KL007 = int(os.getenv("ID_GROUP_KL007"))
except (ValueError, TypeError):
    logger.warning("Cảnh báo: ID_GROUP_KL007 không được đặt trong file .env. Chức năng duyệt điểm KL007 có thể không hoạt động.")
    ID_GROUP_KL007 = 0 # Đặt giá trị mặc định an toàn

try:
    GA4_MEASUREMENT_ID =os.getenv("GA4_MEASUREMENT_ID")
except (ValueError, TypeError):
    logger.warning("GA4_MEASUREMENT_ID không được đặt trong .env.")


try:
    GA4_API_SECRET = os.getenv("GA4_API_SECRET")
except (ValueError, TypeError):
    logger.warning("GA4_API_SECRET không được đặt trong .env.")
