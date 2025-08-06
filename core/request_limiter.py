import sqlite3
import threading
import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from pytz import timezone
from config import DB_PATH
# ======== CẤU HÌNH ========
FLUSH_INTERVAL = 120  # Giây (2 phút)
PROMO_LIMIT = 5
TRANSACTION_LIMIT = 5

# ======== RAM CACHE =========
request_cache = {}
cache_lock = threading.Lock()

# ======== TIỆN ÍCH =========
def get_today():
    return datetime.now().strftime("%Y-%m-%d")

# ======== 1. TĂNG LƯỢT TRONG CACHE (CHỈ SAU GỬI THÀNH CÔNG) ========
def increment_count_in_cache(user_id, action_type):
    user_id = str(user_id)
    today = get_today()

    with cache_lock:
        if user_id not in request_cache or request_cache[user_id]["date"] != today:
            request_cache[user_id] = {
                "date": today,
                "promo": 0,
                "transaction": 0
            }

        request_cache[user_id][action_type] += 1

# ======== 2. TRA CỨU LƯỢT CÒN LẠI TRONG SQLITE ========
def get_remaining_requests_from_db(user_id, action_type):
    user_id = str(user_id)
    today = get_today()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT promo_count, transaction_count, date FROM user_requests WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row or row[2] != today:
        return PROMO_LIMIT if action_type == "promo" else TRANSACTION_LIMIT

    if action_type == "promo":
        return max(0, PROMO_LIMIT - row[0])
    elif action_type == "transaction":
        return max(0, TRANSACTION_LIMIT - row[1])
    return 0

# ======== 3. KIỂM TRA CÒN LƯỢT KHÔNG ========
def is_request_available(user_id, action_type):
    remaining = get_remaining_requests_from_db(user_id, action_type)
    return remaining > 0

# ======== 4. FLUSH CACHE XUỐNG SQLITE ========
def flush_cache_to_sqlite():
    today = get_today()
    with cache_lock:
        if not request_cache:
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        for user_id, data in request_cache.items():
            if data["date"] != today:
                continue

            cursor.execute("""
            INSERT INTO user_requests (user_id, date, promo_count, transaction_count)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                promo_count = excluded.promo_count,
                transaction_count = excluded.transaction_count,
                date = excluded.date
            """, (
                user_id,
                data["date"],
                data.get("promo", 0),
                data.get("transaction", 0)
            ))

        conn.commit()
        conn.close()

# ======== 5. BẮT ĐẦU FLUSHER CHẠY NỀN MỖI 2 PHÚT ========
def start_background_flusher():
    def flusher():
        while True:
            time.sleep(FLUSH_INTERVAL)
            try:
                flush_cache_to_sqlite()
            except Exception as e:
                print(f"❌ Error flushing cache: {e}")
    thread = threading.Thread(target=flusher, daemon=True)
    thread.start()

# ======== 6. ĐẶT LỊCH RESET LÚC 00:00 UTC-4 MỖI NGÀY ========
def reset_daily_requests():
    global request_cache
    with cache_lock:
        request_cache.clear()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_requests")
    conn.commit()
    conn.close()
    print("🔁 Đã reset lượt yêu cầu (UTC-4)")

def schedule_daily_reset():
    scheduler = BackgroundScheduler(timezone=timezone("Etc/GMT+4"))  # UTC-4
    scheduler.add_job(
        func=reset_daily_requests,
        trigger="cron",
        hour=0,
        minute=0,
        id="daily_reset_job"
    )
    scheduler.start()
    print("⏰ Đã lên lịch reset lượt lúc 00:00 UTC-4 mỗi ngày.")

