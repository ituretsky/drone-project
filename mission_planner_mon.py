#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import time
import threading
from datetime import datetime
from dronekit import LocationGlobalRelative, VehicleMode

class TelemetryMonitor:
    """
    Фоновый мониторинг телеметрии.
    Запускается в отдельном потоке и не блокирует основное управление.
    """
    def __init__(self, vehicle, interval=1):
        self.vehicle = vehicle
        self.interval = interval
        self._running = False
        self._thread = None

    def _monitor(self):
        """Фоновый метод, читающий телеметрию."""
        while self._running:
            try:
                alt = self.vehicle.location.global_relative_frame.alt
                lat = self.vehicle.location.global_frame.lat
                lon = self.vehicle.location.global_frame.lon
                mode = self.vehicle.mode.name
                armed = self.vehicle.armed

                print(f"[ТЕЛЕМЕТРИЯ] Высота: {alt:.2f} м | Широта: {lat:.6f} | Долгота: {lon:.6f} | Режим: {mode} | Armed: {armed}")

            except Exception as e:
                print(f"Ошибка при чтении телеметрии: {e}")

            time.sleep(self.interval)

    def start(self):
        """Запускает фоновый мониторинг."""
        if self._running:
            print("Мониторинг уже запущен.")
            return

        self._running = True
        self._thread = threading.Thread(target=self._monitor, daemon=True)
        self._thread.start()
        print("Мониторинг телеметрии запущен.")

    def stop(self):
        """Останавливает фоновый мониторинг."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        print("Мониторинг телеметрии остановлен.")

class MissionPlanner:
    """
    Класс для планирования и выполнения миссий дрона.
    Поддерживает квадратные и прямоугольные маршруты.
    """
    
    def __init__(self, vehicle, config):
        """
        Инициализация планировщика миссий.
        
        Аргументы:
            vehicle -- подключённый объект Vehicle из DroneKit
            config  -- словарь с параметрами миссии (takeoff_alt, square_side, leg_time, log_file)
        """
        self.vehicle = vehicle
        self.config = config
        self.monitor = None
        self.takeoff_alt = config.get("takeoff_alt", 5)
        self.square_side = config.get("square_side", 100)
        self.leg_time = config.get("leg_time", 15)
        self.log_file = config.get("log_file", "track.csv")
        self.mission_type = config.get("mission_type", "square")
        self.waypoints = []
        self.log_data = []
        
    def _get_location_metres(self, original_location, dNorth, dEast):
        """
        Возвращает новую точку, смещённую на dNorth/dEast метров.
        (Вспомогательный метод, внутренний)
        """
        earth_radius = 6378137.0
        dLat = dNorth / earth_radius
        dLon = dEast / earth_radius
        new_lat = original_location.lat + (dLat * 180 / 3.14159)
        new_lon = original_location.lon + (dLon * 180 / 3.14159)
        new_alt = self.takeoff_alt
        return LocationGlobalRelative(new_lat, new_lon, new_alt)
    
    def _arm_and_takeoff(self):
        """
        Взлёт на заданную высоту.
        (Вспомогательный метод, внутренний)
        """
        vehicle = self.vehicle
        target = self.takeoff_alt
        
        print("Переключение в режим GUIDED...")
        vehicle.mode = VehicleMode("GUIDED")
        
        print("Постановка на ARM...")
        vehicle.armed = True
        while not vehicle.armed:
            print("Ожидание ARM...")
            time.sleep(1)
        
        print(f"Взлёт на {target} м...")
        vehicle.simple_takeoff(target)
        
        while True:
            alt = vehicle.location.global_relative_frame.alt
            print(f"Высота: {alt:.2f} м")
            if alt >= target * 0.95:
                print("Целевая высота достигнута!")
                break
            time.sleep(1)
    
    def plan_square(self):
        """
        Планирует маршрут по квадрату со стороной square_side.
        Сохраняет точки в self.waypoints.
        """
        start = self.vehicle.location.global_relative_frame
        side = self.square_side
        
        # Четыре точки квадрата в метрах (север, восток)
        points_metres = [
            (side, 0),
            (side, side),
            (0, side),
            (0, 0)
        ]
        
        self.waypoints = [
            self._get_location_metres(start, dN, dE) 
            for dN, dE in points_metres
        ]
        
        print(f"Спланирован квадратный маршрут со стороной {side} м")
        return self.waypoints
    
    def plan_rectangle(self, width, height):
        """
        Планирует маршрут по прямоугольнику.
        width  -- ширина (метры)
        height -- высота (метры)
        """
        start = self.vehicle.location.global_relative_frame
        
        points_metres = [
            (height, 0),
            (height, width),
            (0, width),
            (0, 0)
        ]
        
        self.waypoints = [
            self._get_location_metres(start, dN, dE) 
            for dN, dE in points_metres
        ]
        
        print(f"Спланирован прямоугольный маршрут {width}x{height} м")
        return self.waypoints
    
    def plan_custom(self, points_metres):
        """
        Планирует маршрут по пользовательскому списку точек.
        points_metres -- список кортежей (dNorth, dEast) в метрах.
        """
        start = self.vehicle.location.global_relative_frame
        
        self.waypoints = [
            self._get_location_metres(start, dN, dE) 
            for dN, dE in points_metres
        ]
        
        print(f"Спланирован пользовательский маршрут из {len(self.waypoints)} точек")
        return self.waypoints
    
    def fly_mission(self):
        """
        Выполняет миссию:
        - Взлёт
        - Облёт всех точек маршрута
        - Посадка
        - Логирование в CSV
        """
        try:
            # 1. Взлёт
            self._arm_and_takeoff()
            
            # --- Запуск мониторинга ---
            self.monitor = TelemetryMonitor(self.vehicle, interval=1)
            self.monitor.start()
            # --------------------------
            
            # 2. Если маршрут не задан, строим квадрат по умолчанию
            if not self.waypoints:
                print("Маршрут не задан. Строим квадрат по умолчанию.")
                self.plan_square()
            
            # 3. Полёт по точкам
            print(f"\n--- Выполнение миссии ({self.mission_type}) ---")
            
            with open(self.log_file, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['time', 'lat', 'lon', 'alt', 'mode', 'wp_index'])
                
                for i, point in enumerate(self.waypoints):
                    print(f"Точка {i+1}: летим в ({point.lat:.7f}, {point.lon:.7f})")
                    self.vehicle.simple_goto(point)
                    time.sleep(self.leg_time)
                    
                    writer.writerow([
                        datetime.now().strftime("%H:%M:%S"),
                        self.vehicle.location.global_frame.lat,
                        self.vehicle.location.global_frame.lon,
                        self.vehicle.location.global_relative_frame.alt,
                        self.vehicle.mode.name,
                        i + 1
                    ])
            
            # 4. Посадка
            print("\n--- Посадка ---")
            self.vehicle.mode = VehicleMode("LAND")
            
            while self.vehicle.armed:
                alt = self.vehicle.location.global_relative_frame.alt
                print(f"Высота: {alt:.2f} м")
                time.sleep(1)
            
            print("Дрон сел!")
            print(f"Лог сохранён в {self.log_file}")
            
        except Exception as e:
            print(f"ОШИБКА ВО ВРЕМЯ ПОЛЁТА: {e}")
        finally:
            # --- Остановка мониторинга ---
            if self.monitor:
                self.monitor.stop()
            # -----------------------------
            if self.vehicle:
                self.vehicle.close()
                print("Соединение закрыто.")
    
    def show_waypoints(self):
        """Выводит список запланированных точек."""
        if not self.waypoints:
            print("Маршрут ещё не спланирован.")
            return
        
        print("\n--- Запланированные точки ---")
        for i, wp in enumerate(self.waypoints):
            print(f"  {i+1}: широта {wp.lat:.7f}, долгота {wp.lon:.7f}, высота {wp.alt} м")


# ====================================================
# Пример использования
# ====================================================
if __name__ == "__main__":
    from dronekit import connect
    
    # Подключение к симулятору
    print("Подключение к симулятору...")
    vehicle = connect('127.0.0.1:14550', wait_ready=True)
    print("Подключено!")
    
    # Конфигурация
    config = {
        "takeoff_alt": 5,
        "square_side": 100,
        "leg_time": 15,
        "log_file": "mission_log.csv",
        "mission_type": "square"
    }
    
    # Создаём планировщик
    planner = MissionPlanner(vehicle, config)
    
    # Планируем квадрат
    planner.plan_square()
    
    # Выводим точки
    planner.show_waypoints()
    
    # Выполняем миссию
    planner.fly_mission()
