import json  # импортируем модуль для сериализации результатов симуляции в формат JSON
from datetime import datetime  # импортируем класс datetime для формирования уникальной временной метки

import matplotlib.pyplot as plt  # импортируем модуль pyplot библиотеки matplotlib для построения графиков

from core.config import (  # импортируем пути и имена файлов, используемые при сохранении результатов визуализации
    SIM_RESULTS_DIR,
    SIMULATION_BAR_CHART_NAME,
    SIMULATION_PIE_CHART_NAME,
)


def save_results(results):  # функция сохранения результатов симуляции в JSON-файл
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # формируем временную метку для уникального имени файла
    result_path = SIM_RESULTS_DIR / f"simulation_results_{timestamp}.json"  # создаём путь к файлу результатов в каталоге симуляции

    with result_path.open("w", encoding="utf-8") as file:  # открываем JSON-файл для записи в кодировке UTF-8
        json.dump(results, file, ensure_ascii=False, indent=4)  # сохраняем структуру результатов в формате JSON с отступами

    return result_path  # возвращаем путь к сохранённому файлу результатов


def create_bar_chart(results):  # функция построения столбчатой диаграммы по результатам симуляции
    accepted_count = sum(1 for item in results if item["status"] == "ACCEPTED")  # подсчитываем количество успешно принятых файлов
    rejected_count = sum(1 for item in results if item["status"] == "REJECTED")  # подсчитываем количество отклонённых файлов

    labels = ["ACCEPTED", "REJECTED"]  # задаём подписи категорий для диаграммы
    values = [accepted_count, rejected_count]  # формируем числовые значения для отображения на диаграмме
    colors = ["#2e8b57", "#c0392b"]  # задаём цвета столбцов для положительного и отрицательного статусов

    chart_path = SIM_RESULTS_DIR / SIMULATION_BAR_CHART_NAME  # формируем путь для сохранения столбчатой диаграммы

    fig, ax = plt.subplots(figsize=(8, 5), facecolor="white")  # создаём фигуру и область построения заданного размера
    bars = ax.bar(labels, values, color=colors)  # строим столбчатую диаграмму по меткам и значениям

    ax.set_title("Статусы результатов симуляции")  # задаём заголовок графика
    ax.set_ylabel("Количество файлов")  # задаём подпись вертикальной оси
    ax.grid(axis="y", linestyle="--", alpha=0.4)  # включаем вспомогательную сетку по оси Y

    for bar in bars:  # поочерёдно обрабатываем каждый построенный столбец
        height = bar.get_height()  # получаем высоту текущего столбца
        ax.text(  # размещаем текстовую подпись над столбцом
            bar.get_x() + bar.get_width() / 2,  # вычисляем горизонтальную координату центра столбца
            height + 0.05,  # задаём вертикальную координату немного выше вершины столбца
            str(height),  # преобразуем числовое значение в текст для отображения
            ha="center",  # выравниваем подпись по центру относительно столбца
            va="bottom"  # привязываем текст по нижней границе к указанной точке
        )

    fig.tight_layout()  # автоматически корректируем отступы элементов внутри фигуры
    fig.savefig(chart_path, dpi=150, facecolor="white", bbox_inches="tight")  # сохраняем диаграмму в файл с заданным разрешением
    plt.close(fig)  # закрываем фигуру для освобождения памяти

    return chart_path  # возвращаем путь к сохранённой столбчатой диаграмме


def create_pie_chart(results):  # функция построения круговой диаграммы по результатам симуляции
    accepted_count = sum(1 for item in results if item["status"] == "ACCEPTED")  # подсчитываем количество успешно принятых файлов
    rejected_count = sum(1 for item in results if item["status"] == "REJECTED")  # подсчитываем количество отклонённых файлов

    labels = ["ACCEPTED", "REJECTED"]  # задаём подписи сегментов круговой диаграммы
    values = [accepted_count, rejected_count]  # формируем числовые значения для сегментов диаграммы
    colors = ["#2e8b57", "#c0392b"]  # задаём цвета сегментов диаграммы

    chart_path = SIM_RESULTS_DIR / SIMULATION_PIE_CHART_NAME  # формируем путь для сохранения круговой диаграммы

    fig, ax = plt.subplots(figsize=(6, 6), facecolor="white")  # создаём квадратную фигуру и область построения
    ax.pie(  # строим круговую диаграмму по значениям и подписям
        values,
        labels=labels,
        autopct="%1.1f%%",  # отображаем долю каждого сегмента в процентах с одной цифрой после запятой
        startangle=90,  # поворачиваем начало отсчёта сегментов для более удобного отображения
        colors=colors
    )
    ax.set_title("Распределение результатов симуляции")  # задаём заголовок круговой диаграммы

    fig.tight_layout()  # корректируем внутренние отступы фигуры перед сохранением
    fig.savefig(chart_path, dpi=150, facecolor="white", bbox_inches="tight")  # сохраняем круговую диаграмму в файл
    plt.close(fig)  # закрываем фигуру для освобождения памяти

    return chart_path  # возвращаем путь к сохранённой круговой диаграмме