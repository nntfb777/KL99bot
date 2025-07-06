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
kl007_user_cache = TTLCache(maxsize=2000, ttl=300)

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
# === LOGIC CHO KL007 (Cache từng yêu cầu) ===
# =======================================================

@cached(kl007_user_cache)
def _find_user_in_kl007_sheet(username: str, worksheet_name: str) -> dict:
    """
    Hàm được cache: Tìm một username cụ thể trong worksheet KL007.
    Chỉ gọi API nếu cặp (username, worksheet_name) chưa có trong cache.
    Trả về một dict có key 'found' để cache cả trường hợp không tìm thấy.
    """
    logger.info(f"CACHE MISS (KL007): Đang tìm kiếm '{username}' trong worksheet '{worksheet_name}'...")
    try:
        client = _get_gspread_client()
        spreadsheet = client.open("KL007 - SIÊU TIỀN THƯỞNG")
        worksheet = spreadsheet.worksheet(worksheet_name)
        cell = worksheet.find(username, in_column=1)

        if not cell:
            return {'found': False}

        row_values = worksheet.row_values(cell.row)
        user_data = {
            'found': True,
            'username': row_values[0] if len(row_values) > 0 else '',
            'bet_ticket': row_values[1] if len(row_values) > 1 else '',
            'reward': row_values[2] if len(row_values) > 2 else '',
            'status': row_values[3] if len(row_values) > 3 else ''
        }
        return user_data

    except (gspread.exceptions.SpreadsheetNotFound, gspread.exceptions.WorksheetNotFound, gspread.exceptions.CellNotFound):
        logger.warning(f"Không tìm thấy sheet/cell khi tìm kiếm KL007 cho '{username}' trong '{worksheet_name}'.")
        return {'found': False}
    except Exception as e:
        logger.error(f"Lỗi API khi tìm kiếm KL007 cho '{username}': {e}")
        # Không trả về gì để không cache lỗi hệ thống
        raise e

def get_kl007_data(username: str, date_str: str) -> dict | None:
    """Giao diện công khai để lấy dữ liệu KL007, sử dụng cache cho từng user."""
    if not date_str or not username: return None
    
    try:
        worksheet_name = date_str[:5]
        result = _find_user_in_kl007_sheet(username, worksheet_name)
        
        # Chỉ trả về dữ liệu nếu 'found' là True
        return result if result and result.get('found') else None
    except Exception as e:
        # Bắt lỗi từ _find_user_in_kl007_sheet để hàm gọi không bị crash
        logger.error(f"Lỗi cuối cùng trong get_kl007_data: {e}")
        return None

# =======================================================
# === LOGIC CHO KL006 (Cache toàn bộ sheet) ===
# =======================================================

@cached(kl006_sheet_cache)
def _read_kl006_sheet_as_map() -> dict:
    """Hàm được cache: Đọc toàn bộ sheet KL006 và tạo map để tra cứu nhanh."""
    logger.info("CACHE MISS (KL006): Đang đọc toàn bộ sheet 'KM KL006'...")
    try:
        client = _get_gspread_client()
        spreadsheet = client.open("Lưu Trình KL99")
        worksheet = spreadsheet.worksheet("KM KL006")
        all_values = worksheet.get_all_values()[1:]
        
        username_to_row_map = {}
        for i, row in enumerate(all_values):
            usernames_in_row = [name for name in (row[0:3] + row[4:9]) if name]
            for name in usernames_in_row:
                username_to_row_map[name.lower()] = i # Lưu username chữ thường để tìm kiếm không phân biệt hoa/thường
        return username_to_row_map
    except Exception as e:
        logger.error(f"Lỗi khi đọc sheet KL006: {e}", exc_info=True)
        return {}

def find_kl006_group(usernames: list[str]) -> tuple[bool, str]:
    """Kiểm tra nhóm KL006, sử dụng cache toàn bộ sheet."""
    if not usernames: return False, "Danh sách thành viên rỗng."
    
    try:
        username_to_row_map = _read_kl006_sheet_as_map()
        if not username_to_row_map:
            return False, "Không thể đọc dữ liệu nhóm KL006 từ Google Sheet."

        found_row_indices = set()
        for username in usernames:
            row_index = username_to_row_map.get(username.lower()) # Tìm kiếm bằng chữ thường
            if row_index is None:
                return False, f"Thành viên '{username}' chưa được đăng ký."
            found_row_indices.add(row_index)

        if len(found_row_indices) == 1:
            return True, ""
        else:
            return False, "Các thành viên không cùng nhóm."
    except Exception as e:
        logger.error(f"Lỗi khi kiểm tra nhóm KL006: {e}", exc_info=True)
        return False, "Lỗi hệ thống khi kiểm tra nhóm."