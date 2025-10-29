import time
from typing import List, Optional
from loguru import logger
from telegram import Update, Message
from telegram.ext import Application, ContextTypes, MessageHandler, filters
from telegram.constants import ParseMode

from bot.chatgpt_client import ChatGPTClient
from bot.channel_monitor import ChannelMonitor
from bot.config import MESSAGE_THRESHOLD_MIN, MESSAGE_THRESHOLD_MAX


class TelegramBotHandler:
    """Главный обработчик Telegram бота"""
    
    def __init__(self, config):
        self.config = config
        self.application = None
        self.chatgpt_client = ChatGPTClient()
        self.monitor = ChannelMonitor(activity_timeout=config.ACTIVITY_TIMEOUT)
        self.bot_id = None
        self.channel_id = None
        
        # История последних сообщений для контекста
        self.recent_messages: List[str] = []
        self.max_context_messages = 3
        
    async def initialize(self):
        """Инициализация бота"""
        self.application = Application.builder().token(self.config.BOT_TOKEN).build()
        self.channel_id = self.config.CHANNEL_ID
        
        # Получаем информацию о боте
        bot_info = await self.application.bot.get_me()
        self.bot_id = bot_info.id
        self.monitor.set_bot_id(self.bot_id)
        
        logger.info(f"Bot initialized: @{bot_info.username} (ID: {self.bot_id})")
        logger.info(f"Channel ID: {self.channel_id}")
        
        # Регистрируем обработчик через application для всех типов обновлений
        # Обработчик поддерживает и каналы и группы
        async def all_updates_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
            # Логируем ВСЕ обновления
            has_channel_post = update.channel_post is not None
            has_edited = update.edited_channel_post is not None
            has_message = update.message is not None
            has_edited_message = update.edited_message is not None
            
            logger.info(f"ALL UPDATES: channel_post={has_channel_post}, message={has_message}, edited={has_edited}, edited_msg={has_edited_message}")
            
            # Обрабатываем сообщения из группы
            if update.message and update.message.chat.type in ['group', 'supergroup']:
                logger.info(f"Processing message from group: {update.message.chat.id}")
                await self.handle_channel_message(update, context)
            # Обрабатываем сообщения из канала
            elif update.channel_post:
                logger.info(f"Processing channel_post from chat: {update.channel_post.chat.id}")
                await self.handle_channel_message(update, context)
            elif update.edited_message and update.edited_message.chat.type in ['group', 'supergroup']:
                logger.info(f"Processing edited message from group")
                update.message = update.edited_message
                await self.handle_channel_message(update, context)
            elif update.edited_channel_post:
                logger.info(f"Processing edited_channel_post")
                update.channel_post = update.edited_channel_post
                await self.handle_channel_message(update, context)
        
        # Используем BaseHandler для обработки всех обновлений  
        from telegram.ext import BaseHandler
        
        class AllUpdatesHandler(BaseHandler):
            def __init__(self, callback):
                super().__init__(callback)
            
            def check_update(self, update):
                return True
        
        self.application.add_handler(AllUpdatesHandler(all_updates_handler))
    
    async def handle_channel_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка сообщений из группы или канала"""
        try:
            # Поддерживаем и сообщения из группы и из канала
            message = update.message if update.message else update.channel_post
            if not message:
                logger.warning("handle_channel_message called but message is None")
                return
            
            # Проверяем, что это сообщение из нужной группы/канала
            chat_id = str(message.chat.id)
            channel_id_str = str(self.channel_id)
            logger.info(f"Received message from chat_id: {chat_id}, expected: {channel_id_str}")
            
            if chat_id != channel_id_str and channel_id_str != chat_id:
                logger.debug(f"Message from different chat, skipping. Got: {chat_id}, Expected: {channel_id_str}")
                return
            
            # Получаем информацию об авторе сообщения
            user_id = None
            if message.from_user:
                user_id = message.from_user.id
            elif message.author_signature:
                # Для каналов без автора
                user_id = hash(message.author_signature)
            
            if user_id is None:
                user_id = message.chat.id  # Fallback
            
            # Обновляем мониторинг активности
            self.monitor.update_last_activity(user_id)
            
            # Добавляем текст сообщения в историю (только от пользователей, не от бота)
            if user_id != self.bot_id and message.text:
                self.recent_messages.append(message.text)
                if len(self.recent_messages) > self.max_context_messages:
                    self.recent_messages.pop(0)
            
            logger.info(f"Message received. User: {user_id}, Text: {message.text[:50] if message.text else 'No text'}")
            
            # Проверяем, должен ли бот ответить
            if self.monitor.should_bot_respond(MESSAGE_THRESHOLD_MIN, MESSAGE_THRESHOLD_MAX):
                await self.respond_to_conversation()
                self.monitor.reset_counter()
                self.recent_messages.clear()
                
        except Exception as e:
            logger.error(f"Error handling channel message: {e}")
    
    async def respond_to_conversation(self):
        """Отвечает на активное обсуждение в канале"""
        try:
            logger.info("Bot responding to conversation")
            
            # Формируем контекст из последних сообщений
            context = "\n".join(self.recent_messages[-3:]) if self.recent_messages else "Общая болтовня"
            
            # Генерируем комментарий
            comment = await self.chatgpt_client.generate_comment(context)
            
            # Отправляем сообщение
            await self.application.bot.send_message(
                chat_id=self.channel_id,
                text=comment
            )
            
            logger.success(f"Bot responded: {comment[:50]}...")
            
        except Exception as e:
            logger.error(f"Error responding to conversation: {e}")
    
    async def send_message_to_channel(self, text: str):
        """Отправляет сообщение в канал"""
        try:
            await self.application.bot.send_message(
                chat_id=self.channel_id,
                text=text
            )
            logger.info("Message sent to channel")
        except Exception as e:
            logger.error(f"Error sending message to channel: {e}")
    
    async def start_polling(self):
        """Запускает long polling"""
        logger.info("Starting bot polling...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling(
            allowed_updates=["channel_post", "edited_channel_post", "message", "edited_message"]
        )
        logger.info("Bot polling started")
    
    async def stop(self):
        """Останавливает бота"""
        logger.info("Stopping bot...")
        if self.application:
            try:
                # Проверяем, запущено ли приложение
                if hasattr(self.application, 'running') and self.application.running:
                    await self.application.stop()
                    await self.application.shutdown()
                else:
                    # Если приложение не запущено, просто выполняем shutdown
                    await self.application.shutdown()
            except RuntimeError as e:
                # Если приложение уже остановлено, просто продолжаем
                logger.debug(f"Application already stopped: {e}")
                try:
                    await self.application.shutdown()
                except Exception as e2:
                    logger.debug(f"Error during shutdown: {e2}")
            except Exception as e:
                logger.error(f"Error stopping application: {e}")
        logger.info("Bot stopped")

