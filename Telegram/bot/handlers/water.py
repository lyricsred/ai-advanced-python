from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, date
from bot.models import User, WaterLog
from bot.utils import get_session, logger


async def log_water(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message_text = '/log_water ' + ' '.join(context.args) if context.args else '/log_water'
    logger.info(f'Получено сообщение: {message_text}')
    
    if not context.args:
        await update.message.reply_text(
            "Использование: /log_water <количество>\n"
            "Пример: /log_water 500"
        )
        return
    
    try:
        amount = float(context.args[0])
        if amount <= 0:
            await update.message.reply_text("Количество должно быть положительным числом!")
            return
        
        session = get_session()
        try:
            user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
            
            if not user:
                await update.message.reply_text(
                    "❌ Профиль не настроен. Используйте /set_profile для настройки."
                )
                return
            
            # Создаём запись о воде
            water_log = WaterLog(
                user_id=user.id,
                amount=amount,
                logged_at=datetime.utcnow()
            )
            session.add(water_log)
            session.commit()
            
            # Подсчитываем выпитую воду за сегодня
            today = date.today()
            total_water = sum(
                log.amount for log in session.query(WaterLog).filter(
                    WaterLog.user_id == user.id,
                    WaterLog.logged_at >= datetime.combine(today, datetime.min.time())
                ).all()
            )
            
            remaining = max(0, user.water_goal - total_water)
            
            await update.message.reply_text(
                f"💧 Записано: {amount:.0f} мл воды\n\n"
                f"📊 Прогресс:\n"
                f"Выпито: {total_water:.0f} мл из {user.water_goal:.0f} мл\n"
                f"Осталось: {remaining:.0f} мл"
            )
        except Exception as e:
            session.rollback()
            await update.message.reply_text(f"❌ Ошибка: {e}")
        finally:
            session.close()
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число!")

