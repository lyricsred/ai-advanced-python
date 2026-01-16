from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from bot.models import User
from bot.utils import get_session, calculate_water_goal, calculate_calorie_goal

WEIGHT, HEIGHT, AGE, GENDER, ACTIVITY, CITY = range(6)


async def set_profile_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        'Давайте настроим ваш профиль!\n\n'
        'Введите ваш вес (в кг):'
    )
    return WEIGHT


async def set_profile_weight(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        weight = float(update.message.text)
        if weight <= 0 or weight > 300:
            await update.message.reply_text('Пожалуйста, введите корректный вес (от 1 до 300 кг):')
            return WEIGHT
        context.user_data['weight'] = weight
        await update.message.reply_text('Введите ваш рост (в см):')
        return HEIGHT
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите число:')
        return WEIGHT


async def set_profile_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        height = float(update.message.text)
        if height <= 0 or height > 250:
            await update.message.reply_text('Пожалуйста, введите корректный рост (от 1 до 250 см):')
            return HEIGHT
        context.user_data['height'] = height
        await update.message.reply_text('Введите ваш возраст:')
        return AGE
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите число:')
        return HEIGHT


async def set_profile_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        age = int(update.message.text)
        if age <= 0 or age > 150:
            await update.message.reply_text('Пожалуйста, введите корректный возраст (от 1 до 150):')
            return AGE
        context.user_data['age'] = age
        await update.message.reply_text(
            'Введите ваш пол (мужской/женский или male/female):'
        )
        return GENDER
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите число:')
        return AGE


async def set_profile_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    gender_text = update.message.text.lower().strip()
    if gender_text in ['мужской', 'male', 'м', 'm']:
        context.user_data['gender'] = 'male'
    elif gender_text in ['женский', 'female', 'ж', 'f']:
        context.user_data['gender'] = 'female'
    else:
        await update.message.reply_text(
            'Пожалуйста, введите \'мужской\' или \'женский\' (или male/female):'
        )
        return GENDER
    
    await update.message.reply_text(
        'Сколько минут активности у вас в день?'
    )
    return ACTIVITY


async def set_profile_activity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        activity = int(update.message.text)
        if activity < 0:
            await update.message.reply_text('Пожалуйста, введите неотрицательное число:')
            return ACTIVITY
        context.user_data['activity_minutes'] = activity
        await update.message.reply_text('В каком городе вы находитесь?')
        return CITY
    except ValueError:
        await update.message.reply_text('Пожалуйста, введите число:')
        return ACTIVITY


async def set_profile_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    city = update.message.text.strip()
    context.user_data['city'] = city
    
    weight = context.user_data['weight']
    height = context.user_data['height']
    age = context.user_data['age']
    gender = context.user_data['gender']
    activity_minutes = context.user_data['activity_minutes']
    
    water_goal = calculate_water_goal(weight, activity_minutes)
    calorie_goal = calculate_calorie_goal(weight, height, age, gender, activity_minutes)
    
    session = get_session()
    try:
        user = session.query(User).filter_by(telegram_id=update.effective_user.id).first()
        
        if user:
            user.weight = weight
            user.height = height
            user.age = age
            user.gender = gender
            user.activity_minutes = activity_minutes
            user.city = city
            user.water_goal = water_goal
            user.calorie_goal = calorie_goal
        else:
            user = User(
                telegram_id=update.effective_user.id,
                weight=weight,
                height=height,
                age=age,
                gender=gender,
                activity_minutes=activity_minutes,
                city=city,
                water_goal=water_goal,
                calorie_goal=calorie_goal
            )
            session.add(user)
        
        session.commit()
        
        await update.message.reply_text(
            f'✅ Профиль успешно сохранён!\n\n'
            f'📊 Ваши данные:\n'
            f'Вес: {weight} кг\n'
            f'Рост: {height} см\n'
            f'Возраст: {age} лет\n'
            f'Пол: {"Мужской" if gender == "male" else "Женский"}\n'
            f'Активность: {activity_minutes} мин/день\n'
            f'Город: {city}\n\n'
            f'🎯 Ваши цели:\n'
            f'Вода: {water_goal:.0f} мл/день\n'
            f'Калории: {calorie_goal:.0f} ккал/день'
        )
    except Exception as e:
        session.rollback()
        await update.message.reply_text(f'❌ Ошибка при сохранении профиля: {e}')
    finally:
        session.close()
    
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text('Настройка профиля отменена.')
    return ConversationHandler.END

