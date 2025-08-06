 #utils/gspread_api.py (Phiên bản cuối cùng, tối ưu hóa)

import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from cachetools import cached, TTLCache

logger = logging.getLogger(__name__)

# --- CẤU HÌNH ---
SCOPE = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
CREDS_FILE = 'google_credentials.json'

# --- BỘ NHỚ ĐỆM (CACHE) ---
# Cache cho kết quả tìm kiếm của từng user trong KL007
# Giữ kết quả trong 5 phút (300 giây), có thể lưu tới 2000 user khác nhau
kl007_user_cache = TTLCache(maxsize=10000, ttl=30)

# Cache cho toàn bộ sheet KL006
# Giữ kết quả trong 5 phút (300 giây)
kl006_sheet_cache = TTLCache(maxsize=2, ttl=300)

# --- HÀM KẾT NỐI (Tối ưu hóa) ---
_client = None
def _get_gspread_client():
    """Tạo hoặc trả về đối tượng client gspread đã được xác thực."""
    global _client
    if _client is None:
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
            _client = gspread.authorize(creds)
            logger.info("Đã xác thực thành công với Google Sheets API.")
        except FileNotFoundError:
            logger.error(f"Lỗi: Không tìm thấy file credentials '{CREDS_FILE}'.")
            raise
        except Exception as e:
            logger.error(f"Không thể xác thực với Google API: {e}", exc_info=True)
            raise
    return _client

# =======================================================
# === LOGIC CHO KL007 ===
# =======================================================


@cached(kl007_user_cache)
def _read_kl007_sheet(worksheet_name: str) -> dict:
    """
    Hàm được cache: Đọc toàn bộ dữ liệu của một worksheet KL007 (theo ngày)
    và tạo map {username_lower: data} để tra cứu nhanh.
    Sử dụng cache kl007_user_cache hiện có.
    """
    logger.info(f"CACHE MISS (KL007 Sheet): Đang đọc toàn bộ sheet '{worksheet_name}'...")
    try:
        client = _get_gspread_client()
        spreadsheet = client.open("KL007 - SIÊU TIỀN THƯỞNG")
        worksheet = spreadsheet.worksheet(worksheet_name)
        all_values = worksheet.get_all_values()[1:]

        username_to_data_map = {}
        for row in all_values:
            if len(row) > 0 and row[0]:
                username = row[0]
                username_to_data_map[username.lower()] = {
                    'username': username,
                    'bet_ticket': row[1] if len(row) > 1 else '',
                    'reward': row[2] if len(row) > 2 else '',
                    'status': row[3] if len(row) > 3 else ''
                }
        return username_to_data_map
    except gspread.exceptions.WorksheetNotFound:
        logger.warning(f"Không tìm thấy sheet '{worksheet_name}' trong file KL007.")
        return {}
    except Exception as e:
        logger.error(f"Lỗi API khi đọc sheet KL007 '{worksheet_name}': {e}")
        raise e

def get_kl007_data(username: str, date_str: str) -> dict | None:
    """
    Giao diện công khai để lấy dữ liệu KL007.
    Sử dụng mô hình cache toàn trang tính để tối ưu hiệu suất.
    """
    if not date_str or not username:
        return None

    try:
        worksheet_name = date_str[:5]

        # 1. Gọi hàm để lấy toàn bộ dữ liệu của sheet từ cache
        sheet_data_map = _read_kl007_sheet(worksheet_name)

        # 2. Tra cứu username (chữ thường) trong map dữ liệu đã cache
        return sheet_data_map.get(username.lower())

    except Exception as e:
        logger.error(f"Lỗi cuối cùng trong get_kl007_data cho '{username}': {e}")
        return None



# =======================================================
# === LOGIC CHO KL006 ===
# =======================================================
def _parse_bet_amount_gsheet(value_str: str) -> float:
    """Helper: Chuyển đổi chuỗi số có dấu phẩy của Google Sheet thành số float."""
    if not isinstance(value_str, str) or not value_str:
        return 0.0
    return float(value_str.replace('.', '').replace(',', '.'))

@cached(kl006_sheet_cache)
def _read_kl006_sheet_as_map() -> dict:
    """
    Hàm được cache: Đọc sheet 'Thưởng nhóm 3', tạo map từ username tới dữ liệu nhóm.
    Lưu cược của thành viên dưới dạng dictionary {tên: cược} để xử lý thứ tự ngẫu nhiên.
    """
    logger.info("CACHE MISS (KL006 - Thưởng nhóm 3): Đang đọc sheet 'Thưởng nhóm 3'...")
    try:
        client = _get_gspread_client()
        spreadsheet = client.open("Lưu Trình KL99")
        worksheet = spreadsheet.worksheet("Thưởng nhóm 3")
        all_values = worksheet.get_all_values()[1:]

        username_to_row_data_map = {}
        for i, row in enumerate(all_values):
            if len(row) < 7: continue

            original_members = [name.strip() for name in row[0].split(',') if name.strip()]
            lowercase_members = [name.lower() for name in original_members]
            bets = [_parse_bet_amount_gsheet(bet) for bet in row[1:4]]

            member_bets_map = {}
            if len(lowercase_members) == len(bets):
                 member_bets_map = dict(zip(lowercase_members, bets))

            row_data = {
                "original_members": original_members,
                "lowercase_members_set": set(lowercase_members),
                "member_bets": member_bets_map,
                "eligibility": row[4].strip(),
                "bonus": row[5].strip(),
                "claimed_status": row[6].strip()
            }

            for name_lower in lowercase_members:
                username_to_row_data_map[name_lower] = row_data

        return username_to_row_data_map
    except Exception as e:
        logger.error(f"Lỗi khi đọc sheet 'Thưởng nhóm 3': {e}", exc_info=True)
        return {}

def get_kl006_team_status_from_cache(username: str) -> dict | None:
    """HÀM MỚI: Tra cứu trạng thái chi tiết của nhóm cho một user từ dữ liệu cache của sheet 'Thưởng nhóm 3'."""
    try:
        all_groups_data_map = _read_kl006_sheet_as_map()
        return all_groups_data_map.get(username.lower())
    except Exception as e:
        logger.error(f"Lỗi khi tra cứu trạng thái KL006 cho user '{username}': {e}", exc_info=True)
        return None