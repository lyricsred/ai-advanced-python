from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, date
from bot.models import User, WaterLog, FoodLog, WorkoutLog
from bot.utils import get_session


async def check_progress(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    session = get_session()
    try:
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
        
        if not user:
            await update.message.reply_text(
                '❌ Профиль не настроен. Используйте /set_profile для настройки.'
            )
            return
        
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())
        
        water_logs = session.query(WaterLog).filter(
            WaterLog.user_id == user.id,
            WaterLog.logged_at >= today_start
        ).all()
        total_water = sum(log.amount for log in water_logs)
        water_remaining = max(0, user.water_goal - total_water)
        water_percentage = (total_water / user.water_goal * 100) if user.water_goal > 0 else 0
        
        food_logs = session.query(FoodLog).filter(
            FoodLog.user_id == user.id,
            FoodLog.logged_at >= today_start
        ).all()
        total_calories_consumed = sum(log.calories for log in food_logs)
        
        workout_logs = session.query(WorkoutLog).filter(
            WorkoutLog.user_id == user.id,
            WorkoutLog.logged_at >= today_start
        ).all()
        total_calories_burned = sum(log.calories_burned for log in workout_logs)
        
        calorie_balance = total_calories_consumed - total_calories_burned
        calorie_remaining = user.calorie_goal - calorie_balance
        calorie_percentage = (calorie_balance / user.calorie_goal * 100) if user.calorie_goal > 0 else 0
        
        message = '📊 Ваш прогресс на сегодня:\n\n'
        
        water_emoji = '✅' if total_water >= user.water_goal else '💧'
        message += (
            f'{water_emoji} Вода:\n'
            f'Выпито: {total_water:.0f} мл из {user.water_goal:.0f} мл\n'
            f'Осталось: {water_remaining:.0f} мл\n'
            f'Прогресс: {water_percentage:.1f}%\n\n'
        )
        
        calorie_emoji = '✅' if calorie_balance <= user.calorie_goal else '⚠️'
        message += (
            f'{calorie_emoji} Калории:\n'
            f'Потреблено: {total_calories_consumed:.0f} ккал\n'
            f'Сожжено: {total_calories_burned:.0f} ккал\n'
            f'Баланс: {calorie_balance:.0f} ккал\n'
            f'Цель: {user.calorie_goal:.0f} ккал\n'
        )
        
        if calorie_remaining > 0:
            message += f'Осталось: {calorie_remaining:.0f} ккал\n'
        else:
            message += f'Превышено на: {abs(calorie_remaining):.0f} ккал\n'
        
        message += f'Прогресс: {calorie_percentage:.1f}%'
        
        await update.message.reply_text(message)
    except Exception as e:
        await update.message.reply_text(f'❌ Ошибка: {e}')
    finally:
        session.close()
