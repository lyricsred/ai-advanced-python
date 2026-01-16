import requests

from bot.config import OPEN_FOOD_FACTS_URL

class FoodClient:
    def __init__(self):
        self.base_url = OPEN_FOOD_FACTS_URL
    
    def get_food_info(self, product_name: str) -> dict:
        try:
            params = {
                'action': 'process',
                'search_terms': product_name,
                'json': 'true'
            }
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                products = data.get('products', [])
                
                if products:
                    first_product = products[0]
                    nutriments = first_product.get('nutriments', {})

                    calories = (
                        nutriments.get('energy-kcal_100g') or
                        nutriments.get('energy-kcal') or
                        (nutriments.get('energy') or 0) / 4.184
                    )
                    
                    product_name_display = (
                        first_product.get('product_name') or
                        first_product.get('product_name_en') or
                        first_product.get('product_name_ru') or
                        product_name
                    )
                    
                    return {
                        'name': product_name_display,
                        'calories': float(calories) if calories else 0
                    }
            
            return None
        except Exception as e:
            print(f"Ошибка при получении информации о продукте: {e}")
            return None

