from . import Place
import numpy as np


class Workplaces(Place):

    def __init__(self, lmbd, place_id):
        super().__init__(lmbd, place_id)

    #def prob(self, temp):
    #    return np.repeat(temp, 6) * self.lmbd
