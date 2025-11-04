import os
from dotenv import load_dotenv

load_dotenv()

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
    if groups_str:
        return [group.strip() for group in groups_str.split(',') if group.strip()]
    
    # Дефолтный список если не задан в .env
    return [
        't.me/+eF-DQe6C7ullMmIy',
        't.me/eventori',
        't.me/bigfingerchat',
        't.me/meropriyatiyachat',
        't.me/event_tusa/1',
        't.me/spbeventjob',
        't.me/mskeventjob',
        't.me/artists_for_you',
        't.me/eventrossii',
        't.me/meropriyatiya_chat',
        't.me/spbeventchat',
        't.me/event_team1',
        't.me/eventsearch',
        't.me/your_organizator'
    ]

# Ключевые слова для поиска (через переменные окружения)
def get_keywords_from_env():
    """Получает список ключевых слов из переменных окружения"""
    keywords_str = os.getenv('KEYWORDS', '')
    if keywords_str:
        return [keyword.strip() for keyword in keywords_str.split(',') if keyword.strip()]
    
    # Дефолтный список если не задан в .env
    return [
        'скрипк', 'альт', 'виолончел', 'контрабас', 'арф', 'флейт', 'саксофон',
        'саксофонист', 'саксофонистк', 'труб', 'тромбон', 'туб', 'валторн',
        'кларнет', 'гобо', 'пианино', 'пианист', 'пианистк', 'роял', 'фортепиано',
        'гитар', 'бас-гитар', 'электрогитар', 'акустик', 'баян', 'аккордеон',
        'гармон', 'голос', 'вокал', 'вокалист', 'вокалистк', 'певиц', 'певец',
        'диджей', 'dj', 'духовой', 'оркестр', 'квартет', 'трио', 'дуэт', 'ансамбл',
        'кавер', 'кавер-бэнд', 'бэнд', 'жива', 'музыка', 'живой', 'звук', 'струнн',
        'духов', 'ударн', 'барабан', 'ханг', 'хор', 'хорист', 'акапела', 'аккапела',
        'фоновая', 'камерная', 'солист', 'соло', 'концерт', 'программ', 'репертуар',
        'классик', 'джаз', 'jazz', 'поп', 'pop', 'рок', 'rock', 'эстрад', 'хит',
        'хиты', 'танцевальн', 'для дет', 'для взросл', 'электро'
    ]

# Получаем конфигурацию
GROUPS_TO_MONITOR = get_groups_from_env()
KEYWORDS = get_keywords_from_env()