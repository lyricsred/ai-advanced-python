from telegram import Update
from telegram.ext import ContextTypes
from bot.utils import logger


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f'Получено сообщение: /start')
    welcome_message = (
        '👋 Привет! Я бот для отслеживания воды, калорий и активности.\n\n'
        '📋 Доступные команды:\n'
        '/set_profile - Настроить профиль\n'
        '/log_water <количество> - Записать выпитую воду (в мл)\n'
        '/log_food <название продукта> - Записать съеденную еду\n'
        '/log_workout <тип> <время> - Записать тренировку (время в минутах)\n'
        '/check_progress - Проверить прогресс\n\n'
        'Начните с команды /set_profile для настройки профиля!'
    )
    await update.message.reply_text(welcome_message)

