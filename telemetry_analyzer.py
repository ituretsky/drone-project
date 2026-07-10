#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import matplotlib.pyplot as plt
import os

def load_telemetry(csv_file):
    """
    Загружает данные из CSV-файла.
    Ожидает колонки: time, lat, lon, alt, mode (и, опционально, speed).
    """
    data = {
        "time": [],
        "lat": [],
        "lon": [],
        "alt": [],
        "mode": []
    }
    
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data["time"].append(row.get("time", ""))
                data["lat"].append(float(row.get("lat", 0)))
                data["lon"].append(float(row.get("lon", 0)))
                data["alt"].append(float(row.get("alt", 0)))
                data["mode"].append(row.get("mode", ""))
        print(f"Загружено {len(data['time'])} записей из {csv_file}")
        return data
    except FileNotFoundError:
        print(f"ОШИБКА: Файл {csv_file} не найден!")
        return None
    except Exception as e:
        print(f"ОШИБКА при чтении {csv_file}: {e}")
        return None

def plot_trajectory(data, output_file="trajectory.png"):
    """Строит траекторию полёта (широта vs долгота)."""
    if not data:
        return
    
    plt.figure(figsize=(10, 8))
    plt.plot(data["lon"], data["lat"], marker='o', linestyle='-', linewidth=2, markersize=4)
    plt.title("Траектория полёта")
    plt.xlabel("Долгота")
    plt.ylabel("Широта")
    plt.grid(True)
    plt.axis('equal')
    plt.savefig(output_file, dpi=150)
    print(f"Траектория сохранена в {output_file}")
    plt.show()

def plot_altitude(data, output_file="altitude.png"):
    """Строит график высоты от времени."""
    if not data:
        return
    
    plt.figure(figsize=(12, 6))
    plt.plot(data["time"], data["alt"], marker='o', linestyle='-', linewidth=2, markersize=4)
    plt.title("Высота полёта")
    plt.xlabel("Время (сек)")
    plt.ylabel("Высота (м)")
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_file, dpi=150)
    print(f"График высоты сохранён в {output_file}")
    plt.show()

def plot_modes(data, output_file="modes.png"):
    """Строит график режимов полёта (если есть данные)."""
    if not data or not data["mode"]:
        print("Нет данных о режимах для визуализации.")
        return
    
    # Преобразуем режимы в числовые значения для графика
    unique_modes = list(set(data["mode"]))
    mode_to_num = {mode: i for i, mode in enumerate(unique_modes)}
    mode_nums = [mode_to_num[m] for m in data["mode"]]
    
    plt.figure(figsize=(12, 4))
    plt.plot(data["time"], mode_nums, marker='o', linestyle='-', linewidth=2, markersize=4)
    plt.title("Режимы полёта")
    plt.xlabel("Время (сек)")
    plt.ylabel("Режим")
    plt.yticks(list(mode_to_num.values()), list(mode_to_num.keys()))
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_file, dpi=150)
    print(f"График режимов сохранён в {output_file}")
    plt.show()

def main():
    # Путь к лог-файлу (можно передать аргументом командной строки)
    log_file = "track.csv"
    
    # Проверяем, есть ли файл
    if not os.path.exists(log_file):
        print(f"Файл {log_file} не найден. Укажите путь к логу.")
        return
    
    # Загружаем данные
    data = load_telemetry(log_file)
    if not data:
        return
    
    # Строим графики
    plot_trajectory(data)
    plot_altitude(data)
    plot_modes(data)
    
    print("Анализ завершён. Все графики сохранены.")

if __name__ == "__main__":
    main()