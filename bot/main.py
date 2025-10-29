#!/usr/bin/env python3
"""Главный файл запуска бота"""
import asyncio
import signal
from loguru import logger

import bot.config as config
from bot.telegram_handler import TelegramBotHandler
from bot.scheduler import SchedulerManager


class BotApplication:
    """Главный класс приложения"""
    
    def __init__(self):
        self.config = config
        self.telegram_handler = None
        self.scheduler = None
        self.running = True
        
    async def initialize(self):
        """Инициализация компонентов"""
        logger.info("Initializing bot application...")
        
        # Инициализируем Telegram handler
        self.telegram_handler = TelegramBotHandler(self.config)
        await self.telegram_handler.initialize()
        
        # Инициализируем планировщик
        self.scheduler = SchedulerManager(self.telegram_handler)
        self.scheduler.set_channel_id(self.config.CHANNEL_ID)
        self.scheduler.start(self.config.SCHEDULED_POSTS)
        
        logger.info("Bot application initialized")
    
    async def run(self):
        """Запускает бота"""
        try:
            await self.initialize()
            
            # Создаем задачу для polling
            polling_task = asyncio.create_task(self.telegram_handler.start_polling())
            
            # Ждем сигнал остановки
            while self.running:
                await asyncio.sleep(0.5)
            
            # Отменяем polling при остановке
            polling_task.cancel()
            try:
                await polling_task
            except asyncio.CancelledError:
                logger.info("Polling task cancelled")
                
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
        except Exception as e:
            logger.error(f"Error in run loop: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Останавливает бота"""
        logger.info("Shutting down...")
        
        if self.scheduler:
            self.scheduler.shutdown()
        
        if self.telegram_handler:
            await self.telegram_handler.stop()
        
        logger.info("Shutdown complete")
    
    def stop(self):
        """Устанавливает флаг остановки"""
        self.running = False


async def main():
    """Главная функция"""
    # Настройка логирования
    logger.add(
        "logs/bot_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="7 days",
        level="INFO"
    )
    
    logger.info("=" * 50)
    logger.info("Starting Pid0r Bot...")
    logger.info("=" * 50)
    
    app = BotApplication()
    
    # Обработка сигналов для graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        app.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())

