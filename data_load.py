import pandas as pd
import numpy as np

# в папке по пути data_path должны находиться файлы:
#   -- people.txt
#   -- households.txt
#   -- workplaces.txt
#   -- schools.txt


def load_and_preprocess_data(data_path):
    # данные о популяции людей
    data = pd.read_csv(data_path + 'people.txt', sep='\t', index_col=0)
    data = data[['sp_id', 'sp_hh_id', 'age', 'sex', 'work_id']]

    # данные о домовладениях
    households = pd.read_csv(data_path + 'households.txt', sep='\t')
    households = households[['sp_id', 'latitude', 'longitude']]


    # подготовка загруженных данных
    data[['sp_id', 'sp_hh_id', 'age']] = data[[
        'sp_id', 'sp_hh_id', 'age']].astype(int)
    data[['work_id']] = data[['work_id']].replace('X', 0).astype(int)
    data = data.sample(frac=1)

    households[['sp_id']] = households[['sp_id']].astype(int)
    households[['latitude', 'longitude']] = households[[
        'latitude', 'longitude']].astype(float)
    households.index = households.sp_id

    return data, households


def generate_dict(data, strains_keys):
    dict_hh_id = {}
    dict_work_id = {}
    dict_school_id = {}
    dict_school_len = {}

    for i in strains_keys:
        cur_susc = data[ (data['susceptible_'+i]==1) & (data.infected==0) ]

        dict_hh_id[i] = {ind[0]: list(ind[1]) for ind in cur_susc.groupby('sp_hh_id').sp_id}

        dict_work_id[i] = {ind[0]: list(ind[1]) for ind in cur_susc[ (cur_susc.age>17) & (cur_susc.work_id!=0) ].groupby('work_id').sp_id}

        dict_school_id[i] = {ind[0]: list(ind[1]) for ind in cur_susc[ (cur_susc.age<=17) & (cur_susc.work_id!=0) ].groupby('work_id').sp_id}

    dict_school_len[i] = {j[0]: len(j[1]) for j in data[(data.age<=17)&(data.work_id!=0)].groupby('work_id').sp_id}

    return dict_hh_id, dict_work_id, dict_school_id, dict_school_len


def set_initial_values(data, strains_keys, alpha_dic):
    for key in strains_keys:  # По умолчанию все иммунные
        data['susceptible_'+key] = 0

    data['infected'] = 0
    data['illness_day'] = 0

    for key in strains_keys:
        data.loc[np.random.choice(data.index, round(len(
            data) * alpha_dic[key]), replace=False), 'susceptible_'+key] = 1
    return data
