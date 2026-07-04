class Drone:
    def __init__(self, model, max_speed, gps_lat, gps_lon):
        self.model = model
        self.max_speed = max_speed
        self.gps_lat = gps_lat
        self.gps_lon = gps_lon

    def fly_to(self, lat, lon):
        self.gps_lat = lat
        self.gps_lon = lon
        print("I'm flying to", lat, lon)

    def hover(self):
        print('Just hovering')

D1 = Drone('Rhinocero', 100, 0, 0)

y = int(input('Enter latitude: '))
x = int(input('Enter longitude: '))

D1.fly_to(y, x)

D1.hover()