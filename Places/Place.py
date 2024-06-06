import numpy as np
from infectiousness import vectorized

class Place:
    '''
    Интерфейс для всех локаций    

    Args:
        lmbd             (int):     вирулентность
        place_id    (dict):    словарь с ключами - id места, а значения - id тех, кто там находится          
    '''

    def __init__(self, lmbd, place_id):

        self.lmbd = lmbd
        self.dict_place_id = place_id
        self.vfunc = vectorized() # векторизованная функция вычисления заразности человека
        self.place_inf = None
        

    def prob(self, temp, place_len):
        return np.repeat(temp, place_len) * self.lmbd


    def set_place_inf(self, place_inf):
        self.place_inf = place_inf      #dict_strain(dict_place(list_sp_id))
        return True


    def infection(self, x_rand):
        real_inf_place = dict()
        
        # strains' iteration
        for strain in self.place_inf.keys():

            real_inf_place[strain] = np.array([])
            
            # places' iteration
            for i in self.place_inf[strain]:
                # текущее количество восприимчивых к данному штамму
                try:
                    place_len = len(self.dict_place_id[strain][i])
                    
                    if place_len != 0:
                        # вычисление заразности каждого заболевшего
                        temp = self.vfunc(self.place_inf[strain][i])

                        # вероятность заражения подверженных
                        prob = self.prob(temp, place_len)
                        contact_length = len(prob)

                        # вероятность не заразиться
                        place_rand = x_rand[:contact_length]
                        x_rand = x_rand[contact_length:]


                        # количество реально заразившихся людей
                        real_inf = len(place_rand[place_rand < prob])
                        real_inf = place_len if place_len < real_inf else real_inf

                        real_inf_id = np.random.choice(
                            np.array(self.dict_place_id[strain][i]), real_inf, replace=False)
                        real_inf_place[strain] = np.concatenate((real_inf_place[strain], real_inf_id))
    
                except:
                    pass # в данном месте нет восприимчивым с данным штаммом
                         # происходит так как словари создаются после задания больных
                         # следовательно в самом начале нет удаления и нет пустых списков
        return real_inf_place


    def clean_place(self, strain, iterator):
        for place_id, person_id in iterator:
            self.dict_place_id[strain][place_id].remove(person_id)
        return True
