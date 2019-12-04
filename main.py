import simpy
import names
import random
from utils import Time
from logging import log
from random_time_slots import workout_time, choosing_membership_time

class Membership:
    types = ['gym', 'group', 'personal']
    male_probabilities = [0.7, 0.1, 0.2]
    female_probabilities = [0.4, 0.3, 0.3]

    def __init__(self, gender):
        if gender == 'male':
            self.type = random.choices(
                population=self.types,
                weights=self.male_probabilities
            )[0]
        elif gender == 'female':
            self.type = random.choices(
                population=self.types,
                weights=self.female_probabilities
            )[0]


class Source:
    def __init__(self, env, gym):
        self.env = env
        self.gym = gym
        self.clients = [Client(env, gym) for i in range(100)]

    def generate(self):
        for i in range(10):
            self.env.process(random.choice(self.clients).enter())
            yield self.env.timeout(random.randint(3, 10))


class Client:
    def __init__(self, env, gym):
        self.env = env
        self.gym = gym
        self.gender = random.choice(['male', 'female'])
        self.membership = random.choices([Membership(self.gender), None], [0.2, 0.8])[0]
        self.name = names.get_full_name(gender=self.gender)

    def log(self, message):
        log(message, self.env.now)

    def enter(self):
        self.log(f'{self.name} entered')
        if self.membership:
            self.log(f'{self.name} have {self.membership.type} membership')
            yield self.env.process(self.process_client())
        else:
            self.log(f"{self.name} don't have a membership yet!")
            yield self.env.process(self.get_membership())

        self.log(f'{self.name} leaved')

    def process_client(self):
        with self.gym.request() as req:
            yield req

            self.log(f'{self.name} working...')
            yield self.env.timeout(workout_time())
        
    def get_membership(self):
        self.log(f'{self.name} choosing...')
        yield self.env.timeout(choosing_membership_time())
        self.membership = Membership(self.gender)
        self.log(f'{self.name} buyed a {self.membership.type} membership')
        yield self.env.process(self.process_client())

    def __repr__(self):
        return self.name

env = simpy.Environment()
gym = simpy.Resource(env, capacity=50)
group_room = simpy.Resource(env, capacity=15)

source = Source(env, gym)
env.process(source.generate())

env.run(until=1440)