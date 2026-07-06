#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import csv
import time
from datetime import datetime
from dronekit import connect, VehicleMode, LocationGlobalRelative

# ====================================================
# 1. Загрузка конфигурации из JSON
# ====================================================
def load_config(config_file="config.json"):
    """Загружает параметры из JSON-файла."""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        print("Конфигурация загружена:")
        for key, value in config.items():
            print(f"  {key}: {value}")
        return config
    except FileNotFoundError:
        print(f"ОШИБКА: Файл {config_file} не найден!")
        raise
    except json.JSONDecodeError as e:
        print(f"ОШИБКА: Некорректный JSON в {config_file}: {e}")
        raise

# ====================================================
# 2. Подключение к симулятору
# ====================================================
def connect_sitl(connection_string='127.0.0.1:14550'):
    """Подключается к SITL и возвращает объект Vehicle."""
    try:
        print("Подключение к симулятору...")
        vehicle = connect(connection_string, wait_ready=True)
        print("Подключено!")
        return vehicle
    except Exception as e:
        print(f"ОШИБКА подключения: {e}")
        raise

# ====================================================
# 3. Взлёт
# ====================================================
def arm_and_takeoff(vehicle, target_altitude):
    """Взлёт на заданную высоту."""
    print("Переключение в режим GUIDED...")
    vehicle.mode = VehicleMode("GUIDED")

    print("Постановка на ARM...")
    vehicle.armed = True
    while not vehicle.armed:
        print("Ожидание ARM...")
        time.sleep(1)

    print(f"Взлёт на {target_altitude} м...")
    vehicle.simple_takeoff(target_altitude)

    while True:
        alt = vehicle.location.global_relative_frame.alt
        print(f"Высота: {alt:.2f} м")
        if alt >= target_altitude * 0.95:
            print("Целевая высота достигнута!")
            break
        time.sleep(1)

# ====================================================
# 4. Пересчёт метров в градусы
# ====================================================
def get_location_metres(original_location, dNorth, dEast):
    """Возвращает новую точку, смещённую на dNorth/dEast метров."""
    earth_radius = 6378137.0
    dLat = dNorth / earth_radius
    dLon = dEast / earth_radius
    new_lat = original_location.lat + (dLat * 180 / 3.14159)
    new_lon = original_location.lon + (dLon * 180 / 3.14159)
    return LocationGlobalRelative(new_lat, new_lon, original_location.alt)

# ====================================================
# 5. Основная программа
# ====================================================
def main():
    try:
        # 5.1 Загружаем конфиг
        config = load_config()
        takeoff_alt = config.get("takeoff_alt", 5)
        square_side = config.get("square_side", 100)
        leg_time = config.get("leg_time", 15)
        log_file = config.get("log_file", "track.csv")

        # 5.2 Подключаемся к симулятору
        vehicle = connect_sitl()

        # 5.3 Взлёт
        arm_and_takeoff(vehicle, takeoff_alt)

        # 5.4 Полёт по квадрату
        print(f"\n--- Начало движения по квадрату (сторона {square_side} м) ---")
        start_location = vehicle.location.global_relative_frame

        points_metres = [
            (square_side, 0),
            (square_side, square_side),
            (0, square_side),
            (0, 0)
        ]
        points = [get_location_metres(start_location, dN, dE) for dN, dE in points_metres]

        # 5.5 Логирование
        with open(log_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['time', 'lat', 'lon', 'alt', 'mode'])

            for i, point in enumerate(points):
                print(f"Точка {i+1}: летим в ({point.lat:.7f}, {point.lon:.7f})")
                vehicle.simple_goto(point)
                time.sleep(leg_time)

                # Запись в лог (одна точка после каждой ноги)
                writer.writerow([
                    datetime.now().strftime("%H:%M:%S"),
                    vehicle.location.global_frame.lat,
                    vehicle.location.global_frame.lon,
                    vehicle.location.global_relative_frame.alt,
                    vehicle.mode.name
                ])

        # 5.6 Посадка
        print("\n--- Посадка ---")
        vehicle.mode = VehicleMode("LAND")

        while vehicle.armed:
            alt = vehicle.location.global_relative_frame.alt
            print(f"Высота: {alt:.2f} м")
            time.sleep(1)

        print("Дрон сел!")
        print(f"Лог сохранён в {log_file}")

    except Exception as e:
        print(f"КРИТИЧЕСКАЯ ОШИБКА: {e}")
    finally:
        if 'vehicle' in locals() and vehicle:
            vehicle.close()
            print("Соединение закрыто.")

# ====================================================
# 6. Запуск
# ====================================================
if __name__ == "__main__":
    main()
