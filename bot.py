
import asyncio
import re
import logging
import random
from datetime import datetime, timezone
from telethon import TelegramClient, events
import sqlite3
import os

from config import API_ID, API_HASH, BOT_TOKEN, TARGET_GROUP, SESSION_NAME, GROUPS_TO_MONITOR, KEYWORDS

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramMonitor:
    def __init__(self):
        """
        Гибридная архитектура:
        - userbot (API_ID + API_HASH) для мониторинга групп
        - bot (BOT_TOKEN) для отправки уведомлений
        """
        # Userbot для мониторинга групп (от имени пользователя)
        self.user_client = TelegramClient(f"{SESSION_NAME}_user", API_ID, API_HASH)
        
        # Bot для отправки уведомлений (токен бота)
        self.bot_client = TelegramClient(f"{SESSION_NAME}_bot", API_ID, API_HASH)
        
        self.target_entity = None  # Информация о целевой группе
        self.start_time = None  # Время запуска бота
        self.groups_entities = {}  # Кэш информации о группах
        self.monitored_chats = []  # Список ID чатов для мониторинга
        
    async def init(self):
        """Инициализация и запуск системы"""
        try:
            # Запускаем userbot (потребует авторизации при первом запуске)
            await self.user_client.start()
            self.start_time = datetime.now(timezone.utc)
            
            # Небольшая задержка для безопасности
            await asyncio.sleep(random.uniform(1, 3))
            
            # Запускаем bot
            await self.bot_client.start(bot_token=BOT_TOKEN)
            
        except sqlite3.OperationalError as e:
            if "no such column: version" in str(e):
                logger.error("❌ Поврежденная база данных сессии. Удаляем и пересоздаем...")
                # Удаляем поврежденные файлы сессии
                session_files = [
                    f"{SESSION_NAME}_user.session", f"{SESSION_NAME}_user.session-journal",
                    f"{SESSION_NAME}_bot.session", f"{SESSION_NAME}_bot.session-journal"
                ]
                for file in session_files:
                    if os.path.exists(file):
                        os.remove(file)
                        logger.info(f"🗑️ Удален файл: {file}")
                
                # Пересоздаем клиенты и запускаем заново
                self.user_client = TelegramClient(f"{SESSION_NAME}_user", API_ID, API_HASH)
                self.bot_client = TelegramClient(f"{SESSION_NAME}_bot", API_ID, API_HASH)
                
                await self.user_client.start()
                await asyncio.sleep(random.uniform(1, 3))
                await self.bot_client.start(bot_token=BOT_TOKEN)
                
                self.start_time = datetime.now(timezone.utc)
                logger.info("✅ Сессии пересозданы успешно")
            else:
                raise
        
        print(f"✅ Система запущена в {self.start_time.strftime('%d.%m.%Y %H:%M')}")
        
        # Получаем информацию о userbot
        user_me = await self.user_client.get_me()
        print(f"👤 Userbot: {user_me.first_name} (@{user_me.username or 'без username'})")
        
        # Получаем информацию о боте
        bot_me = await self.bot_client.get_me()
        print(f"🤖 Bot: {bot_me.first_name} (@{bot_me.username})")
        
        # Задержка для безопасности
        await asyncio.sleep(random.uniform(2, 5))
        
        # Получаем информацию о целевой группе
        try:
            self.target_entity = await self.bot_client.get_entity(TARGET_GROUP)
            group_name = getattr(self.target_entity, 'title', TARGET_GROUP)
            print(f"✅ Уведомления будут отправляться в: {group_name}")
        except Exception as e:
            print(f"❌ Ошибка получения целевой группы {TARGET_GROUP}: {e}")
            print("⚠️  Убедитесь, что бот добавлен в целевую группу")
            
        # Получаем информацию о группах для мониторинга
        await self.get_groups_info()
        
        # Настраиваем обработчик событий
        await self.setup_event_handlers()

    async def get_groups_info(self):
        """Получает информацию о группах для мониторинга через userbot"""
        print(f"📋 Настройка мониторинга {len(GROUPS_TO_MONITOR)} групп...")
        
        for i, group_url in enumerate(GROUPS_TO_MONITOR):
            try:
                # Задержка между запросами для безопасности
                if i > 0:
                    delay = random.uniform(1, 3)
                    await asyncio.sleep(delay)
                
                # Преобразуем URL в entity через userbot
                entity = await self.url_to_entity(group_url)
                if entity:
                    self.groups_entities[group_url] = entity
                    self.monitored_chats.append(entity.id)
                    group_name = getattr(entity, 'title', group_url)
                    print(f"✅ Добавлена группа: {group_name}")
                else:
                    print(f"❌ Не удалось получить группу: {group_url}")
                    
            except Exception as e:
                print(f"❌ Ошибка при получении группы {group_url}: {e}")
                
        print(f"📊 Успешно настроено {len(self.groups_entities)} групп из {len(GROUPS_TO_MONITOR)}")
        
        # Финальная задержка
        await asyncio.sleep(random.uniform(2, 4))
        
    async def setup_event_handlers(self):
        """Настраивает обработчики событий для мониторинга через userbot"""
        print("🔧 Настройка обработчиков событий...")
        
        @self.user_client.on(events.NewMessage(chats=self.monitored_chats))
        async def handle_new_message(event):
            """Обработчик новых сообщений"""
            try:
                # Небольшая случайная задержка для имитации человеческого поведения
                await asyncio.sleep(random.uniform(1.5, 5))
                
                # Пропускаем сообщения без текста
                if not event.text:
                    return
                    
                # Пропускаем старые сообщения (до запуска бота)
                event_time = event.date
                if event_time.tzinfo is None:
                    event_time = event_time.replace(tzinfo=timezone.utc)
                
                if event_time < self.start_time:
                    return
                    
                # Проверяем на ключевые слова
                keywords = self.find_keywords(event.text)
                if keywords:
                    # Получаем информацию о группе
                    chat = await event.get_chat()
                    logger.info(f"🎯 Найдено сообщение с ключевыми словами в {chat.title}: {keywords[:3]}")
                    
                    # Задержка перед обработкой
                    await asyncio.sleep(random.uniform(1, 3))
                    
                    await self.process_found_message(event, chat)
                    
            except Exception as e:
                logger.error(f"❌ Ошибка в обработчике сообщений: {e}")
        
        print("✅ Обработчики событий настроены")
        
    async def url_to_entity(self, url):
        """Преобразует URL группы в entity через userbot"""
        try:
            # Убираем префикс t.me/
            if url.startswith('t.me/'):
                url = url[5:]
            elif url.startswith('https://t.me/'):
                url = url[13:]
                
            # Обрабатываем разные типы ссылок
            if url.startswith('+'):
                # Инвайт-ссылка
                return await self.user_client.get_entity(url)
            elif '/c/' in url:
                # Приватная группа
                parts = url.split('/c/')[1].split('/')
                chat_id = int(parts[0])
                return await self.user_client.get_entity(f"-100{chat_id}")
            else:
                # Обычная группа/канал
                username = url.split('/')[0]
                return await self.user_client.get_entity(username)
                
        except Exception as e:
            logger.error(f"Ошибка преобразования URL {url}: {e}")
            return None
        
    def find_keywords(self, text):
        """
        Поиск ключевых слов в тексте сообщения.
        Возвращает список найденных ключевых слов.
        """
        if not text:
            return []
            
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in KEYWORDS:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)
                
        return found_keywords
        
    def extract_telegram_username(self, text):
        """Извлекает Telegram username из текста"""
        if not text:
            return None
            
        # Ищем @username в тексте
        pattern = r'@([a-zA-Z0-9_]+)'
        matches = re.findall(pattern, text)
        
        if matches:
            return matches[0]  # Возвращаем первый найденный username
            
        return None
        
    async def create_contact_button_from_event(self, event, sender):
        """Создает кнопку для связи с автором сообщения из события"""
        try:
            # Проверяем, есть ли @username в тексте сообщения
            username_in_text = self.extract_telegram_username(event.text)
            
            if username_in_text:
                # Если есть username в тексте, используем его
                return f"[Написать @{username_in_text}](https://t.me/{username_in_text})"
            elif sender and hasattr(sender, 'username') and sender.username:
                # Если есть username у автора сообщения
                return f"[Написать @{sender.username}](https://t.me/{sender.username})"
            else:
                # Если нет username, создаем ссылку на отправку сообщения по ID
                user_id = event.sender_id
                return f"[Написать автору](tg://user?id={user_id})"
                
        except Exception as e:
            logger.error(f"Ошибка создания кнопки контакта: {e}")
            return "[Связаться с автором]()"
            
    async def process_found_message(self, event, group_entity):
        """Обрабатывает найденное сообщение"""
        try:
            # Получаем отправителя через userbot
            sender = await event.get_sender()
            
            # Задержка для безопасности
            await asyncio.sleep(random.uniform(0.5, 1.5))
            
            # Формируем информацию об авторе
            author_info = "Неизвестный автор"
            if sender:
                if hasattr(sender, 'username') and sender.username:
                    author_info = f"@{sender.username}"
                elif hasattr(sender, 'first_name'):
                    author_info = sender.first_name
                    if hasattr(sender, 'last_name') and sender.last_name:
                        author_info += f" {sender.last_name}"
                        
            # Информация о группе
            group_name = getattr(group_entity, 'title', 'Неизвестная группа')
            
            # Найденные ключевые слова
            keywords = self.find_keywords(event.text)
            keywords_text = ", ".join(keywords[:5])  # Показываем первые 5 ключевых слов
            
            # Создаем кнопку для связи с автором
            contact_button = await self.create_contact_button_from_event(event, sender)
            
            # Создаем ссылки на группу и сообщение
            group_link = await self.create_group_link(group_entity)
            message_link = await self.create_message_link(event, group_entity)
            
            # Формируем текст уведомления
            notification_text = (
                f"🎵 **Найдено предложение!**\n\n"
                f"👤 **Автор:** {author_info}\n"
                f"💬 **Группа:** {group_link}\n"
                f"🔍 **Ключевые слова:** {keywords_text}\n"
                f"📅 **Время:** {event.date.strftime('%d.%m.%Y %H:%M')}\n\n"
                f"**Сообщение:**\n{event.text}\n\n"
                f"🔗 {message_link}\n"
                f"👆 {contact_button}"
            )
            
            # Задержка перед отправкой уведомления
            await asyncio.sleep(random.uniform(1, 2))
            
            # Отправляем уведомление через bot
            if self.target_entity:
                await self.bot_client.send_message(
                    self.target_entity,
                    notification_text,
                    parse_mode='markdown'
                )
                
                logger.info(f"✅ Отправлено уведомление о сообщении от {author_info} в {group_name}")
            else:
                logger.warning("⚠️ Целевая группа не настроена")
                
        except Exception as e:
            logger.error(f"❌ Ошибка при обработке найденного сообщения: {e}")
            
    async def create_group_link(self, group_entity):
        """Создает ссылку на группу"""
        try:
            group_name = getattr(group_entity, 'title', 'Группа')
            
            # Если у группы есть username
            if hasattr(group_entity, 'username') and group_entity.username:
                return f"[{group_name}](https://t.me/{group_entity.username})"
            else:
                # Для приватных групп используем ID
                chat_id = str(group_entity.id)
                if chat_id.startswith('-100'):
                    # Убираем префикс -100 для создания ссылки
                    clean_id = chat_id[4:]
                    return f"[{group_name}](https://t.me/c/{clean_id})"
                else:
                    # Обычная группа
                    return f"{group_name}"
                    
        except Exception as e:
            logger.error(f"Ошибка создания ссылки на группу: {e}")
            return getattr(group_entity, 'title', 'Группа')
            
    async def create_message_link(self, event, group_entity):
        """Создает ссылку на конкретное сообщение"""
        try:
            message_id = event.id
            
            # Если у группы есть username (публичная)
            if hasattr(group_entity, 'username') and group_entity.username:
                return f"[Перейти к сообщению](https://t.me/{group_entity.username}/{message_id})"
            else:
                # Для приватных групп
                chat_id = str(group_entity.id)
                if chat_id.startswith('-100'):
                    # Убираем префикс -100 для создания ссылки
                    clean_id = chat_id[4:]
                    return f"[Перейти к сообщению](https://t.me/c/{clean_id}/{message_id})"
                else:
                    return "[Ссылка недоступна для приватной группы]()"
                    
        except Exception as e:
            logger.error(f"Ошибка создания ссылки на сообщение: {e}")
            return "[Ссылка на сообщение недоступна]()"
            
    async def run(self):
        """Запуск системы"""
        try:
            await self.init()
            
            print("🔍 Гибридный мониторинг запущен!")
            print("👤 Userbot - мониторинг групп от вашего имени")
            print("🤖 Bot - отправка уведомлений в целевую группу")
            print(f"📝 Отслеживаем {len(KEYWORDS)} ключевых слов")
            print("📡 Используем события для реального времени")
            print("🛡️  Добавлены задержки для безопасности")
            print("⏹️  Нажмите Ctrl+C для остановки")
            
            # Запускаем бесконечный цикл для обработки событий
            await self.user_client.run_until_disconnected()
            
        except KeyboardInterrupt:
            logger.info("⏹️ Получен сигнал остановки")
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")
        finally:
            await self.user_client.disconnect()
            await self.bot_client.disconnect()
            logger.info("✅ Система остановлена")

async def main():
    """Главная функция"""
    monitor = TelegramMonitor()
    await monitor.run()

if __name__ == "__main__":
    asyncio.run(main())