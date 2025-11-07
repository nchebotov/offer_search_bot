import os
from dotenv import load_dotenv

# Загружаем .env файл только если он существует (для локальной разработки)
# На хостинге используются системные переменные окружения
if os.path.exists('.env'):
    load_dotenv()
    print("📄 Загружены переменные из .env файла")
else:
    print("🌐 Используются системные переменные окружения")

# Telegram API credentials
API_ID = int(os.getenv('API_ID', '0'))
API_HASH = os.getenv('API_HASH', '')

# Bot token от @BotFather
BOT_TOKEN = os.getenv('BOT_TOKEN', '')

# Целевая группа для уведомлений
TARGET_GROUP = os.getenv('TARGET_GROUP', '@your_target_group')

# Session name
SESSION_NAME = os.getenv('SESSION_NAME', 'offer_search_bot')


# Группы для мониторинга (через переменные окружения)
def get_groups_from_env():
    """Получает список групп из переменных окружения"""
    groups_str = os.getenv('GROUPS_TO_MONITOR', '')
    return [group.strip() for group in groups_str.split(',') if group.strip()]


# Ключевые слова для поиска (через переменные окружения)
def get_keywords_from_env():
    """Получает список ключевых слов из переменных окружения"""
    keywords_str = os.getenv('KEYWORDS', '')
    return [keyword.strip() for keyword in keywords_str.split(',') if keyword.strip()]
    

# Получаем конфигурацию
GROUPS_TO_MONITOR = get_groups_from_env()
KEYWORDS = get_keywords_from_env()