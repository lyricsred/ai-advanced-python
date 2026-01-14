from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters
from bot.handlers.start import start_command
from bot.handlers.profile import (
    set_profile_start,
    set_profile_weight,
    set_profile_height,
    set_profile_age,
    set_profile_gender,
    set_profile_activity,
    set_profile_city,
    cancel
)
from bot.handlers.water import log_water
from bot.handlers.food import log_food_start, log_food_amount, cancel_food
from bot.handlers.workout import log_workout
from bot.handlers.progress import check_progress
from bot.handlers.profile import WEIGHT, HEIGHT, AGE, GENDER, ACTIVITY, CITY
from bot.handlers.food import FOOD_AMOUNT


def get_profile_handler():
    return ConversationHandler(
        entry_points=[CommandHandler('set_profile', set_profile_start)],
        states={
            WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_profile_weight)],
            HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_profile_height)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_profile_age)],
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_profile_gender)],
            ACTIVITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_profile_activity)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_profile_city)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )


def get_food_handler():
    return ConversationHandler(
        entry_points=[CommandHandler('log_food', log_food_start)],
        states={
            FOOD_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, log_food_amount)],
        },
        fallbacks=[CommandHandler('cancel', cancel_food)],
    )


def register_handlers(application):
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(get_profile_handler())
    application.add_handler(CommandHandler('log_water', log_water))
    application.add_handler(get_food_handler())
    application.add_handler(CommandHandler('log_workout', log_workout))
    application.add_handler(CommandHandler('check_progress', check_progress))
