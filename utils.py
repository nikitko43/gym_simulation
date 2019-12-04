class Time:
    def __init__(self, simulation_time=0):
        self.simulation_time = simulation_time

    @property
    def day(self):
        return self.simulation_time // 1440

    @property
    def hour(self):
        return (self.simulation_time // 60) % 24

    @property
    def minute(self):
        return self.simulation_time % 60

    def __repr__(self):
        return f'{str(self.hour).zfill(2)}:{str(self.minute).zfill(2)}'
