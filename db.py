import os
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO)

# SQLite3 database fayli
DATABASE_NAME = 'garajhub.db'

def get_db_connection():
    """Database ulanishini olish"""
    conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Row formatda natijalarni olish
    return conn

def init_db():
    """Database jadvalarini yaratish"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Users jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            last_name TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            gender TEXT DEFAULT '',
            birth_date TEXT DEFAULT '',
            bio TEXT DEFAULT '',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Startups jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS startups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            logo TEXT,
            group_link TEXT NOT NULL,
            owner_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            results TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            ended_at TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users(user_id)
        )
    ''')
    
    # Startup members jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS startup_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            startup_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(startup_id, user_id),
            FOREIGN KEY (startup_id) REFERENCES startups(id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Indexlar yaratish
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON users(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_startup_owner ON startups(owner_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_startup_status ON startups(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_member_startup ON startup_members(startup_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_member_user ON startup_members(user_id)')
    
    conn.commit()
    conn.close()
    logging.info("SQLite database initialized successfully")

# =========== USERS FUNCTIONS ===========

def get_user(user_id: int) -> Optional[Dict]:
    """Foydalanuvchini ID bo'yicha olish"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT * FROM users WHERE user_id = ?',
            (user_id,)
        )
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return dict(user)
        return None
    except Exception as e:
        logging.error(f"Error getting user {user_id}: {e}")
        return None

def save_user(user_id: int, username: str, first_name: str):
    """Yangi foydalanuvchi qo'shish yoki mavjudni yangilash"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, username, first_name, joined_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, datetime.now()))
        
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Error saving user {user_id}: {e}")

def update_user_field(user_id: int, field: str, value: str):
    """Foydalanuvchi maydonini yangilash"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            f'UPDATE users SET {field} = ? WHERE user_id = ?',
            (value, user_id)
        )
        
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Error updating user field {user_id}.{field}: {e}")

# =========== STARTUPS FUNCTIONS ===========

def create_startup(name: str, description: str, logo: str, group_link: str, owner_id: int) -> Optional[int]:
    """Yangi startup yaratish"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO startups (name, description, logo, group_link, owner_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, description, logo, group_link, owner_id, datetime.now()))
        
        startup_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return startup_id
    except Exception as e:
        logging.error(f"Error creating startup: {e}")
        return None

def get_startup(startup_id: int) -> Optional[Dict]:
    """Startupni ID bo'yicha olish"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT * FROM startups WHERE id = ?',
            (startup_id,)
        )
        
        startup = cursor.fetchone()
        conn.close()
        
        if startup:
            return dict(startup)
        return None
    except Exception as e:
        logging.error(f"Error getting startup {startup_id}: {e}")
        return None

def get_startups_by_owner(owner_id: int) -> List[Dict]:
    """Muallif ID bo'yicha startuplarni olish"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT * FROM startups WHERE owner_id = ? ORDER BY created_at DESC',
            (owner_id,)
        )
        
        startups = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return startups
    except Exception as e:
        logging.error(f"Error getting startups for owner {owner_id}: {e}")
        return []

def get_pending_startups(page: int = 1, per_page: int = 5) -> Tuple[List[Dict], int]:
    """Kutilayotgan startuplar"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Jami son
        cursor.execute('SELECT COUNT(*) FROM startups WHERE status = "pending"')
        total = cursor.fetchone()[0]
        
        # Sahifalangan natijalar
        offset = (page - 1) * per_page
        cursor.execute(
            'SELECT * FROM startups WHERE status = "pending" ORDER BY created_at DESC LIMIT ? OFFSET ?',
            (per_page, offset)
        )
        
        startups = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return startups, total
    except Exception as e:
        logging.error(f"Error getting pending startups: {e}")
        return [], 0

def get_active_startups(page: int = 1, per_page: int = 10) -> Tuple[List[Dict], int]:
    """Faol startuplar"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Jami son
        cursor.execute('SELECT COUNT(*) FROM startups WHERE status = "active"')
        total = cursor.fetchone()[0]
        
        # Sahifalangan natijalar
        offset = (page - 1) * per_page
        cursor.execute(
            'SELECT * FROM startups WHERE status = "active" ORDER BY created_at DESC LIMIT ? OFFSET ?',
            (per_page, offset)
        )
        
        startups = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return startups, total
    except Exception as e:
        logging.error(f"Error getting active startups: {e}")
        return [], 0

def update_startup_status(startup_id: int, status: str):
    """Startup holatini yangilash"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if status == 'active':
            cursor.execute(
                'UPDATE startups SET status = ?, started_at = ? WHERE id = ?',
                (status, datetime.now(), startup_id)
            )
        elif status == 'completed':
            cursor.execute(
                'UPDATE startups SET status = ?, ended_at = ? WHERE id = ?',
                (status, datetime.now(), startup_id)
            )
        else:
            cursor.execute(
                'UPDATE startups SET status = ? WHERE id = ?',
                (status, startup_id)
            )
        
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Error updating startup status {startup_id}: {e}")

def update_startup_results(startup_id: int, results: str):
    """Startup natijalarini yangilash"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE startups SET results = ? WHERE id = ?',
            (results, startup_id)
        )
        
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Error updating startup results {startup_id}: {e}")

# =========== STARTUP MEMBERS FUNCTIONS ===========

def add_startup_member(startup_id: int, user_id: int) -> Optional[int]:
    """Startupga a'zo qo'shish"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Mavjudligini tekshirish
        cursor.execute(
            'SELECT id FROM startup_members WHERE startup_id = ? AND user_id = ?',
            (startup_id, user_id)
        )
        
        existing = cursor.fetchone()
        if existing:
            conn.close()
            return existing['id']
        
        # Yangi a'zo qo'shish
        cursor.execute('''
            INSERT INTO startup_members (startup_id, user_id, joined_at)
            VALUES (?, ?, ?)
        ''', (startup_id, user_id, datetime.now()))
        
        request_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return request_id
    except Exception as e:
        logging.error(f"Error adding startup member: {e}")
        return None

def get_join_request_id(startup_id: int, user_id: int) -> Optional[int]:
    """Qo'shilish so'rovi ID sini olish"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT id FROM startup_members WHERE startup_id = ? AND user_id = ?',
            (startup_id, user_id)
        )
        
        request = cursor.fetchone()
        conn.close()
        
        if request:
            return request['id']
        return None
    except Exception as e:
        logging.error(f"Error getting join request: {e}")
        return None

def update_join_request(request_id: int, status: str):
    """Qo'shilish so'rovini yangilash"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'UPDATE startup_members SET status = ? WHERE id = ?',
            (status, request_id)
        )
        
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Error updating join request {request_id}: {e}")

def get_startup_members(startup_id: int, page: int = 1, per_page: int = 5) -> Tuple[List[Dict], int]:
    """Startup a'zolarini olish"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Jami son
        cursor.execute(
            '''SELECT COUNT(*) FROM startup_members sm
               JOIN users u ON sm.user_id = u.user_id
               WHERE sm.startup_id = ? AND sm.status = "accepted"''',
            (startup_id,)
        )
        total = cursor.fetchone()[0]
        
        # Sahifalangan natijalar
        offset = (page - 1) * per_page
        cursor.execute(
            '''SELECT u.user_id, u.first_name, u.last_name, u.username, u.phone, u.bio
               FROM startup_members sm
               JOIN users u ON sm.user_id = u.user_id
               WHERE sm.startup_id = ? AND sm.status = "accepted"
               LIMIT ? OFFSET ?''',
            (startup_id, per_page, offset)
        )
        
        members = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return members, total
    except Exception as e:
        logging.error(f"Error getting startup members {startup_id}: {e}")
        return [], 0

def get_all_startup_members(startup_id: int) -> List[int]:
    """Startupning barcha a'zolari (faqat user_id lar)"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT user_id FROM startup_members WHERE startup_id = ? AND status = "accepted"',
            (startup_id,)
        )
        
        members = [row['user_id'] for row in cursor.fetchall()]
        conn.close()
        
        return members
    except Exception as e:
        logging.error(f"Error getting all startup members {startup_id}: {e}")
        return []

# =========== STATISTICS FUNCTIONS ===========

def get_statistics() -> Dict:
    """Umumiy statistika"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM startups')
        total_startups = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM startups WHERE status = "active"')
        active_startups = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM startups WHERE status = "pending"')
        pending_startups = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM startups WHERE status = "completed"')
        completed_startups = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM startups WHERE status = "rejected"')
        rejected_startups = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_users': total_users,
            'total_startups': total_startups,
            'active_startups': active_startups,
            'pending_startups': pending_startups,
            'completed_startups': completed_startups,
            'rejected_startups': rejected_startups
        }
    except Exception as e:
        logging.error(f"Error getting statistics: {e}")
        return {}

def get_all_users() -> List[int]:
    """Barcha foydalanuvchi ID larini olish"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT user_id FROM users')
        users = [row['user_id'] for row in cursor.fetchall()]
        conn.close()
        
        return users
    except Exception as e:
        logging.error(f"Error getting all users: {e}")
        return []

def get_recent_users(limit: int = 10) -> List[Dict]:
    """So'nggi foydalanuvchilar"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT user_id, username, first_name, last_name, joined_at FROM users ORDER BY joined_at DESC LIMIT ?',
            (limit,)
        )
        
        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return users
    except Exception as e:
        logging.error(f"Error getting recent users: {e}")
        return []

def get_recent_startups(limit: int = 10) -> List[Dict]:
    """So'nggi startuplar"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT id, name, status, created_at FROM startups ORDER BY created_at DESC LIMIT ?',
            (limit,)
        )
        
        startups = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return startups
    except Exception as e:
        logging.error(f"Error getting recent startups: {e}")
        return []

def get_completed_startups(page: int = 1, per_page: int = 5) -> Tuple[List[Dict], int]:
    """Yakunlangan startuplar"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Jami son
        cursor.execute('SELECT COUNT(*) FROM startups WHERE status = "completed"')
        total = cursor.fetchone()[0]
        
        # Sahifalangan natijalar
        offset = (page - 1) * per_page
        cursor.execute(
            'SELECT * FROM startups WHERE status = "completed" ORDER BY created_at DESC LIMIT ? OFFSET ?',
            (per_page, offset)
        )
        
        startups = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return startups, total
    except Exception as e:
        logging.error(f"Error getting completed startups: {e}")
        return [], 0

def get_rejected_startups(page: int = 1, per_page: int = 5) -> Tuple[List[Dict], int]:
    """Rad etilgan startuplar"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Jami son
        cursor.execute('SELECT COUNT(*) FROM startups WHERE status = "rejected"')
        total = cursor.fetchone()[0]
        
        # Sahifalangan natijalar
        offset = (page - 1) * per_page
        cursor.execute(
            'SELECT * FROM startups WHERE status = "rejected" ORDER BY created_at DESC LIMIT ? OFFSET ?',
            (per_page, offset)
        )
        
        startups = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return startups, total
    except Exception as e:
        logging.error(f"Error getting rejected startups: {e}")
        return [], 0