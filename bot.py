import json
import config
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# 1. Функция загрузки базы данных из JSON
def load_db():
    with open('database.json', 'r', encoding='utf-8') as f:
        return json.load(f)

# 2. Определение намерения (Intent Detection) по ТЗ
def detect_intent(text, db):
    text = text.lower()
    # Проверяем на токсичность
    for word in db['intents']['toxic']:
        if word in text: return "TOXIC"
    # Проверяем на спам
    for word in db['intents']['spam']:
        if word in text: return "SPAM"
    # Если плохих слов нет — считаем запрос правовым
    return "LEGAL"

# 3. Поиск правила в законах (Конституция и УК)
def find_rule(text, db):
    text = text.lower()
    # Сначала ищем в УК (запрещенное)
    for rule in db['uk']:
        for key in rule['keywords']:
            if key in text: return rule
    # Затем в Конституции (разрешенное)
    for rule in db['constitution']:
        for key in rule['keywords']:
            if key in text: return rule
    return None

# 4. Основной обработчик сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    db = load_db()
    user_text = update.message.text
    user_id = update.effective_user.id
    
    intent = detect_intent(user_text, db)

    # Логика поведения по ТЗ: игнор игрока + уведомление админу
    if intent in ["TOXIC", "SPAM"]:
        await context.bot.send_message(
            chat_id=config.ADMIN_ID,
            text=f"⚠️ СИСТЕМА ФИЛЬТРАЦИИ\nТип: {intent}\nUser ID: {user_id}\nТекст: {user_text}"
        )
        return # Просто выходим, ничего не отвечая пользователю

    # Если запрос LEGAL — ищем ответ в базе данных
    rule = find_rule(user_text, db)
    
    if rule:
        status_icon = "✅" if rule['result'] == "ALLOWED" else "🚫"
        response = (
            f"{status_icon} ЮРИДИЧЕСКИЙ СТАТУС: {rule['result']}\n\n"
            f"Норма закона:\n\"{rule['text']}\""
        )
    else:
        response = "⚖️ СТАТУС: UNKNOWN\nВ базе правил не найдено совпадений по вашему запросу."
    
    await update.message.reply_text(response)

# 5. Точка запуска бота
if __name__ == '__main__':
    print("--- Бот запущен и охраняет сервер ---")
    
    # Создаем приложение и передаем ему токен из конфига
    app = Application.builder().token(config.TOKEN).build()
    
    # Говорим боту реагировать на любой текст (кроме команд)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бесконечный цикл проверки сообщений
    app.run_polling()
