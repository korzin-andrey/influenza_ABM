import numpy as np

def func_b_r(inf_day):
    a = [0.0, 0.0, 0.9, 0.9, 0.55, 0.3, 0.15, 0.05]
    if inf_day < 9:
        return 0.5
    else:
        return 0

def vectorized():
    return np.vectorize(func_b_r)
