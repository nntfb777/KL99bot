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

# Tên hiển thị bạn muốn đặt cho bot
BOT_DISPLAY_NAME = "KL99 - Đẳng Cấp Hàng Đầu Châu Á!"

# Các mốc chia sẻ và số tiền thưởng
SHARE_MILESTONES = [15, 30, 50, 100]

# Bạn có thể lấy File ID bằng cách gửi ảnh cho bot và dùng lệnh /getid (nếu bạn đã implement)
# hoặc dùng hàm get_file_id_handler trong handlers/utils.py
START_IMAGE_FILE_ID = "AgACAgUAAxkBAAIHMWho1E3K6PhGU6MW8CksYWduIVFdAAISxDEbVz9IV0CguZpfUdkQAQADAgADeAADNgQ"
PROMO_KL001_IMAGE_ID = "AgACAgUAAxkBAAICg2g-Mt3D4jR3CW2HjTB9pvt-B2GjAAK2wTEbhgHwVaax8wABZYXQngEAAwIAA3MAAzYE"
PROMO_KL006_IMAGE_ID = "AgACAgUAAxkBAAIHK2ho08XJrnhpQx5RYGkQv65mzuZ1AAILxDEbVz9IV79-jYJtNslTAQADAgADeAADNgQ"
PROMO_KL007_IMAGE_ID = "AgACAgUAAxkBAAIHLmho0-HoawSU9gTF6XOA0nonQYuXAAINxDEbVz9IV5DQ2gmCV3OVAQADAgADeAADNgQ"

try:
    ID_GROUP_PROMO = int(os.getenv("ID_GROUP_PROMO"))
except (ValueError, TypeError):
    logger.error("Lỗi: ID_GROUP_PROMO không được đặt hoặc không phải là số trong file .env. Đặt giá trị mặc định là 0.")
    ID_GROUP_PROMO = 0 # Đặt một giá trị mặc định an toàn để bot không crash

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