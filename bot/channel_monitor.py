import time
from typing import List, Optional
from loguru import logger


class ChannelMonitor:
    """Мониторит активность в канале"""
    
    def __init__(self, activity_timeout: int = 3600):
        self.activity_timeout = activity_timeout
        self.last_user_message_time: Optional[float] = None
        self.message_counter = 0
        self.bot_user_id = None
        
    def set_bot_id(self, bot_id: int):
        """Устанавливает ID бота для исключения его сообщений из подсчета"""
        self.bot_user_id = bot_id
        logger.info(f"Bot ID set: {bot_id}")
    
    def update_last_activity(self, user_id: int):
        """Обновляет время последней активности"""
        if user_id != self.bot_user_id:
            self.last_user_message_time = time.time()
            self.message_counter += 1
            logger.debug(f"Activity updated. Counter: {self.message_counter}")
    
    def is_channel_active(self) -> bool:
        """Проверяет, активен ли канал"""
        if self.last_user_message_time is None:
            return False
        
        time_since_last_message = time.time() - self.last_user_message_time
        is_active = time_since_last_message < self.activity_timeout
        logger.debug(f"Channel active: {is_active}, time since last: {time_since_last_message}s")
        return is_active
    
    def should_bot_respond(self, threshold_min: int, threshold_max: int) -> bool:
        """Проверяет, должен ли бот ответить (по количеству сообщений)"""
        if not self.is_channel_active():
            return False
        
        should_respond = threshold_min <= self.message_counter <= threshold_max
        if should_respond:
            logger.info(f"Bot should respond! Counter: {self.message_counter}")
        
        return should_respond
    
    def reset_counter(self):
        """Сбрасывает счетчик сообщений"""
        self.message_counter = 0
        logger.debug("Counter reset")

