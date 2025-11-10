import sqlite3
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Tuple

logger = logging.getLogger(__name__)

class MessageTimeManager:
    """Менеджер для работы с временными метками последних сообщений"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.db_path = os.path.join(data_dir, 'message_times.db')
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS last_messages (
                        group_url TEXT PRIMARY KEY,
                        group_id INTEGER,
                        group_name TEXT,
                        last_message_time TIMESTAMP,
                        last_message_id INTEGER,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
                logger.info("✅ База данных инициализирована")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации базы данных: {e}")
            raise
    
    def save_last_message_time(self, group_url: str, group_id: int, group_name: str, 
                              message_time: datetime, message_id: int):
        """Сохранение времени последнего сообщения"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO last_messages 
                    (group_url, group_id, group_name, last_message_time, last_message_id, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (group_url, group_id, group_name, message_time, message_id, datetime.now(timezone.utc)))
                conn.commit()
                logger.debug(f"💾 Сохранено время для группы: {message_time}")
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения времени для группы: {e}")
    
    def get_last_message_time(self, group_url: str) -> Optional[datetime]:
        """Получение времени последнего сообщения для группы"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    'SELECT last_message_time FROM last_messages WHERE group_url = ?',
                    (group_url,)
                )
                result = cursor.fetchone()
                if result:
                    # Преобразуем строку обратно в datetime
                    time_str = result[0]
                    if isinstance(time_str, str):
                        return datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                    return time_str
                return None
        except Exception as e:
            logger.error(f"❌ Ошибка получения времени для группы: {e}")
            return None
    
    def get_all_last_times(self) -> Dict[str, Tuple[datetime, int, str]]:
        """Получение всех сохраненных времен"""
        result = {}
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT group_url, last_message_time, group_id, group_name 
                    FROM last_messages
                ''')
                for row in cursor.fetchall():
                    group_url, time_str, group_id, group_name = row
                    if isinstance(time_str, str):
                        message_time = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                    else:
                        message_time = time_str
                    result[group_url] = (message_time, group_id, group_name)
                logger.info(f"📊 Загружено {len(result)} сохраненных времен")
        except Exception as e:
            logger.error(f"❌ Ошибка получения всех времен: {e}")
        return result
    
    def get_fallback_time(self, minutes_ago: int = 10) -> datetime:
        """Получение времени для fallback (по умолчанию 10 минут назад)"""
        return datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    
    def cleanup_old_records(self, days_old: int = 30):
        """Очистка старых записей (опционально)"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    'DELETE FROM last_messages WHERE updated_at < ?',
                    (cutoff_date,)
                )
                deleted_count = cursor.rowcount
                conn.commit()
                if deleted_count > 0:
                    logger.info(f"🗑️ Удалено {deleted_count} старых записей")
        except Exception as e:
            logger.error(f"❌ Ошибка очистки старых записей: {e}")
    
    def get_statistics(self) -> Dict[str, int]:
        """Получение статистики по базе данных"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('SELECT COUNT(*) FROM last_messages')
                total_groups = cursor.fetchone()[0]
                
                cursor = conn.execute('''
                    SELECT COUNT(*) FROM last_messages 
                    WHERE updated_at > datetime('now', '-1 day')
                ''')
                active_today = cursor.fetchone()[0]
                
                return {
                    'total_groups': total_groups,
                    'active_today': active_today
                }
        except Exception as e:
            logger.error(f"❌ Ошибка получения статистики: {e}")
            return {'total_groups': 0, 'active_today': 0}