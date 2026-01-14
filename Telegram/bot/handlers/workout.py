from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, date
from bot.models import User, WorkoutLog
from bot.utils import get_session, calculate_workout_calories


async def log_workout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 2:
        await update.message.reply_text(
            'Использование: /log_workout <тип тренировки> <время в минутах>\n'
            'Пример: /log_workout бег 30'
        )
        return
    
    try:
        workout_type = ' '.join(context.args[:-1])
        duration = int(context.args[-1])
        
        if duration <= 0:
            await update.message.reply_text('Время должно быть положительным числом!')
            return
        
        session = get_session()
        try:
            user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
            
            if not user:
                await update.message.reply_text(
                    '❌ Профиль не настроен. Используйте /set_profile для настройки.'
                )
                return
            
            calories_burned = calculate_workout_calories(workout_type, duration, user.weight)
            
            workout_log = WorkoutLog(
                user_id=user.id,
                workout_type=workout_type,
                duration=duration,
                calories_burned=calories_burned,
                logged_at=datetime.utcnow()
            )
            session.add(workout_log)
            session.commit()
            
            today = date.today()
            total_burned_today = sum(
                log.calories_burned for log in session.query(WorkoutLog).filter(
                    WorkoutLog.user_id == user.id,
                    WorkoutLog.logged_at >= datetime.combine(today, datetime.min.time())
                ).all()
            )
            
            extra_water = (duration // 30) * 200
            
            message = (
                f'🏃‍♂️ Тренировка записана!\n\n'
                f'Тип: {workout_type}\n'
                f'Время: {duration} минут\n'
                f'Сожжено: {calories_burned:.0f} ккал\n\n'
                f'📊 Сожжено за сегодня: {total_burned_today:.0f} ккал'
            )
            
            if extra_water > 0:
                message += f'\n\n💧 Рекомендуется выпить дополнительно {extra_water} мл воды'
            
            await update.message.reply_text(message)
        except Exception as e:
            session.rollback()
            await update.message.reply_text(f'❌ Ошибка: {e}')
        finally:
            session.close()
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите корректное время (число)!')

