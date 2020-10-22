import sys
from defines import *
from dataclasses import dataclass

@dataclass
class Pos:
    x: int
    y: int

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __add__(self, other):
        return Pos(self.x + other.x, self.y + other.y)

class Utilities:
    @staticmethod
    def double_digit_stringify_int(num):
        return '0' + str(num) if num < 10 else str(num)

    @staticmethod
    def get_sorted_indeces(indeces):
        box_indeces = [int(indeces[i:i + 2]) for i in range(0, len(indeces), 2)]
        box_indeces.sort()
        mapped = map(Utilities.double_digit_stringify_int, box_indeces)
        return "".join(mapped)

    @staticmethod
    def get_num_boxes_and_spaces(rows, cols, environment):
        boxes = 0
        spaces = 0
        for row in range(rows):
            for col in range(cols):
                if environment[row][col] == BOX:
                    boxes += 1
                if environment[row][col] != WALL:
                    spaces += 1
        return boxes, spaces

    @staticmethod
    def create_space_and_index_conversion_dictionaries(rows, cols, environment):
        value = 0
        pos2index = {}
        for row in range(rows):
            for col in range(cols):
                if environment[row][col] != WALL:
                    rowkey = Utilities.double_digit_stringify_int(row)
                    colkey = Utilities.double_digit_stringify_int(col)
                    key = rowkey + colkey
                    value += 1
                    pos2index[sys.intern(key)] = value

        index2pos = {v: k for k, v in pos2index.items()}
        return pos2index, index2pos

    @staticmethod
    def create_boxes_combinatorics_conversion_dictionaries(num_spaces):
        boxes_index2states = {}
        value = 0
        for n1 in range(1, num_spaces + 1):
            for n2 in range(n1 + 1, num_spaces + 1):
                for n3 in range(n2 + 1, num_spaces + 1):
                    for n4 in range(n3 + 1, num_spaces + 1):
                        key1 = Utilities.double_digit_stringify_int(n1)
                        key2 = Utilities.double_digit_stringify_int(n2)
                        key3 = Utilities.double_digit_stringify_int(n3)
                        key4 = Utilities.double_digit_stringify_int(n4)
                        key = key1 + key2 + key3 + key4
                        value += 1
                        boxes_index2states[sys.intern(key)] = value

        boxes_states2index = {v: k for k, v in boxes_index2states.items()}
        return boxes_index2states, boxes_states2index
