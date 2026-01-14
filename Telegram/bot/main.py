from telegram.ext import Application
from bot.config.bot_config import BOT_TOKEN
from bot.utils import init_db
from bot.handlers import register_handlers


def main() -> None:
    init_db()
    application = Application.builder().token(BOT_TOKEN).build()

    register_handlers(application)
    
    application.run_polling()


if __name__ == '__main__':
    main()