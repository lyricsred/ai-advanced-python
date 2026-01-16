import logging
from telegram.ext import Application, MessageHandler, filters
from telegram import Update
from telegram.ext import ContextTypes
from bot.config.bot_config import BOT_TOKEN
from bot.utils import init_db
from bot.handlers import register_handlers

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def log_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message:
        message_text = update.message.text or update.message.caption or ''
        if message_text:
            logger.info(f'Получено сообщение: {message_text}')


def main() -> None:
    logger.info('Инициализация базы данных...')
    init_db()
    
    logger.info('Создание приложения бота...')
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(MessageHandler(filters.ALL, log_message), group=0)
    
    register_handlers(application)
    
    logger.info('Бот запущен и готов к работе!')
    application.run_polling()


if __name__ == '__main__':
    main()