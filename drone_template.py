# drone_template.py
class SimpleDrone:
    def __init__(self, name, battery=10):
        self.name = name
        self.battery = battery
        self.altitude = 0

    def takeoff(self, target_height):
        if target_height <= 0:
            raise ValueError("Высота должна быть > 0")
        self.altitude = target_height
        print(f"{self.name} взлетел на {self.altitude} м")

    def land(self):
        self.altitude = 0
        print(f"{self.name} сел")

    def status(self):
        print(f"{self.name}: батарея {self.battery}%, высота {self.altitude} м")

    def charge(self, percent):
        self.battery = min(100, self.battery + percent)
        print(f"Батарея теперь {self.battery}%")

# --- проверка ---
if __name__ == "__main__":
    my_drone = SimpleDrone("TestDrone")
    my_drone.status()
    my_drone.takeoff(765)
    my_drone.land()
    my_drone.charge(30)
    my_drone.status()
