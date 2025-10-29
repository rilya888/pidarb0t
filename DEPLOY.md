# 🚀 Быстрая инструкция по деплою

## Railway - один клик

### 1. Подключи GitHub
- Иди на [railway.app](https://railway.app)
- Войди через GitHub
- **New Project** → **Deploy from GitHub repo**
- Выбери `rilya888/pidarb0t`

### 2. Добавь переменные
В настройках проекта → Variables:

```env
TELEGRAM_BOT_TOKEN=ваш_токен
OPENAI_API_KEY=ваш_ключ  
TELEGRAM_CHANNEL_ID=-1003122131444
```

### 3. Готово!
Railway автоматически:
- ✅ Установит Python 3.11 (из runtime.txt)
- ✅ Установит зависимости (из requirements.txt)
- ✅ Запустит бота (из Procfile)

## Проверка

Открой логи в Railway dashboard - должны увидеть:
```
Bot initialized: @pid0r0_bot
Bot polling started
```

Отправь сообщения в канал - бот ответит!

