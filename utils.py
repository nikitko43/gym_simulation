class Time:
    def __init__(self, simulation_time=0):
        self.simulation_time = simulation_time

    @property
    def day(self):
        return self.simulation_time // 86400

    @property
    def hour(self):
        return (self.simulation_time // 3600) % 24

    @property
    def minute(self):
        return (self.simulation_time // 60) % 60

    @property
    def second(self):
        return self.simulation_time % 60
    

    def __repr__(self):
        return '{:02.0f}:{:02.0f}:{:02.0f}'.format(self.hour, self.minute, self.second)
