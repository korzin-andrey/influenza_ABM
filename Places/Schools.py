from . import Place
import numpy as np


class Schools(Place):

    def __init__(self, lmbd, place_id):
        super().__init__(lmbd, place_id)

    #def prob(self, temp):
    #    return np.repeat(temp, 7) * self.lmbd

