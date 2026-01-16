from telegram.ext import Application
from bot.config.bot_config import BOT_TOKEN
from bot.utils import init_db, logger
from bot.handlers import register_handlers


def main() -> None:
    logger.info('Инициализация базы данных...')
    init_db()
    
    logger.info('Создание приложения бота...')
    application = Application.builder().token(BOT_TOKEN).build()
    
    register_handlers(application)
    
    logger.info('Бот запущен и готов к работе!')
    application.run_polling()


if __name__ == '__main__':
    main()