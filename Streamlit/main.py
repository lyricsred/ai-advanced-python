import pandas as pd
import numpy as np
import streamlit as st
from utils.data_analysis import (
    analyze_data_sequential,
    analyze_data_parallel,
    compare_parallelization_performance,
    get_seasonal_normal_range
)
from utils.weather_api import (
    get_current_temperature_sync,
    get_current_temperature_async_wrapper,
    get_current_season,
    compare_sync_async_performance
)
from utils.visualizations import (
    plot_temperature_timeseries,
    plot_seasonal_profiles,
    plot_temperature_distribution,
    plot_anomaly_timeline
)

st.set_page_config(
    page_title="Анализ температурных данных",
    page_icon="🌡️",
    layout="wide"
)

st.title('🌡️ Анализ температурных данных')
st.markdown('---')

st.header('📁 Загрузка данных')
uploaded_file = st.file_uploader('Выберите CSV-файл с температурными данными', type='csv')

if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = None

if uploaded_file is not None:
    data = pd.read_csv(uploaded_file)
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    
    st.success('✅ Данные загружены успешно!')
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Всего записей", len(data))
    with col2:
        st.metric("Городов", data['city'].nunique())
    with col3:
        st.metric("Период данных", 
                 f"{data['timestamp'].min().date()} - {data['timestamp'].max().date()}")
    
    st.subheader('📊 Первые строки данных')
    display_data = data.head(10).copy()
    if 'timestamp' in display_data.columns:
        display_data = display_data.copy()
        display_data['timestamp'] = display_data['timestamp'].dt.strftime('%Y-%m-%d')
    st.dataframe(display_data, width='stretch')
    
    st.subheader('📈 Описательная статистика')
    numeric_cols = data.select_dtypes(include=[np.number]).columns
    desc_data = data[numeric_cols].describe()
    st.dataframe(desc_data, width='stretch')
    
    st.markdown('---')
    st.header('🔍 Анализ данных')
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button('🚀 Запустить анализ данных'):
            with st.spinner('Выполняется анализ данных...'):
                results = analyze_data_sequential(data)
                for city in results:
                    if 'data' in results[city] and 'timestamp' in results[city]['data'].columns:
                        results[city]['data'] = results[city]['data'].copy()
                        results[city]['data']['timestamp'] = results[city]['data']['timestamp'].astype(str)
                st.session_state.analysis_results = results
            st.success('✅ Анализ завершен!')
    
    with col2:
        if st.button('⚡ Сравнить производительность распараллеливания'):
            with st.spinner('Сравнение производительности...'):
                performance = compare_parallelization_performance(data)
                st.session_state.parallel_performance = performance
            
            if 'parallel_performance' in st.session_state:
                perf = st.session_state.parallel_performance
                st.success('✅ Сравнение завершено!')
                
                st.subheader('📊 Результаты сравнения производительности')
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Последовательно", f"{perf['sequential']:.3f} сек")
                with col2:
                    st.metric("Параллельно (процессы)", f"{perf['parallel_process']:.3f} сек")
                with col3:
                    st.metric("Параллельно (потоки)", f"{perf['parallel_thread']:.3f} сек")
                
                if perf['sequential'] > 0:
                    speedup_process = perf['sequential'] / perf['parallel_process']
                    speedup_thread = perf['sequential'] / perf['parallel_thread']
                    
                    fastest_method = min(perf.items(), key=lambda x: x[1])
                    fastest_name = {'sequential': 'Последовательный', 
                                    'parallel_process': 'Параллельный (процессы)',
                                    'parallel_thread': 'Параллельный (потоки)'}[fastest_method[0]]
                    
                    if speedup_process < 1 and speedup_thread < 1:
                        st.warning(f'''
                        **Результаты анализа производительности:**
                        - Последовательный метод оказался быстрее всех ({perf['sequential']:.3f} сек)
                        - Параллельный (процессы): {perf['parallel_process']:.3f} сек (замедление в {1/speedup_process:.2f}x)
                        - Параллельный (потоки): {perf['parallel_thread']:.3f} сек (замедление в {1/speedup_thread:.2f}x)
                        
                        **Выводы:**
                        - Для данного объема данных накладные расходы на создание процессов/потоков
                          перевешивают выгоду от распараллеливания.
                        - Распараллеливание эффективно для больших датасетов или при большом количестве городов.
                        - Для небольших данных последовательный метод предпочтительнее.
                        ''')
                    else:
                        st.success(f'''
                        **Результаты анализа производительности:**
                        - Ускорение при использовании процессов: {speedup_process:.2f}x
                        - Ускорение при использовании потоков: {speedup_thread:.2f}x
                        - Самый быстрый метод: {fastest_name}
                        
                        **Выводы:**
                        - Распараллеливание эффективно для данного объема данных.
                        - Для CPU-интенсивных задач процессы обычно эффективнее потоков,
                          так как обходят GIL (Global Interpreter Lock) в Python.
                        ''')
    
    if st.session_state.analysis_results is not None:
        st.markdown('---')
        st.header('📊 Результаты анализа')
        
        cities = sorted(data['city'].unique())
        selected_city = st.selectbox('🏙️ Выберите город для анализа', cities)
        
        if selected_city:
            city_results = st.session_state.analysis_results[selected_city]
            city_data = city_results['data'].copy()
            if 'timestamp' in city_data.columns:
                city_data['timestamp'] = pd.to_datetime(city_data['timestamp'])
            seasonal_stats = city_results['seasonal_stats']
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Средняя температура", f"{city_data['temperature'].mean():.2f}°C")
            with col2:
                st.metric("Максимальная температура", f"{city_data['temperature'].max():.2f}°C")
            with col3:
                st.metric("Минимальная температура", f"{city_data['temperature'].min():.2f}°C")
            with col4:
                st.metric("Количество аномалий", city_results['anomaly_count'])
            
            st.subheader('📈 Временной ряд температуры')
            fig_timeseries = plot_temperature_timeseries(city_data, selected_city)
            st.pyplot(fig_timeseries)
            
            st.subheader('🌍 Сезонные профили')
            fig_seasonal = plot_seasonal_profiles(seasonal_stats, selected_city)
            st.pyplot(fig_seasonal)
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader('📊 Распределение температуры')
                fig_dist = plot_temperature_distribution(data, selected_city)
                st.pyplot(fig_dist)
            
            with col2:
                st.subheader('⚠️ Временная линия аномалий')
                fig_anomaly = plot_anomaly_timeline(city_data, selected_city)
                st.pyplot(fig_anomaly)
            
            st.markdown('---')
            st.header('🌡️ Мониторинг текущей температуры')
            
            api_key = st.text_input('🔑 Введите API ключ OpenWeatherMap', type='password')
            
            if api_key:
                col1, col2 = st.columns(2)
                with col1:
                    method = st.radio('Выберите метод запроса', ['Синхронный', 'Асинхронный'])
                    
                    if st.button('Получить текущую температуру'):
                        with st.spinner('Запрос к API...'):
                            if method == 'Синхронный':
                                current_temp, error = get_current_temperature_sync(selected_city, api_key)
                            else:
                                current_temp, error = get_current_temperature_async_wrapper(selected_city, api_key)
                            
                            st.session_state.current_temp = current_temp
                            st.session_state.temp_error = error
                
                with col2:
                    if st.button('⚡ Сравнить производительность методов API'):
                        test_cities = cities[:min(5, len(cities))]
                        with st.spinner(f'Сравнение производительности для {len(test_cities)} городов...'):
                            api_performance = compare_sync_async_performance(test_cities, api_key)
                            st.session_state.api_performance = api_performance
                        
                        if 'api_performance' in st.session_state:
                            perf = st.session_state.api_performance
                            st.success('✅ Сравнение завершено!')
                            
                            st.subheader('📊 Результаты сравнения методов API')
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Синхронный метод", f"{perf['sync']:.3f} сек")
                            with col2:
                                st.metric("Асинхронный метод", f"{perf['async']:.3f} сек")
                            
                            if perf['sync'] > 0:
                                speedup = perf['sync'] / perf['async']
                                st.info(f'''
                                **Выводы:**
                                - Ускорение при использовании асинхронного метода: {speedup:.2f}x
                                - Для одиночных запросов разница минимальна, но для множественных запросов
                                  асинхронный метод значительно быстрее, так как позволяет выполнять
                                  запросы параллельно, не блокируя выполнение программы.
                                - Асинхронный метод особенно эффективен при работе с несколькими городами одновременно.
                                ''')
                
                if 'current_temp' in st.session_state:
                    current_temp = st.session_state.current_temp
                    error = st.session_state.temp_error
                    
                    if error:
                        st.error(f'❌ Ошибка: {error}')
                    elif current_temp is not None:
                        st.success(f'✅ Текущая температура в {selected_city}: {current_temp:.2f}°C')
                        
                        current_season = get_current_season()
                        season_names = {
                            'winter': 'Зима',
                            'spring': 'Весна',
                            'summer': 'Лето',
                            'autumn': 'Осень'
                        }
                        st.info(f'📅 Текущий сезон: {season_names[current_season]}')
                        
                        min_temp, max_temp = get_seasonal_normal_range(
                            seasonal_stats, selected_city, current_season
                        )
                        
                        if min_temp is not None and max_temp is not None:
                            is_normal = min_temp <= current_temp <= max_temp
                            
                            if is_normal:
                                st.success(f'✅ Температура в пределах нормы для сезона ({min_temp:.2f}°C - {max_temp:.2f}°C)')
                            else:
                                st.warning(f'⚠️ Температура выходит за пределы нормы для сезона!')
                                st.info(f'Нормальный диапазон: {min_temp:.2f}°C - {max_temp:.2f}°C')
                                st.info(f'Текущая температура: {current_temp:.2f}°C')
                        else:
                            st.warning('⚠️ Не удалось определить нормальный диапазон для данного сезона')
            else:
                st.info('💡 Введите API ключ для получения текущей температуры')
                st.markdown('''
                **Как получить API ключ:**
                1. Зарегистрируйтесь на [OpenWeatherMap](https://openweathermap.org/api)
                2. Получите бесплатный API ключ
                3. Обратите внимание: ключ может активироваться через 2-3 часа
                ''')

else:
    st.info('👆 Пожалуйста, загрузите CSV-файл с температурными данными для начала работы')
    st.markdown('''
    **Формат данных:**
    - `city`: Название города
    - `timestamp`: Дата (формат: YYYY-MM-DD)
    - `temperature`: Среднесуточная температура в °C
    - `season`: Сезон года (winter, spring, summer, autumn)
    ''')
