#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from dronekit import connect, VehicleMode
import time

# Подключение к SITL (порт 14550 по умолчанию)
print("Подключение к симулятору...")
vehicle = connect('127.0.0.1:14550', wait_ready=True)

# Вывод информации о дроне
print(f"Режим: {vehicle.mode.name}")
print(f"Высота: {vehicle.location.global_relative_frame.alt} м")
print(f"Широта: {vehicle.location.global_frame.lat}")
print(f"Долгота: {vehicle.location.global_frame.lon}")

# Взлёт на 5 метров
print("Взлёт на 5 метров...")
vehicle.mode = VehicleMode("GUIDED")
vehicle.armed = True
vehicle.simple_takeoff(5)

# Ожидание достижения высоты
while vehicle.location.global_relative_frame.alt < 4.5:
    print(f"Высота: {vehicle.location.global_relative_frame.alt:.2f} м")
    time.sleep(1)

print("Достигнута целевая высота!")

# Посадка
print("Посадка...")
vehicle.mode = VehicleMode("LAND")

# Ожидание посадки
while vehicle.armed:
    print(f"Высота: {vehicle.location.global_relative_frame.alt:.2f} м")
    time.sleep(1)

print("Дрон сел!")

# Закрытие соединения
vehicle.close()
print("Сеанс завершён.")