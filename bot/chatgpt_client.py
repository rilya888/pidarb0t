from openai import OpenAI
from loguru import logger
import random
from bot.config import OPENAI_API_KEY, OPENAI_MODEL, JOKE_PROMPT, MEME_PROMPT, COMMENT_PROMPT_TEMPLATE, MENTION_PROMPT_TEMPLATE, STETHEM_QUOTES


class ChatGPTClient:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = OPENAI_MODEL
        logger.info("ChatGPT client initialized")
    
    async def generate_joke(self) -> str:
        """Генерирует пошлую шутку/анекдот"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ты гопник-матершинник из плохого района."},
                    {"role": "user", "content": JOKE_PROMPT}
                ],
                temperature=0.9,
                max_tokens=200
            )
            
            joke = response.choices[0].message.content.strip()
            logger.info(f"Generated joke: {joke[:50]}...")
            return joke
            
        except Exception as e:
            logger.error(f"Error generating joke: {e}")
            return "Эх, сегодня не до шуток... Твоя мать в отпуске, так что и я в отпуске от остроумия."
    
    async def generate_meme_quote(self) -> str:
        """Генерирует мемную цитату в стиле Стетхема"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ты гопник-матершинник из плохого района в стиле Стетхема."},
                    {"role": "user", "content": MEME_PROMPT}
                ],
                temperature=0.9,
                max_tokens=150
            )
            
            quote = response.choices[0].message.content.strip()
            logger.info(f"Generated meme quote: {quote[:50]}...")
            return quote
            
        except Exception as e:
            logger.error(f"Error generating meme quote: {e}")
            # Fallback на готовые цитаты
            return random.choice(STETHEM_QUOTES)
    
    async def generate_random_content(self) -> str:
        """Генерирует случайный контент (шутка или мемная цитата)"""
        content_type = random.choice(["joke", "meme"])
        
        if content_type == "joke":
            return await self.generate_joke()
        else:
            return await self.generate_meme_quote()
    
    async def generate_comment(self, conversation_context: str) -> str:
        """Генерирует грубый комментарий на тему обсуждения"""
        try:
            prompt = COMMENT_PROMPT_TEMPLATE.format(conversation_context=conversation_context)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ты гопник-матершинник из плохого района."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9,
                max_tokens=150
            )
            
            comment = response.choices[0].message.content.strip()
            logger.info(f"Generated comment: {comment[:50]}...")
            return comment
            
        except Exception as e:
            logger.error(f"Error generating comment: {e}")
            return "Ясно, понятно. Короче, решил я пофилософствовать тут с вами, интеллигентами..."
    
    async def generate_mention_response(self, message_text: str, username: str = "пользователь") -> str:
        """Генерирует грубый ответ на обращение пользователя"""
        try:
            prompt = MENTION_PROMPT_TEMPLATE.format(
                username=username,
                message_text=message_text
            )
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ты гопник-матершинник из плохого района."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9,
                max_tokens=150
            )
            
            response_text = response.choices[0].message.content.strip()
            logger.info(f"Generated mention response: {response_text[:50]}...")
            return response_text
            
        except Exception as e:
            logger.error(f"Error generating mention response: {e}")
            return "Ясно, понятно. Короче, решил я тут пофилософствовать с вами, интеллигентами..."

