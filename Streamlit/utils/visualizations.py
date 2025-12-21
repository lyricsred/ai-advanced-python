import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


def plot_temperature_timeseries(
    data: pd.DataFrame, city: str, show_anomalies: bool = True
) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(
        data["timestamp"],
        data["temperature"],
        color="lightblue",
        linewidth=1,
        label="Температура",
        alpha=0.7,
    )

    if "moving_avg" in data.columns:
        ax.plot(
            data["timestamp"],
            data["moving_avg"],
            color="blue",
            linewidth=2,
            label="Скользящее среднее (30 дней)",
        )

    if show_anomalies and "anomaly" in data.columns:
        anomalies_data = data[data["anomaly"]]
        if len(anomalies_data) > 0:
            ax.scatter(
                anomalies_data["timestamp"],
                anomalies_data["temperature"],
                color="red",
                s=50,
                marker="x",
                linewidths=2,
                label="Аномалии",
                zorder=5,
            )

    ax.set_xlabel("Дата", fontsize=12)
    ax.set_ylabel("Температура (°C)", fontsize=12)
    ax.set_title(f"Временной ряд температуры: {city}", fontsize=14, fontweight="bold")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))

    plt.xticks(rotation=45)
    plt.tight_layout()

    return fig


def plot_seasonal_profiles(seasonal_stats: pd.DataFrame, city: str) -> plt.Figure:
    city_stats = seasonal_stats[seasonal_stats["city"] == city].copy()

    season_order = ["winter", "spring", "summer", "autumn"]
    season_names = {"winter": "Зима", "spring": "Весна", "summer": "Лето", "autumn": "Осень"}

    city_stats["season_order"] = city_stats["season"].map(
        {season: i for i, season in enumerate(season_order)}
    )
    city_stats = city_stats.sort_values("season_order")

    fig, ax = plt.subplots(figsize=(10, 6))

    seasons = [season_names[s] for s in city_stats["season"]]
    mean_temps = city_stats["mean_temp"].values
    std_temps = city_stats["std_temp"].values

    ax.errorbar(
        seasons,
        mean_temps,
        yerr=std_temps,
        fmt="o-",
        color="blue",
        linewidth=3,
        markersize=10,
        capsize=5,
        capthick=2,
        label="Средняя температура ± σ",
    )

    upper_bound = mean_temps + 2 * std_temps
    lower_bound = mean_temps - 2 * std_temps

    ax.plot(
        seasons, upper_bound, "--", color="lightblue", linewidth=1.5, label="Верхняя граница (±2σ)"
    )
    ax.plot(
        seasons, lower_bound, "--", color="lightblue", linewidth=1.5, label="Нижняя граница (±2σ)"
    )
    ax.fill_between(seasons, lower_bound, upper_bound, color="lightblue", alpha=0.2)
    ax.set_xlabel("Сезон", fontsize=12)
    ax.set_ylabel("Температура (°C)", fontsize=12)
    ax.set_title(f"Сезонные профили температуры: {city}", fontsize=14, fontweight="bold")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    return fig


def plot_temperature_distribution(data: pd.DataFrame, city: str) -> plt.Figure:
    city_data = data[data["city"] == city]

    fig, ax = plt.subplots(figsize=(10, 6))

    ax.hist(
        city_data["temperature"],
        bins=50,
        color="skyblue",
        alpha=0.7,
        edgecolor="black",
        linewidth=0.5,
    )

    mean_temp = city_data["temperature"].mean()

    ax.axvline(
        mean_temp, color="red", linestyle="--", linewidth=2, label=f"Среднее: {mean_temp:.2f}°C"
    )
    ax.set_xlabel("Температура (°C)", fontsize=12)
    ax.set_ylabel("Частота", fontsize=12)
    ax.set_title(f"Распределение температуры: {city}", fontsize=14, fontweight="bold")
    ax.legend(loc="best")
    ax.grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    return fig


def plot_anomaly_timeline(data: pd.DataFrame, city: str) -> plt.Figure:
    city_data = data[data["city"] == city].copy()
    city_data = city_data.sort_values("timestamp")

    city_data["year_month"] = pd.to_datetime(city_data["timestamp"]).dt.to_period("M")
    monthly_anomalies = city_data.groupby("year_month")["anomaly"].sum().reset_index()
    monthly_anomalies["year_month"] = monthly_anomalies["year_month"].astype(str)

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.bar(
        monthly_anomalies["year_month"],
        monthly_anomalies["anomaly"],
        color="coral",
        alpha=0.7,
        edgecolor="black",
        linewidth=0.5,
    )
    ax.set_xlabel("Месяц", fontsize=12)
    ax.set_ylabel("Количество аномалий", fontsize=12)
    ax.set_title(f"Временная линия аномалий: {city}", fontsize=14, fontweight="bold")
    ax.grid(True, alpha=0.3, axis="y")

    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    return fig
