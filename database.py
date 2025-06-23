# Tệp: database.py
import sqlite3
import json
import uuid
import datetime
import logging
from contextlib import contextmanager

import config

logger = logging.getLogger(__name__)

@contextmanager
def db_connect():
    """Cung cấp một kết nối an toàn đến database."""
    conn = None
    try:
        conn = sqlite3.connect(config.DATABASE_FILE, check_same_thread=False)
        conn.row_factory = sqlite3.Row # Cho phép truy cập cột bằng tên
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Lỗi kết nối database: {e}")
    finally:
        if conn:
            conn.close()

def init_db():
    """Khởi tạo các bảng trong database nếu chúng chưa tồn tại."""
    with db_connect() as conn:
        cursor = conn.cursor()

        # Bảng người dùng
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            referral_code TEXT UNIQUE NOT NULL,
            share_count INTEGER DEFAULT 0,
            was_referred_by_user_id INTEGER,
            claimed_promos TEXT DEFAULT '{}',
            claimed_share_milestones TEXT DEFAULT '{}',
            created_at TEXT NOT NULL,
            pending_share_milestone_claim INTEGER DEFAULT NULL
        )""")

        # Bảng yêu cầu nạp tiền
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS deposit_requests (
            request_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            username TEXT,
            game_username TEXT NOT NULL,
            photo_file_id TEXT NOT NULL,
            status TEXT NOT NULL,
            details TEXT DEFAULT '{}',
            created_at TEXT NOT NULL,
            processed_at TEXT
        )""")

        # Bảng yêu cầu rút tiền
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS withdrawal_requests (
            request_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            username TEXT,
            game_username TEXT NOT NULL,
            amount INTEGER NOT NULL,
            status TEXT NOT NULL,
            details TEXT DEFAULT '{}',
            created_at TEXT NOT NULL,
            processed_at TEXT
        )""")

        # Bảng yêu cầu khuyến mãi
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS promotion_requests (
            request_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            username TEXT,
            game_username TEXT NOT NULL,
            promo_code TEXT NOT NULL,
            status TEXT NOT NULL,
            details TEXT DEFAULT '{}',
            created_at TEXT NOT NULL,
            processed_at TEXT
        )""")

        # Bảng yêu cầu chia sẻ MỚI
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS share_requests (
            request_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            username TEXT,
            game_username TEXT NOT NULL,
            milestone INTEGER NOT NULL,
            status TEXT NOT NULL,
            details TEXT DEFAULT '{}',
            created_at TEXT NOT NULL,
            processed_at TEXT
        )""")

        conn.commit()
        logger.info("✅ Database đã được khởi tạo/cập nhật thành công.")

def _row_to_dict(row):
    if row is None: return None
    return dict(row)

def _create_request(table_name, data):
    with db_connect() as conn:
        cursor = conn.cursor()
        data['created_at'] = datetime.datetime.now().isoformat()
        if 'details' in data and isinstance(data['details'], dict):
            data['details'] = json.dumps(data['details'])

        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data.values()])
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        try:
            cursor.execute(query, tuple(data.values()))
            conn.commit()
            logger.info(f"Yêu cầu {table_name} mới đã được tạo: {data.get('request_id')}")
            return True
        except sqlite3.IntegrityError as e:
            logger.error(f"Lỗi khi tạo yêu cầu {table_name}: {e} (Có thể trùng request_id)")
            return False

def _get_request(table_name, request_id):
    with db_connect() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name} WHERE request_id = ?", (request_id,))
        row = cursor.fetchone()
        if row:
            req_dict = _row_to_dict(row)
            if 'details' in req_dict and req_dict['details']:
                req_dict['details'] = json.loads(req_dict['details'])
            else:
                req_dict['details'] = {}
            return req_dict
        return None

def _update_request(table_name, request_id, updates):
    with db_connect() as conn:
        cursor = conn.cursor()
        updates['processed_at'] = datetime.datetime.now().isoformat()
        if 'details' in updates and isinstance(updates['details'], dict):
            updates['details'] = json.dumps(updates['details'])

        set_clause = ", ".join([f"{key} = ?" for key in updates])
        values = list(updates.values()) + [request_id]
        query = f"UPDATE {table_name} SET {set_clause} WHERE request_id = ?"
        cursor.execute(query, tuple(values))
        conn.commit()
        return True

# Convenience functions for deposit
def create_deposit_request(data):
    return _create_request('deposit_requests', data)

def get_deposit_request(request_id):
    return _get_request('deposit_requests', request_id)

def update_deposit_request(request_id, updates):
    return _update_request('deposit_requests', request_id, updates)

# Convenience functions for withdrawal
def create_withdrawal_request(data):
    return _create_request('withdrawal_requests', data)

def get_withdrawal_request(request_id):
    return _get_request('withdrawal_requests', request_id)

def update_withdrawal_request(request_id, updates):
    return _update_request('withdrawal_requests', request_id, updates)

# Convenience functions for promotion
def create_promotion_request(data):
    return _create_request('promotion_requests', data)

def get_promotion_request(request_id):
    return _get_request('promotion_requests', request_id)

def update_promotion_request(request_id, updates):
    return _update_request('promotion_requests', request_id, updates)

# Convenience functions for share requests MỚI
def create_share_request(data):
    return _create_request('share_requests', data)

def get_share_request(request_id):
    return _get_request('share_requests', request_id)

def update_share_request(request_id, updates):
    return _update_request('share_requests', request_id, updates)

# Existing user functions
def get_user_data(user_id):
    with db_connect() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user_data = _row_to_dict(cursor.fetchone())
        if user_data:
            user_data['claimed_promos'] = json.loads(user_data.get('claimed_promos', '{}'))
            user_data['claimed_share_milestones'] = json.loads(user_data.get('claimed_share_milestones', '{}'))
        return user_data

def create_user(user_id, referral_code, was_referred_by_user_id=None):
    with db_connect() as conn:
        cursor = conn.cursor()
        new_user = {
            "user_id": user_id,
            "referral_code": referral_code,
            "share_count": 0,
            "was_referred_by_user_id": was_referred_by_user_id,
            "claimed_promos": json.dumps({}),
            "claimed_share_milestones": json.dumps({}),
            "pending_share_milestone_claim": None,
            "created_at": datetime.datetime.now().isoformat(),
            'pending_share_milestone_claim': None
        }
        cursor.execute("""
        INSERT INTO users (user_id, referral_code, share_count, was_referred_by_user_id,
                           claimed_promos, claimed_share_milestones, created_at, pending_share_milestone_claim)
        VALUES (:user_id, :referral_code, :share_count, :was_referred_by_user_id,
                :claimed_promos, :claimed_share_milestones, :created_at, :pending_share_milestone_claim)
        """, new_user) # <<< ĐÃ SỬA LẠI CÂU LỆNH INSERT
        conn.commit()
        logger.info(f"Tạo người dùng mới trong SQLite: {user_id}")
        new_user['claimed_promos'] = {}
        new_user['claimed_share_milestones'] = {}
        return new_user

def update_user_data(user_id, updates):
    with db_connect() as conn:
        cursor = conn.cursor()

        for key in ['claimed_promos', 'claimed_share_milestones']:
            if key in updates and isinstance(updates[key], (dict, list)):
                updates[key] = json.dumps(updates[key])

        set_clause = ", ".join([f"{key} = ?" for key in updates])
        values = list(updates.values()) + [user_id]

        query = f"UPDATE users SET {set_clause} WHERE user_id = ?"
        cursor.execute(query, tuple(values))
        conn.commit()
        return True

def get_user_id_by_referral_code(referral_code):
    with db_connect() as conn:
        cursor = conn.cre.fetchone()
        return row['user_id'] if row else None

def get_current_time_str():
    """Lấy thời gian hiện tại theo định dạng ISO 8601."""
    return datetime.now(TIMEZONE).isoformat()