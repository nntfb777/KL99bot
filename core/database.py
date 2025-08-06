# core/database.py
import secrets
import logging
import json
import uuid
import aiosqlite
from config import DB_PATH
from typing import List

# Cấu hình logging
logger = logging.getLogger(__name__)
DB_FILE = 'klbot.db'




async def init_db(): # <<--- THAY ĐỔI 1: CHUYỂN THÀNH ASYNC
    """
    (Async) Khởi tạo các bảng trong CSDL nếu chúng chưa tồn tại.
    """
    # <<--- THAY ĐỔI 2: SỬ DỤNG AIOSQLITE ---
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("PRAGMA journal_mode=WAL;")
        logger.info("Đang khởi tạo cơ sở dữ liệu (async)...")

        # Bảng `users`
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            first_name TEXT NOT NULL,
            username TEXT,
            referral_code TEXT NOT NULL UNIQUE,
            share_count INTEGER NOT NULL DEFAULT 0,
            referred_by_user_id INTEGER,
            claimed_milestones TEXT,
            FOREIGN KEY (referred_by_user_id) REFERENCES users (user_id)
        );
        """)

        # Bảng `promo_claims`
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS promo_claims (
            claim_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            promo_code TEXT NOT NULL,
            game_username TEXT,
            details TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        );
        """)

        # Bảng `user_requests`
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS user_requests (
            user_id TEXT PRIMARY KEY,
            promo_count INTEGER NOT NULL DEFAULT 0,
            transaction_count INTEGER NOT NULL DEFAULT 0,
            date TEXT NOT NULL
        );
        """)

        await conn.commit()
        logger.info("Cơ sở dữ liệu đã được kiểm tra và khởi tạo thành công.")

# =========== HÀM THAO TÁC VỚI USERS ===========

# core/database.py

async def get_or_create_user(user_id: int, first_name: str = None, username: str = None) -> dict:
    """(Async) Lấy hoặc tạo người dùng mới, với các bước debug."""
    # ===== BƯỚC 1: XÁC NHẬN HÀM ĐÃ ĐƯỢC GỌI =====

    try:
        # ===== BƯỚC 2: KẾT NỐI DATABASE =====
        async with aiosqlite.connect(DB_PATH) as conn:
            await conn.execute("PRAGMA journal_mode=WAL;")
            conn.row_factory = aiosqlite.Row
            cursor = await conn.cursor()

            try:
                # ===== BƯỚC 5: THỰC THI SELECT =====
                await cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                user = await cursor.fetchone()

                if user:
                    return dict(user)

                # ===== BƯỚC 8: TẠO USER MỚI =====
                ref_code = str(uuid.uuid4())[:8]

                await cursor.execute(
                    "INSERT INTO users (user_id, first_name, username, referral_code, claimed_milestones) VALUES (?, ?, ?, ?, ?)",
                    (user_id, first_name or f"User {user_id}", username, ref_code, json.dumps([]))
                )
                await conn.commit()

                await cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                new_user = await cursor.fetchone()
                return dict(new_user)
            finally:
                await cursor.close()

    except Exception as e:
        print(f"--- !!! LỖI NGHIÊM TRỌNG TRONG `get_or_create_user`: {type(e).__name__} - {e} !!! ---")
        logger.error(f"Lỗi trong `get_or_create_user`: {e}", exc_info=True)
        print("="*58 + "\n\n")
        raise e # Ném lỗi ra ngoài để biết


async def set_referrer(user_id: int, referrer_id: int) -> bool:
    """(Async) Gán người giới thiệu và tăng share_count."""
    # `async with` sẽ tự động mở và đóng kết nối một cách an toàn
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("PRAGMA journal_mode=WAL;")
        cursor = await conn.cursor()
        try:
            # `await` cho mỗi lệnh thực thi
            await cursor.execute(
                "UPDATE users SET referred_by_user_id = ? WHERE user_id = ? AND referred_by_user_id IS NULL",
                (referrer_id, user_id)
            )

            # `cursor.rowcount` vẫn hoạt động như cũ
            if cursor.rowcount > 0:
                await cursor.execute("UPDATE users SET share_count = share_count + 1 WHERE user_id = ?", (referrer_id,))
                await conn.commit() # `await` cho lệnh commit
                logger.info(f"User {user_id} đã được gán người giới thiệu là {referrer_id}. Lượt chia sẻ của người giới thiệu đã được tăng.")
                return True

            return False
        finally:
            # Luôn đóng con trỏ sau khi sử dụng xong
            await cursor.close()

async def record_claimed_milestone(user_id: int, milestone: int):
    """(Async) Ghi nhận một mốc đã nhận thưởng vào bảng users."""
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("PRAGMA journal_mode=WAL;")
        conn.row_factory = aiosqlite.Row
        cursor = await conn.cursor()
        try:
            await cursor.execute("SELECT claimed_milestones FROM users WHERE user_id = ?", (user_id,))
            result = await cursor.fetchone()

            claimed_list = json.loads(result['claimed_milestones']) if result and result['claimed_milestones'] else []

            if milestone not in claimed_list:
                claimed_list.append(milestone)
                claimed_list.sort()
                await cursor.execute(
                    "UPDATE users SET claimed_milestones = ? WHERE user_id = ?",
                    (json.dumps(claimed_list), user_id)
                )
                await conn.commit()
                logger.info(f"User {user_id} đã được ghi nhận hoàn thành mốc chia sẻ {milestone}.")
        finally:
            await cursor.close()

# =========== HÀM XỬ LÝ HÀNG ĐỢI KHUYẾN MÃI CHUNG ===========

async def add_promo_claim(user_id: int, promo_code: str, game_username: str = None, details: dict = None) -> int:
    """(Async) Thêm một yêu cầu khuyến mãi vào hàng đợi chung."""
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("PRAGMA journal_mode=WAL;")
        cursor = await conn.cursor()
        try:
            details_json = json.dumps(details) if details else None
            await cursor.execute(
                "INSERT INTO promo_claims (user_id, promo_code, game_username, details) VALUES (?, ?, ?, ?)",
                (user_id, promo_code, game_username, details_json)
            )
            claim_id = cursor.lastrowid
            await conn.commit()
            logger.info(f"User {user_id} đã thêm yêu cầu KM '{promo_code}' (ID: {claim_id}) vào hàng đợi.")
            return claim_id
        finally:
            await cursor.close()

async def get_promo_claim(claim_id: int) -> dict | None:
    """(Async) Lấy thông tin một yêu cầu khuyến mãi từ hàng đợi."""
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("PRAGMA journal_mode=WAL;")
        conn.row_factory = aiosqlite.Row
        cursor = await conn.cursor()
        try:
            await cursor.execute("SELECT * FROM promo_claims WHERE claim_id = ?", (claim_id,))
            claim = await cursor.fetchone()
            return dict(claim) if claim else None
        finally:
            await cursor.close()

async def delete_promo_claim(claim_id: int):
    """(Async) Xóa một yêu cầu khuyến mãi khỏi hàng đợi."""
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.cursor()
        try:
            await cursor.execute("DELETE FROM promo_claims WHERE claim_id = ?", (claim_id,))
            await conn.commit()
            logger.info(f"Yêu cầu KM ID {claim_id} đã được xử lý và xóa khỏi hàng đợi.")
        finally:
            await cursor.close()




async def process_approved_share_claim(claim_id: int) -> bool:
    """
    (An toàn hơn) Xử lý khi admin DUYỆT yêu cầu.
    Chỉ xử lý claim 'SHARING' và trả về True nếu thành công.
    """
    claim_data = await get_promo_claim(claim_id)
    if not claim_data:
        logger.warning(f"Không tìm thấy yêu cầu ID {claim_id} để xử lý.")
        return False

    # Đảm bảo chúng ta chỉ xử lý đúng loại claim
    if claim_data.get('promo_code') != 'SHARING':
        logger.error(f"process_approved_share_claim được gọi cho một claim không phải 'SHARING' (ID: {claim_id})")
        # Vẫn xóa claim để không bị kẹt, nhưng báo lỗi và trả về False
        await delete_promo_claim(claim_id)
        return False

    try:
        details = json.loads(claim_data.get('details', '{}'))
        milestone = details.get('milestone')
        user_id = claim_data.get('user_id')

        if milestone and user_id:
            await record_claimed_milestone(user_id, milestone)
            await delete_promo_claim(claim_id)
            logger.info(f"Yêu cầu chia sẻ ID {claim_id} đã được duyệt và xử lý thành công.")
            return True
        else:
            logger.error(f"Thiếu thông tin 'milestone' hoặc 'user_id' trong claim ID {claim_id}.")
            await delete_promo_claim(claim_id) # Vẫn xóa để không bị kẹt
            return False

    except (json.JSONDecodeError, KeyError) as e:
        logger.error(f"Lỗi khi xử lý details của claim ID {claim_id}: {e}")
        await delete_promo_claim(claim_id)
        return False

# =========== CÁC HÀM CŨ KHÁC (GIỮ LẠI NẾU CẦN) ===========
async def add_shares_to_user(user_id: int, shares_delta: int) -> tuple[bool, int]:
    """(Async) Thêm hoặc bớt thủ công lượt chia sẻ cho người dùng."""
    await get_or_create_user(user_id) # Đảm bảo user tồn tại
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("PRAGMA journal_mode=WAL;")
        conn.row_factory = aiosqlite.Row
        cursor = await conn.cursor()
        try:
            await cursor.execute("SELECT share_count FROM users WHERE user_id = ?", (user_id,))
            result = await cursor.fetchone()
            if not result:
                logger.error(f"Không thể tìm thấy user {user_id} để cập nhật share_count.")
                return False, -1

            current_shares = result['share_count']
            new_total = max(0, current_shares + shares_delta)

            await cursor.execute("UPDATE users SET share_count = ? WHERE user_id = ?", (new_total, user_id))
            await conn.commit()

            logger.info(f"Admin changed shares for user {user_id} by {shares_delta}. Old: {current_shares}, New: {new_total}")
            return True, new_total
        except Exception as e:
            logger.error(f"Lỗi khi cập nhật share_count cho user {user_id}: {e}", exc_info=True)
            return False, -1
        finally:
            await cursor.close()

async def get_user_by_referral_code(ref_code: str) -> dict | None:
    """(Async) Lấy thông tin người dùng bằng mã giới thiệu."""
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("PRAGMA journal_mode=WAL;")
        conn.row_factory = aiosqlite.Row
        cursor = await conn.cursor()
        try:
            await cursor.execute("SELECT * FROM users WHERE referral_code = ?", (ref_code,))
            user = await cursor.fetchone()
            return dict(user) if user else None
        finally:
            await cursor.close()

async def get_user_by_id(user_id: int) -> dict | None:
    """(Async) Lấy thông tin người dùng bằng ID."""
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("PRAGMA journal_mode=WAL;")
        conn.row_factory = aiosqlite.Row
        cursor = await conn.cursor()
        try:
            await cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = await cursor.fetchone()
            return dict(user) if user else None
        finally:
            await cursor.close()




async def has_pending_share_claim(user_id: int) -> bool:
    """
    (Async) Kiểm tra xem người dùng có yêu cầu thưởng chia sẻ đang chờ không.
    """
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("PRAGMA journal_mode=WAL;")
        cursor = await conn.cursor()
        try:
            await cursor.execute(
                "SELECT 1 FROM promo_claims WHERE user_id = ? AND promo_code = 'SHARING' LIMIT 1",
                (user_id,)
            )
            result = await cursor.fetchone()
            return bool(result)
        finally:
            await cursor.close()




async def clear_all_claims_for_user(user_id: int) -> int:
    """
    (Async) Xóa TẤT CẢ các yêu cầu trong bảng promo_claims cho một user_id cụ thể.
    """
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("PRAGMA journal_mode=WAL;")
        cursor = await conn.cursor()
        try:
            await cursor.execute("DELETE FROM promo_claims WHERE user_id = ?", (user_id,))
            deleted_count = cursor.rowcount
            await conn.commit()
            if deleted_count > 0:
                logger.info(f"Đã xóa {deleted_count} yêu cầu khỏi promo_claims cho user_id {user_id} bằng lệnh admin.")
            return deleted_count
        finally:
            await cursor.close()


async def get_all_pending_claims() -> List[dict]:
    """
    (Async) Lấy tất cả các yêu cầu đang ở trạng thái 'pending' từ CSDL.
    """
    async with aiosqlite.connect(DB_PATH) as conn:
        conn.row_factory = aiosqlite.Row
        cursor = await conn.cursor()
        try:
            # Giả sử bạn đã có cột `status` với giá trị mặc định là 'pending'
            await cursor.execute("SELECT * FROM promo_claims WHERE status = 'pending'")
            claims = await cursor.fetchall()
            # Chuyển đổi list các aiosqlite.Row thành list các dict
            return [dict(row) for row in claims]
        finally:
            await cursor.close()


