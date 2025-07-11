# core/database.py
import secrets
import sqlite3
import logging
import json
import uuid
import aiosqlite
from config import DB_PATH

# Cấu hình logging
logger = logging.getLogger(__name__)
DB_FILE = 'klbot.db'


async def get_connection():
    return await aiosqlite.connect(DB_PATH)

def get_db_connection():
    """
    Tạo kết nối tới CSDL SQLite.
    Kết nối sẽ trả về các hàng dưới dạng dictionary-like objects.
    """
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    except sqlite3.Error as e:
        logger.critical(f"Lỗi kết nối cơ sở dữ liệu: {e}", exc_info=True)
        raise

def init_db():
    """
    Khởi tạo các bảng trong CSDL nếu chúng chưa tồn tại.
    Hàm này được thiết kế để chỉ lưu trữ dữ liệu tối thiểu cần thiết.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        logger.info("Đang khởi tạo cơ sở dữ liệu...")

        # Bảng `users` chỉ lưu dữ liệu cần thiết cho tính năng chia sẻ.
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT NOT NULL,
            username TEXT,
            referral_code TEXT NOT NULL UNIQUE,
            share_count INTEGER NOT NULL DEFAULT 0,
            referred_by_user_id INTEGER,
            claimed_milestones TEXT, -- Lưu các mốc đã nhận dưới dạng JSON list, ví dụ: '[15, 30]'
            FOREIGN KEY (referred_by_user_id) REFERENCES users (user_id)
        );
        """)

        # Bảng `promo_claims` hoạt động như một hàng đợi tạm thời.
        # Bản ghi sẽ bị xóa ngay sau khi được xử lý.
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS promo_claims (
            claim_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            promo_code TEXT NOT NULL,
            game_username TEXT,
            details TEXT, -- Dữ liệu bổ sung dưới dạng JSON, ví dụ: thành viên nhóm KL006
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        );
        """)

        # Bảng `share_milestone_claims` cũng là hàng đợi tạm thời.
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS share_milestone_claims (
            claim_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            milestone INTEGER NOT NULL,
            game_username TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        );
        """)

        conn.commit()
        logger.info("Cơ sở dữ liệu đã được kiểm tra và khởi tạo thành công.")
    finally:
        conn.close()

# =========== HÀM THAO TÁC VỚI USERS ===========

def get_or_create_user(user_id: int, first_name: str = None, username: str = None):
    """
    Lấy thông tin người dùng. Nếu chưa tồn tại, tạo mới và trả về.
    first_name và username là tùy chọn, hữu ích khi chỉ muốn lấy thông tin.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()

        if user:
            # Nếu người dùng đã tồn tại, chỉ cần trả về thông tin của họ
            return dict(user)
        else:
            # === LOGIC TẠO NGƯỜI DÙNG MỚI ===

            # 1. Đặt giá trị mặc định cho first_name NẾU nó không được cung cấp
            if not first_name:
                first_name = f"User {user_id}"

            # 2. Tạo mã giới thiệu duy nhất
            ref_code = str(uuid.uuid4())[:8]
            # Vòng lặp while để đảm bảo mã là duy nhất (logic này đã tốt)
            cursor.execute("SELECT 1 FROM users WHERE referral_code = ?", (ref_code,))
            while cursor.fetchone():
                ref_code = str(uuid.uuid4())[:8]
                cursor.execute("SELECT 1 FROM users WHERE referral_code = ?", (ref_code,))

            # 3. Thêm người dùng mới vào database
            cursor.execute(
                "INSERT INTO users (user_id, first_name, username, referral_code, claimed_milestones) VALUES (?, ?, ?, ?, ?)",
                (user_id, first_name, username, ref_code, json.dumps([]))
            )
            conn.commit()
            logger.info(f"Người dùng mới đã được tạo: ID {user_id}, Tên {first_name}")

            # 4. Lấy lại thông tin người dùng vừa tạo và trả về
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            return dict(cursor.fetchone())

    finally:
        if conn:
            conn.close()

def set_referrer(user_id: int, referrer_id: int) -> bool:
    """Gán người giới thiệu cho user và tăng điểm cho người giới thiệu."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Chỉ cập nhật nếu user chưa có người giới thiệu
        cursor.execute(
            "UPDATE users SET referred_by_user_id = ? WHERE user_id = ? AND referred_by_user_id IS NULL",
            (referrer_id, user_id)
        )
        if cursor.rowcount > 0:
            # Tăng điểm cho người giới thiệu
            cursor.execute("UPDATE users SET share_count = share_count + 1 WHERE user_id = ?", (referrer_id,))
            conn.commit()
            logger.info(f"User {user_id} đã được gán người giới thiệu là {referrer_id}. Lượt chia sẻ của người giới thiệu đã được tăng.")
            return True
        return False
    finally:
        conn.close()


# =========== HÀM XỬ LÝ HÀNG ĐỢI KHUYẾN MÃI (PROMO) ===========

def add_promo_claim(user_id: int, promo_code: str, game_username: str, details: dict = None) -> int:
    """Thêm một yêu cầu khuyến mãi vào hàng đợi tạm thời."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        details_json = json.dumps(details) if details else None
        cursor.execute(
            "INSERT INTO promo_claims (user_id, promo_code, game_username, details) VALUES (?, ?, ?, ?)",
            (user_id, promo_code, game_username, details_json)
        )
        claim_id = cursor.lastrowid
        conn.commit()
        logger.info(f"User {user_id} đã thêm yêu cầu KM '{promo_code}' (ID: {claim_id}) vào hàng đợi.")
        return claim_id
    finally:
        conn.close()

def get_promo_claim(claim_id: int):
    """Lấy thông tin một yêu cầu khuyến mãi từ hàng đợi."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM promo_claims WHERE claim_id = ?", (claim_id,))
        claim = cursor.fetchone()
        return dict(claim) if claim else None
    finally:
        conn.close()

def delete_promo_claim(claim_id: int):
    """Xóa một yêu cầu khuyến mãi khỏi hàng đợi sau khi đã xử lý."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM promo_claims WHERE claim_id = ?", (claim_id,))
        conn.commit()
        logger.info(f"Yêu cầu KM ID {claim_id} đã được xử lý và xóa khỏi hàng đợi.")
    finally:
        conn.close()

# =========== HÀM XỬ LÝ HÀNG ĐỢI MỐC CHIA SẺ (SHARE MILESTONE) ===========

def add_share_claim(user_id: int, milestone: int, game_username: str) -> int:
    """Thêm yêu cầu nhận thưởng mốc chia sẻ vào hàng đợi."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO share_milestone_claims (user_id, milestone, game_username) VALUES (?, ?, ?)",
            (user_id, milestone, game_username)
        )
        claim_id = cursor.lastrowid
        conn.commit()
        logger.info(f"User {user_id} đã yêu cầu nhận mốc {milestone} (Claim ID: {claim_id}).")
        return claim_id
    finally:
        conn.close()

def get_share_claim(claim_id: int):
    """Lấy thông tin yêu cầu mốc chia sẻ từ hàng đợi."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM share_milestone_claims WHERE claim_id = ?", (claim_id,))
        claim = cursor.fetchone()
        return dict(claim) if claim else None
    finally:
        conn.close()

def process_approved_share_claim(claim_id: int):
    """
    Xử lý khi admin DUYỆT yêu cầu: ghi nhận mốc đã nhận và xóa yêu cầu khỏi hàng đợi.
    """
    claim_data = get_share_claim(claim_id)
    if not claim_data:
        logger.warning(f"Không tìm thấy yêu cầu mốc chia sẻ ID {claim_id} để xử lý.")
        return

    user_id = claim_data['user_id']
    milestone = claim_data['milestone']

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Lấy danh sách các mốc đã nhận hiện tại
        cursor.execute("SELECT claimed_milestones FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        claimed_list = json.loads(result['claimed_milestones']) if result and result['claimed_milestones'] else []

        # Thêm mốc mới nếu chưa có
        if milestone not in claimed_list:
            claimed_list.append(milestone)
            claimed_list.sort()
            # Cập nhật lại vào CSDL
            cursor.execute(
                "UPDATE users SET claimed_milestones = ? WHERE user_id = ?",
                (json.dumps(claimed_list), user_id)
            )
            logger.info(f"User {user_id} đã được ghi nhận hoàn thành mốc chia sẻ {milestone}.")

        # Xóa yêu cầu khỏi hàng đợi
        cursor.execute("DELETE FROM share_milestone_claims WHERE claim_id = ?", (claim_id,))
        conn.commit()
        logger.info(f"Yêu cầu mốc chia sẻ ID {claim_id} đã được duyệt và xóa.")
    finally:
        conn.close()

def delete_share_claim(claim_id: int):
    """
    Xóa yêu cầu khỏi hàng đợi (dùng khi admin TỪ CHỐI).
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM share_milestone_claims WHERE claim_id = ?", (claim_id,))
        conn.commit()
        logger.info(f"Yêu cầu mốc chia sẻ ID {claim_id} đã bị từ chối và xóa.")
    finally:
        conn.close()


async def add_shares_to_user(user_id: int, shares_delta: int) -> tuple[bool, int]:
    """
    Cộng hoặc trừ lượt chia sẻ cho người dùng.
    Nếu người dùng chưa có, sẽ tự động tạo mới trước khi thay đổi.
    """
    if shares_delta == 0:
        return False, -1

    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # 1. Đảm bảo người dùng tồn tại bằng cách gọi get_or_create_user
        # LƯU Ý: Chúng ta cần thông tin first_name. Lệnh admin không có thông tin này.
        # Chúng ta sẽ tạm thời dùng một tên mặc định nếu phải tạo mới.

        # Kiểm tra trước
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user_record = cursor.fetchone()

        if not user_record:
            # Nếu không có, tạo mới với tên mặc định. Admin có thể sửa sau nếu cần.
            # Bạn cần lấy first_name và username từ đâu đó hoặc dùng giá trị mặc định.
            # Vì lệnh này admin dùng, bot không biết tên người dùng.
            # Chúng ta sẽ tạo một người dùng "tạm"
            logger.warning(f"User {user_id} not found. Creating a temporary user record to add shares.")
            # Tạo mã giới thiệu duy nhất
            ref_code = str(uuid.uuid4())[:8]
            cursor.execute("SELECT 1 FROM users WHERE referral_code = ?", (ref_code,))
            while cursor.fetchone():
                ref_code = str(uuid.uuid4())[:8]

            cursor.execute(
                "INSERT INTO users (user_id, first_name, username, referral_code, claimed_milestones) VALUES (?, ?, ?, ?, ?)",
                (user_id, f"User {user_id}", None, ref_code, json.dumps([]))
            )
            # Lấy lại bản ghi vừa tạo
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user_record = cursor.fetchone()

        current_shares = user_record['share_count']

        # 2. Tính toán giá trị mới
        new_total = max(0, current_shares + shares_delta)

        # 3. Cập nhật
        cursor.execute(
            "UPDATE users SET share_count = ? WHERE user_id = ?",
            (new_total, user_id)
        )
        conn.commit()

        logger.info(f"Admin changed shares for user {user_id} by {shares_delta}. Old: {current_shares}, New: {new_total}")
        return True, new_total

    except Exception as e:
        logger.error(f"Failed to update share_count for user {user_id} in database: {e}")
        return False, -1
    finally:
        if conn:
            conn.close()

def get_user_by_referral_code(ref_code: str):
    """
    Tìm người dùng dựa trên mã giới thiệu (referral_code).

    Args:
        ref_code (str): Mã giới thiệu cần tìm.

    Returns:
        dict: Một dictionary chứa thông tin người dùng nếu tìm thấy,
              nếu không thì trả về None.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE referral_code = ?", (ref_code,))
        user = cursor.fetchone()

        return dict(user) if user else None

    except Exception as e:
        logger.error(f"Lỗi khi tìm người dùng bằng mã giới thiệu '{ref_code}': {e}")
        return None
    finally:
        if conn:
            conn.close()


def get_user_by_id(user_id: int):
    """
    Tìm người dùng dựa trên user_id.

    Args:
        user_id (int): ID của người dùng Telegram cần tìm.

    Returns:
        dict: Một dictionary chứa thông tin người dùng nếu tìm thấy,
              nếu không thì trả về None.
    """
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()

        return dict(user) if user else None

    except Exception as e:
        logger.error(f"Lỗi khi tìm người dùng bằng ID '{user_id}': {e}")
        return None
    finally:
        if conn:
            conn.close()