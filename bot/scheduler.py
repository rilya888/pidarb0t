import asyncio
import random
from datetime import datetime, time as dt_time
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bot.chatgpt_client import ChatGPTClient


class SchedulerManager:
    """Управляет запланированными постами бота"""
    
    def __init__(self, bot_instance):
        self.bot_instance = bot_instance
        self.scheduler = AsyncIOScheduler()
        self.chatgpt_client = ChatGPTClient()
        self.channel_id = None
        
    def set_channel_id(self, channel_id: str):
        """Устанавливает ID канала"""
        self.channel_id = channel_id
    
    async def post_random_content(self):
        """Отправляет рандомный пост в канал"""
        if not self.channel_id:
            logger.error("Channel ID not set!")
            return
        
        try:
            # Проверяем, действительно ли канал тихий
            if self.bot_instance.monitor.is_channel_active():
                logger.info("Channel is active, skipping scheduled post")
                return
            
            logger.info("Posting random content to channel")
            content = await self.chatgpt_client.generate_random_content()
            
            # Используем метод бота для отправки сообщения
            if hasattr(self.bot_instance, 'application'):
                bot = self.bot_instance.application.bot
                await bot.send_message(
                    chat_id=self.channel_id,
                    text=content
                )
                logger.success("Scheduled post sent successfully")
            
        except Exception as e:
            logger.error(f"Error posting scheduled content: {e}")
    
    def schedule_posts(self, posts_config):
        """Настраивает расписание постов"""
        for post in posts_config:
            hour = post["hour"]
            minute = post["minute"]
            
            # Добавляем рандомный offset ±30 минут
            offset = random.randint(-30, 30)
            final_minute = minute + offset
            
            # Обрабатываем переполнение
            if final_minute < 0:
                final_minute += 60
                hour -= 1
            elif final_minute >= 60:
                final_minute -= 60
                hour += 1
            
            hour = max(0, min(23, hour))
            final_minute = max(0, min(59, final_minute))
            
            logger.info(f"Scheduling post at {hour:02d}:{final_minute:02d}")
            
            self.scheduler.add_job(
                self.post_random_content,
                CronTrigger(hour=hour, minute=final_minute),
                id=f"post_{hour}_{final_minute}"
            )
    
    def start(self, posts_config):
        """Запускает планировщик"""
        self.schedule_posts(posts_config)
        self.scheduler.start()
        logger.info("Scheduler started")
    
    def shutdown(self):
        """Останавливает планировщик"""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")

