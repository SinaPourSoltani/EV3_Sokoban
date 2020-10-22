import math
from utilities import Utilities as utils

def comb(num_spaces, num_boxes, *indeces, combinations=None):
    if combinations is None:
        combinations = []

    print(num_spaces, num_boxes, indeces)

    if len(indeces) == num_boxes:
        for i in range(1, num_boxes):
            if indeces[num_boxes - i] == num_spaces:
                indeces = indeces[:-i-1] + tuple(range(indeces[-i-1]+1, indeces[-i-1]+1 + num_boxes - i - 1))
                comb(num_spaces, num_boxes, *indeces)

    if len(indeces) == 0:
        indeces = 1,

    if len(indeces) < num_boxes:
        value_of_last_index = indeces[-1]
        indeces += value_of_last_index + 1,
        combi = comb(num_spaces, num_boxes, *indeces)
        if combi is not None:
            combinations.append(combi)

    elif indeces[num_boxes - 1] == num_spaces:
        return

    elif len(indeces) == num_boxes:
        indeces = indeces[:-1] + (indeces[-1]+1,)
        comb(num_spaces,num_boxes,*indeces)

    combi = ""
    for index in indeces:
        combi += utils.double_digit_stringify_int(index)
    return combi


def combinations(n, k, min_n=0, accumulator=None):
    if accumulator is None:
        accumulator = []
    if k == 0:
        return [accumulator]
    else:
        return [l for x in range(min_n, n)
                for l in combinations(n, k - 1, x + 1, accumulator + [x + 1])]

#comb(10,4)


print(len(combinations(35,4)))





