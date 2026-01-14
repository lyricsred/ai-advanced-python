def calculate_water_goal(weight: float, activity_minutes: int) -> float:
    base_water = weight * 30

    activity_water = (activity_minutes // 30) * 500
    
    total_water = base_water + activity_water
    
    return round(total_water, 1)


def calculate_calorie_goal(weight: float, height: float, age: int, gender: str, activity_minutes: int) -> float:
    bmr = 10 * weight + 6.25 * height - 5 * age
    
    if gender.lower() == 'male':
        bmr += 5
    else:
        bmr -= 161

    if activity_minutes < 30:
        activity_factor = 1.2
    elif activity_minutes < 60:
        activity_factor = 1.375
    elif activity_minutes < 90:
        activity_factor = 1.55
    else:
        activity_factor = 1.725
    
    total_calories = bmr * activity_factor
    
    return round(total_calories, 1)


def calculate_workout_calories(workout_type: str, duration: int, weight: float) -> float:
    met_values = {
        'бег': 8,
        'running': 8,
        'run': 8,
        'ходьба': 3.5,
        'walking': 3.5,
        'walk': 3.5,
        'велосипед': 6,
        'cycling': 6,
        'bike': 6,
        'плавание': 7,
        'swimming': 7,
        'swim': 7,
        'силовые': 5,
        'strength': 5,
        'weights': 5,
        'йога': 3,
        'yoga': 3,
        'тренировка': 5,
        'workout': 5,
    }
    
    workout_lower = workout_type.lower().strip()
    met = met_values.get(workout_lower, 5)

    hours = duration / 60
    calories = met * weight * hours
    
    return round(calories, 1)

