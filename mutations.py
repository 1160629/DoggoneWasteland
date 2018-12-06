
class Mutation:
    def __init__(self):
        self.mutation_to = None

class Mutations:
    def __init__(self):
        self.mutations = []

    def mutate(self, mutation):
        self.mutations.append(mutation)
        #print(self.mutations)

    def get(self):
        return []

    def get_dodge_chance(self):
        return 0