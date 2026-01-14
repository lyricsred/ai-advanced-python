from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime, date
from bot.models import User, FoodLog
from bot.utils import get_session
from bot.clients import FoodClient

FOOD_AMOUNT = 1


async def log_food_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not context.args:
        await update.message.reply_text(
            'Использование: /log_food <название продукта>\n'
            'Пример: /log_food банан'
        )
        return ConversationHandler.END
    
    product_name = ' '.join(context.args)
    context.user_data['product_name'] = product_name
    
    food_client = FoodClient()
    food_info = food_client.get_food_info(product_name)
    
    if not food_info or food_info['calories'] == 0:
        await update.message.reply_text(
            f'❌ Не удалось найти информацию о продукте '{product_name}'.\n'
            f'Попробуйте использовать английское название или другой продукт.'
        )
        return ConversationHandler.END
    
    context.user_data['food_info'] = food_info
    await update.message.reply_text(
        f'🍽 {food_info['name']} — {food_info['calories']:.0f} ккал на 100 г.\n\n'
        f'Сколько грамм вы съели?'
    )
    return FOOD_AMOUNT


async def log_food_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        amount = float(update.message.text)
        if amount <= 0:
            await update.message.reply_text('Количество должно быть положительным числом!')
            return FOOD_AMOUNT
        
        food_info = context.user_data.get('food_info')
        product_name = context.user_data.get('product_name')
        
        if not food_info:
            await update.message.reply_text('Произошла ошибка. Попробуйте снова.')
            return ConversationHandler.END
        
        calories_per_100g = food_info['calories']
        total_calories = (calories_per_100g * amount) / 100
        
        session = get_session()
        try:
            user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
            
            if not user:
                await update.message.reply_text(
                    '❌ Профиль не настроен. Используйте /set_profile для настройки.'
                )
                return ConversationHandler.END
            
            food_log = FoodLog(
                user_id=user.id,
                product_name=product_name,
                calories=total_calories,
                amount=amount,
                logged_at=datetime.utcnow()
            )
            session.add(food_log)
            session.commit()
            
            today = date.today()
            total_calories_today = sum(
                log.calories for log in session.query(FoodLog).filter(
                    FoodLog.user_id == user.id,
                    FoodLog.logged_at >= datetime.combine(today, datetime.min.time())
                ).all()
            )
            
            await update.message.reply_text(
                f'✅ Записано: {total_calories:.1f} ккал ({amount:.0f} г {food_info['name']})\n\n'
                f'📊 Потреблено за сегодня: {total_calories_today:.0f} ккал'
            )
        except Exception as e:
            session.rollback()
            await update.message.reply_text(f'❌ Ошибка: {e}')
        finally:
            session.close()
        
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите число!')
        return FOOD_AMOUNT


async def cancel_food(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Логирование еды отменено.')
    return ConversationHandler.END

