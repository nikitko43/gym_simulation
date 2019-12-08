import simpy
import random
import os
import csv
from math import floor
from collections import defaultdict
from statistics import mean
from contextlib import contextmanager
from mimesis import Person
from mimesis.enums import Gender
from utils import Time
from experiment import Experiment

report_only = input('Показать только отчет (да/нет)? ').lower().startswith('д')

# setup environment and other stuff

env = simpy.Environment()
exp = Experiment()

gym = simpy.Resource(env, capacity=exp.get_gym_capacity())
manager = simpy.Resource(env, capacity=exp.get_manager_capacity())
trainers = simpy.Resource(env, capacity=exp.get_trainers())
group_room = simpy.Resource(env, capacity=exp.get_group_room_capacity())

person = Person('ru')



# statistics

class Stats:
    def __init__(self):
        self.times = defaultdict(list)
        self.values = defaultdict(int)

    def inc(self, name):
        self.values[name] += 1

    def waiting_time(self, time, name):
        self.times[name].append(time)

    def wait_for(self, name):
        return len(list(filter(lambda x: x > 0, self.times[name])))

    def mean_wait_for(self, name, value_only=False):
        filtered = list(filter(lambda x: x > 0, self.times[name]))
        if len(filtered) == 0:
            if value_only:
                return 0
            return '0 секунд'
        mean_value = mean(filtered)

        if value_only:
            return floor(mean_value)

        if mean_value < 60:
            return f'{mean_value:.0f} секунд'
        return f'{mean_value // 60:.0f} минут и {mean_value % 60:.0f} секунд'

    def report(self):
        print(f'')
        print(f'Сегодня пришло {self.values["in"]} человек, из них:')
        print(f'  Мужчин: {self.values["in_male"]}, женщин: {self.values["in_female"]}')
        print(f'  Имели купленный абонемент: {self.values["in_have"]}')
        print(f'  Не имели купленного абонемента: {self.values["in_have_not"]}')
        print(f'    Из них')
        print(f'      купили обычный абонемент: {self.values["обычный"]}')
        print(f'      купили групповой абонемент: {self.values["групповой"]}')
        print(f'      купили персональный абонемент: {self.values["персональный"]}')
        print(f'  Занимались')
        print(f'    в тренажерном зале: {self.values["working_gym"]}')
        print(f'    в зале для групповых тренировок: {self.values["working_group"]}')
        print(f'    в тренажерном зале c персональным тренером: {self.values["working_trainer"]}')
        print(f'')
        print(f'Клиенты ждали пока освободится')
        print(f'  администратор: {self.wait_for("manager")} раз, в среднем {self.mean_wait_for("manager")}')
        print(f'  тренажерный зал: {self.wait_for("gym")} раз, в среднем {self.mean_wait_for("gym")}')
        print(f'  зал для групповых тренировок: {self.wait_for("group_room")} раз, в среднем {self.mean_wait_for("group_room")}')
        print(f'  хотя бы один из персональных тренеров: {self.wait_for("trainer")} раз, в среднем {self.mean_wait_for("trainer")}')
        print(f'')

        
        if not os.path.isfile('log.csv'):
            with open('log.csv', 'w', newline='') as file:
                csvwriter = csv.writer(file, delimiter=',')
                csvwriter.writerow(list(stats.values.keys()) + ['wait_gym', 'wait_manager', 'wait_group_room', 'wait_trainer'])
                csvwriter.writerow(list(stats.values.values()) + [self.mean_wait_for("gym", value_only=True), self.mean_wait_for("manager", value_only=True), 
                                                                  self.mean_wait_for("group_room", value_only=True), self.mean_wait_for("trainer", value_only=True)])
        else:
            with open('log.csv', 'a', newline='') as file:
                csvwriter = csv.writer(file, delimiter=',')
                csvwriter.writerow(list(stats.values.values()) + [self.mean_wait_for("gym", value_only=True), self.mean_wait_for("manager", value_only=True), 
                                                                  self.mean_wait_for("group_room", value_only=True), self.mean_wait_for("trainer", value_only=True)])



stats = Stats()   # initialize statistic engine


@contextmanager
def waiting(name):
    time = env.now
    yield
    stats.waiting_time(env.now - time, name)



# random time slots

def experiment_time(name):
    distribution, parameters = exp.get_time_parameters(name)
    return getattr(random, distribution)(*parameters)



# utils that using environment (for shortness and readability)

def log(message):
    if not report_only:
        print(f'[{str(Time(env.now))}] {message}')



# gym things

class Membership:
    types = ['обычный', 'групповой', 'персональный']
    male_probabilities = exp.get_male_probabilities()
    female_probabilities = exp.get_female_probabilities()

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


class DaySource:
    def __init__(self):
        self.clients = [Client() for i in range(exp.clients_total())]

    def start(self):
        yield env.timeout(36000) # wait for working day to start
        yield env.process(self.generate())

    def generate(self):
        for i in range(46800):
            hour_proba = exp.get_hour_enter_probability(Time(env.now).hour)
            probability =  hour_proba / 3600 * exp.clients_total() * exp.get_client_enter_probability()

            if random.uniform(0, 1) < probability:
                env.process(random.choice(self.clients).enter())
            yield env.timeout(1)


class Client:
    def __init__(self):
        self.gender = random.choice(['male', 'female'])
        probabilities = exp.clients_have_membership()
        self.membership = random.choices([Membership(self.gender), None], probabilities)[0]
        self.name = person.full_name(gender=Gender.MALE if self.gender == 'male' else Gender.FEMALE)

    def enter(self):
        log(f'{self.name} зашел')

        stats.inc('in')
        if self.gender == 'male':
            stats.inc('in_male')
        else:
            stats.inc('in_female')

        if self.membership:
            log(f'У {self.name} есть {self.membership.type} абонемент')
            stats.inc('in_have')
            yield env.process(self.process_client())
        else:
            log(f"У {self.name} еще нет абонемента!")
            stats.inc('in_have_not')
            yield env.process(self.get_membership())

        log(f'{self.name} ушел')

    def process_client(self):
        if self.membership.type == 'обычный':
            with gym.request() as req:
                with waiting('gym'):
                    yield req

                log(f'{self.name} занимается в тренажерном зале...')
                stats.inc('working_gym')
                yield env.timeout(experiment_time('workout'))

        if self.membership.type == 'групповой':
            with group_room.request() as req:
                with waiting('group_room'):
                    yield req

                log(f'{self.name} занимается в зале для групповых тренировок...')
                stats.inc('working_group')
                yield env.timeout(experiment_time('workout'))

        if self.membership.type == 'персональный':
            with gym.request() as req:
                with waiting('gym'):
                    yield req

                with trainers.request() as req_trainer:
                    with waiting('trainer'):
                        yield req_trainer

                    log(f'{self.name} занимается в зале c персональным тренером...')
                    stats.inc('working_trainer')
                    yield env.timeout(experiment_time('workout'))
        
    def get_membership(self):
        log(f'{self.name} выбирает что приобрести...')
        with manager.request() as req:
            with waiting('manager'):
                yield req

            yield env.timeout(experiment_time('choosing_membership'))
            self.membership = Membership(self.gender)

        log(f'{self.name} купил {self.membership.type} абонемент')
        stats.inc(self.membership.type)
        yield env.process(self.process_client())

    def __repr__(self):
        return self.name



source = DaySource()

env.process(source.start())
env.run(until=82800)

stats.report()
