from telegram.ext import Application

from bot.config.bot_config import BOT_TOKEN

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    application.run_polling()

if __name__ == '__main__':
    main()