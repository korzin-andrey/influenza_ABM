from tqdm import tqdm
import time
from Places import Households, Place, Schools, Workplaces
from data_load import load_and_preprocess_data, generate_dict, set_initial_values
import os
import pandas as pd
import numpy as np
from collections import defaultdict
import datetime
import warnings
warnings.filterwarnings('ignore')
pd.options.display.width = None
pd.options.display.max_columns = None

import copy
# import cProfile

def strainForInfIndex(idx):  # idx from 1
    return strains_keys[idx-1]


def infIndexForStrain(strain):
    return strains_keys.index(strain) + 1


def aggregateOutputDics(dic_list, strains_keys):
    dic_res = {}
    for key in strains_keys:
        dic_res[key] = []
        for elem in dic_list:
            dic_res[key].append(elem[key])

    return dic_res


def func_b_r(inf_day):
    a = [0.0, 0.0, 0.9, 0.9, 0.55, 0.3, 0.15, 0.05]
    if inf_day < 9:
        return a[inf_day - 1]
    else:
        return 0







def main(number_seed, data_folder, susceptible,
        lmbd, infected_init_dic, days):
    np.random.seed(number_seed)
    
    strains_keys = infected_init_dic.keys()

    for key in strains_keys:
        I0 = np.random.choice(
            susceptible[susceptible['susceptible_'+key]==1].sp_id, 
            infected_init_dic[key], replace=False
        )

        susceptible.loc[susceptible.sp_id.isin(I0),
                    ['infected', 'susceptible_'+key, 'illness_day']] = [infIndexForStrain(key), 0, 3]

    # создание словарей с восприимчивыми
    dict_hh_id, dict_work_id, dict_school_id, dict_school_len = generate_dict(susceptible, strains_keys)

    infected, incidence_infected = [], []

    # обьекты класса мест, где происходит заражение
    houses_class = Households(lmbd, dict_hh_id)
    works_class = Workplaces(lmbd, dict_work_id)
    schools_class = Schools(lmbd, dict_school_id)

    for day in tqdm(days):
        if len(susceptible[susceptible.illness_day > 2]) != 0:
            x_rand = np.random.rand(10_000_000)
            curr = susceptible[susceptible.infected != 0]

            hh_inf = {i: defaultdict(list) for i in strains_keys}
            work_inf = {i: defaultdict(list) for i in strains_keys}
            school_inf = {i: defaultdict(list) for i in strains_keys}

            index = curr.index.to_numpy()
            ill_day = curr.illness_day.to_numpy()
            strains = curr.infected.to_numpy()
            curr_hh = hh_id[index]
            curr_work = work_id[index]
            curr_school = school_id[index]

            for day, strain, hh, work, school in zip(ill_day, strains, curr_hh, curr_work, curr_school):
                curr_strain = strainForInfIndex(strain)

                hh_inf[curr_strain][hh].append(day)
                if work != 0:
                    work_inf[curr_strain][work].append(day)
                if school != 0:
                    school_inf[curr_strain][school].append(day)


            houses_class.set_place_inf(hh_inf)
            works_class.set_place_inf(work_inf)
            schools_class.set_place_inf(school_inf)
        
            # словари с ключами - штаммами, значениями - id человека
            infected_id_hh = houses_class.infection(x_rand)
            infected_id_work = works_class.infection(x_rand)
            infected_id_school = schools_class.infection(x_rand)

            # реально заразившиеся
            for strain in strains_keys:
                infected_id = np.concatenate(
                    (infected_id_hh[strain], 
                    infected_id_work[strain], 
                    infected_id_school[strain])
                )
                infected_id = np.unique(infected_id.astype(int))

                susceptible.loc[
                            susceptible.sp_id.isin(infected_id), 
                            ['infected', 'illness_day', 'susceptible_'+strain]
                                ] = [infIndexForStrain(strain), 0, 0]

                infected_people = susceptible[(
                    susceptible.sp_id.isin(infected_id))]
                infected_work = infected_people[(susceptible.work_id != 0)
                                                & (susceptible.age > 17)]
                infected_school = infected_people[(susceptible.work_id != 0)
                                                  & (susceptible.age <= 17)]



                # удаление заразившихся из восприимчивых
                houses_class.clean_place(
                    strain,
                    zip(infected_people.sp_hh_id, infected_people.sp_id)
                )

                works_class.clean_place(
                    strain,
                    zip(infected_work.work_id, infected_work.sp_id)
                )

                schools_class.clean_place(
                    strain,
                    zip(infected_school.work_id, infected_school.sp_id)
                )

        # TODO: разбивку по штаммам
        newly_infected = len(
            susceptible[(susceptible.illness_day == 0) & (susceptible.infected != 0)])
        curr_infected = int(susceptible[['infected']].sum())

        infected.append(curr_infected)
        incidence_infected.append(newly_infected)


        pd.DataFrame(infected).to_csv(
            out_path + f"prevalence_{number_seed}.csv")
        pd.DataFrame(incidence_infected).to_csv(
            out_path + f"incidence_{number_seed}.csv")

        # обновление параметров
        susceptible.loc[susceptible.infected != 0, 'illness_day'] += 1
        for key in strains_keys:
            susceptible.loc[susceptible.illness_day > 8, ['susceptible_'+key]] = 0
        susceptible.loc[susceptible.illness_day > 8, ['infected', 'illness_day']] = 0


    return infected


if __name__ == '__main__':
    infected_init_dic = {'H1N1': 10, 'H3N2': 0, 'B': 0}
    alpha_dic = {'H1N1': 0.78, 'H3N2': 0.74, 'B': 0.6}
    lmbd = 0.17
    num_runs = 1
    init_infected = 10
    days = range(1, 150)
    strains_keys = ['H1N1', 'H3N2', 'B']

    data_folder = 'chelyabinsk_15km/'
    data_path = './data/' + data_folder
    out_path = './results/' + data_folder

    # получаем данные
    people, households = load_and_preprocess_data(data_path)

    # задаем невосприимчивых и датафрэйм восприимчивых
    susceptible = set_initial_values(people, strains_keys, alpha_dic)
    susceptible.index = range(len(susceptible))
    susceptible.index = susceptible.index.astype(np.int32)
    hh_id = susceptible.sp_hh_id.to_numpy()
    work_id = susceptible.work_id.to_numpy()
    age = susceptible.age.to_numpy()
    school_id = np.copy(work_id)
    work_id = np.copy(work_id)
    school_id[age > 17] = 0
    school_id[age < 7] = 0
    work_id[age < 18] = 0

    # проверяем наличие output директории
    if not os.path.exists(out_path):
        os.makedirs(out_path)
        print("Directory created successfully!")
    else:
        print("Directory already exists!")

    for i in range(2):
        main(number_seed=i, data_folder=data_folder, 
            susceptible=copy.deepcopy(susceptible), lmbd=lmbd, 
            infected_init_dic=infected_init_dic, days=days
            )
