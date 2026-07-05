#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dronekit import connect, VehicleMode, LocationGlobalRelative
import time
import csv
from datetime import datetime

def get_location_metres(original_location, dNorth, dEast):
    """
    Возвращает новую точку, смещённую на dNorth (метры на север) 
    и dEast (метры на восток) от original_location.
    """
    earth_radius = 6378137.0  # Радиус Земли в метрах
    dLat = dNorth / earth_radius
    dLon = dEast / earth_radius  # Приближение для малых расстояний
    new_lat = original_location.lat + (dLat * 180 / 3.14159)
    new_lon = original_location.lon + (dLon * 180 / 3.14159)
    return LocationGlobalRelative(new_lat, new_lon, original_location.alt)

# Подключение к симулятору
print("Подключение к симулятору...")
vehicle = connect('127.0.0.1:14550', wait_ready=True)

def arm_and_takeoff(target_altitude):
    """Функция взлёта на заданную высоту"""
    print("Переключение в режим GUIDED...")
    vehicle.mode = VehicleMode("GUIDED")
    
    print("Постановка на ARM...")
    vehicle.armed = True
    while not vehicle.armed:
        print("Ожидание ARM...")
        time.sleep(1)
    
    print(f"Взлёт на {target_altitude} метров...")
    vehicle.simple_takeoff(target_altitude)
    
    # Ожидание достижения высоты
    while True:
        alt = vehicle.location.global_relative_frame.alt
        print(f"Высота: {alt:.2f} м")
        if alt >= target_altitude * 0.95:
            print("Целевая высота достигнута!")
            break
        time.sleep(1)

# --- Основная программа ---
# 1. Взлёт
arm_and_takeoff(5)

# 2. Квадратный маршрут (сторона 100 метров)
print("\n--- Начало движения по квадрату ---")

# Получаем стартовую позицию (после взлёта)
start_location = vehicle.location.global_relative_frame

# Точки в метрах (север, восток)
points_metres = [
    (100, 0),   # 100 м на север
    (100, 100),  # 100 м на север и 100 м на восток
    (0, 100),   # 0 м на север, 100 м на восток
    (0, 0)     # Возврат в центр
]

points = [get_location_metres(start_location, dN, dE) for dN, dE in points_metres]

with open('track.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['time', 'lat', 'lon', 'alt', 'mode'])

    for i, point in enumerate(points):
        print(f"Точка {i+1}: летим в ({point.lat}, {point.lon})")
        vehicle.simple_goto(point)
        for j in range(15): # Даём время на движение (увеличьте, если дрон не успевает)
            writer.writerow([
                datetime.now().strftime("%H:%M:%S"),
                vehicle.location.global_frame.lat,
                vehicle.location.global_frame.lon,
                vehicle.location.global_relative_frame.alt,
                vehicle.mode.name
            ])
            time.sleep(1)

# 3. Посадка
print("\n--- Посадка ---")
vehicle.mode = VehicleMode("LAND")

# Ожидание посадки
while vehicle.armed:
    alt = vehicle.location.global_relative_frame.alt
    print(f"Высота: {alt:.2f} м")
    time.sleep(1)

print("Дрон сел!")
vehicle.close()
print("Сеанс завершён.")
