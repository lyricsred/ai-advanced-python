import requests
import aiohttp
import asyncio
from datetime import datetime
from typing import Optional, Dict, Tuple
import time


def get_current_temperature_sync(city: str, api_key: str) -> Tuple[Optional[float], Optional[str]]:
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': city,
        'appid': api_key,
        'units': 'metric'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        temperature = data['main']['temp']
        return temperature, None
        
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            error_msg = "Invalid API key. Please see https://openweathermap.org/faq#error401 for more info."
            return None, error_msg
        return None, f"HTTP Error: {str(e)}"
    except requests.exceptions.RequestException as e:
        return None, f"Request Error: {str(e)}"
    except KeyError:
        return None, "Unexpected response format from API"
    except Exception as e:
        return None, f"Error: {str(e)}"


async def get_current_temperature_async(city: str, api_key: str) -> Tuple[Optional[float], Optional[str]]:
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': city,
        'appid': api_key,
        'units': 'metric'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 401:
                    error_msg = "Invalid API key. Please see https://openweathermap.org/faq#error401 for more info."
                    return None, error_msg
                
                response.raise_for_status()
                data = await response.json()
                temperature = data['main']['temp']
                return temperature, None      
    except aiohttp.ClientError as e:
        return None, f"Client Error: {str(e)}"
    except asyncio.TimeoutError:
        return None, "Request timeout"
    except KeyError:
        return None, "Unexpected response format from API"
    except Exception as e:
        return None, f"Error: {str(e)}"


def get_current_temperature_async_wrapper(city: str, api_key: str) -> Tuple[Optional[float], Optional[str]]:
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(get_current_temperature_async(city, api_key))


async def get_multiple_temperatures_async(cities: list, api_key: str) -> Dict[str, Tuple[Optional[float], Optional[str]]]:
    tasks = [get_current_temperature_async(city, api_key) for city in cities]
    results = await asyncio.gather(*tasks)
    
    return {city: result for city, result in zip(cities, results)}


def compare_sync_async_performance(cities: list, api_key: str) -> Dict[str, float]:
    performance = {}

    start = time.time()
    for city in cities:
        get_current_temperature_sync(city, api_key)
    performance['sync'] = time.time() - start

    start = time.time()
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.run_until_complete(get_multiple_temperatures_async(cities, api_key))
    performance['async'] = time.time() - start
    
    return performance


def get_current_season() -> str:
    month = datetime.now().month
    
    month_to_season = {
        12: "winter", 1: "winter", 2: "winter",
        3: "spring", 4: "spring", 5: "spring",
        6: "summer", 7: "summer", 8: "summer",
        9: "autumn", 10: "autumn", 11: "autumn"
    }
    
    return month_to_season[month]

