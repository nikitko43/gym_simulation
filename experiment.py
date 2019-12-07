from yaml import load, Loader


class Experiment:
    def __init__(self):
        file = input('Введите название YAML файла эксперимента: ')
        if not file:
            file = 'experiments/exp1.yml'
        self.exp = load(open(file, 'r'), Loader=Loader)['experiment']

    def join(self, join_target):
        return {key: value for d in join_target for key, value in d.items()} 

    def get_time_parameters(self, name):
        slot = self.join(self.exp['time_slots'][name])
        distribution = slot['distribution']
        parameters = slot['parameters']

        parameters = [int(value[:-1]) * 60 if str(value)[-1] == 'm' else int(value[:-1]) for value in parameters]
        return distribution, parameters

    def clients_total(self):
        return self.join(self.exp['clients'])['total']

    def clients_have_membership(self):
        proba = self.join(self.exp['clients'])['having_membership']
        return proba, abs(proba - 1)

    def get_male_probabilities(self):
        mb = self.join(self.exp['memberships'])
        mp = 'male_probability'
        return self.join(mb['обычный'])[mp], self.join(mb['обычный'])[mp], self.join(mb['обычный'])[mp]

    def get_female_probabilities(self):
        mb = self.join(self.exp['memberships'])
        fp = 'female_probability'
        return self.join(mb['обычный'])[fp], self.join(mb['обычный'])[fp], self.join(mb['обычный'])[fp]

    def get_trainers(self):
        return self.exp['trainers']

    def get_gym_capacity(self):
        return self.exp['gym_capacity']

    def get_manager_capacity(self):
        return self.exp['manager_capacity']

    def get_group_room_capacity(self):
        return self.exp['group_room_capacity']

    def get_hour_enter_probability(self, hour):
        visitations = self.join(self.exp['visitations'])
        return visitations[hour] / sum(visitations.values())

    def get_client_enter_probability(self):
        return self.exp['client_enter_probability']
