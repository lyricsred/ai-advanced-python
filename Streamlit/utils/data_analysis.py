from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Dict, Tuple

import numpy as np
import pandas as pd
import time


def calculate_moving_average(data: pd.DataFrame, window: int = 30) -> pd.Series:
    return data["temperature"].rolling(window=window, center=True).mean()


def calculate_seasonal_statistics(data: pd.DataFrame) -> pd.DataFrame:
    seasonal_stats = (
        data.groupby(["city", "season"]).agg({"temperature": ["mean", "std"]}).reset_index()
    )
    seasonal_stats.columns = ["city", "season", "mean_temp", "std_temp"]

    return seasonal_stats


def detect_anomalies(
    data: pd.DataFrame, moving_avg: pd.Series, threshold_std: float = 2.0
) -> pd.Series:
    residuals = data["temperature"] - moving_avg
    std_residuals = residuals.std()
    anomalies = np.abs(residuals) > (threshold_std * std_residuals)

    return anomalies


def analyze_city_data(
    city_data: pd.DataFrame, window: int = 30, threshold_std: float = 2.0
) -> Dict:
    city_data = city_data.sort_values("timestamp").reset_index(drop=True)
    moving_avg = calculate_moving_average(city_data, window)
    anomalies = detect_anomalies(city_data, moving_avg, threshold_std)
    seasonal_stats = calculate_seasonal_statistics(city_data)
    city_data = city_data.copy()
    city_data["moving_avg"] = moving_avg
    city_data["anomaly"] = anomalies

    return {
        "data": city_data,
        "seasonal_stats": seasonal_stats,
        "anomaly_count": anomalies.sum(),
        "total_measurements": len(city_data),
    }


def analyze_data_sequential(
    data: pd.DataFrame, window: int = 30, threshold_std: float = 2.0
) -> Dict[str, Dict]:
    results = {}
    cities = data["city"].unique()
    for city in cities:
        city_data = data[data["city"] == city].copy()
        results[city] = analyze_city_data(city_data, window, threshold_std)

    return results


def analyze_city_wrapper(args: Tuple) -> Tuple[str, Dict]:
    city, city_data, window, threshold_std = args
    results = analyze_city_data(city_data, window, threshold_std)

    return city, results


def analyze_data_parallel(
    data: pd.DataFrame, window: int = 30, threshold_std: float = 2.0, method: str = "process"
) -> Dict[str, Dict]:
    cities = data["city"].unique()
    args_list = [
        (city, data[data["city"] == city].copy(), window, threshold_std) for city in cities
    ]
    executor_class = ProcessPoolExecutor if method == "process" else ThreadPoolExecutor
    results = {}
    with executor_class() as executor:
        futures = executor.map(analyze_city_wrapper, args_list)
        for city, result in futures:
            results[city] = result

    return results


def compare_parallelization_performance(
    data: pd.DataFrame, window: int = 30, threshold_std: float = 2.0
) -> Dict[str, float]:
    performance = {}

    start = time.time()
    analyze_data_sequential(data, window, threshold_std)
    performance["sequential"] = time.time() - start

    start = time.time()
    analyze_data_parallel(data, window, threshold_std, method="process")
    performance["parallel_process"] = time.time() - start

    start = time.time()
    analyze_data_parallel(data, window, threshold_std, method="thread")
    performance["parallel_thread"] = time.time() - start

    return performance


def get_seasonal_normal_range(
    seasonal_stats: pd.DataFrame, city: str, season: str
) -> Tuple[float, float]:
    city_season_stats = seasonal_stats[
        (seasonal_stats["city"] == city) & (seasonal_stats["season"] == season)
    ]

    if len(city_season_stats) == 0:
        return None, None

    mean_temp = city_season_stats["mean_temp"].iloc[0]
    std_temp = city_season_stats["std_temp"].iloc[0]

    return mean_temp - 2 * std_temp, mean_temp + 2 * std_temp
