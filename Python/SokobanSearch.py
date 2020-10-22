import sys
import numpy as np
from utilities import Utilities as utils
from defines import *
import math
import time
from dataclasses import dataclass

# position = (row, col)
# index = 1D position

# combi     : state
# '01020304': 1
# '01020305': 2
# . . .
# '32333435': 52360

# '13142122'


@dataclass
class Node:
    state: float
    depth: int
    # boxes_state + agent_state / 100


@dataclass
class Pos:
    x: int
    y: int

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __add__(self, other):
        return Pos(self.x + other.x, self.y + other.y)

class Search:
    def __init__(self, map_file_path):
        self.map_file_path = map_file_path
        self.rows = 0
        self.cols = 0
        self.environment = []

        self.moves = [Pos(-1, 0), Pos(0, 1), Pos(1, 0), Pos(0, -1)]

        self.read_map()
        self.num_boxes, self.num_spaces,  = utils.get_num_boxes_and_spaces(self.rows, self.cols, self.environment)

        self.pos2index, self.index2pos = utils.create_space_and_index_conversion_dictionaries(self.rows, self.cols, self.environment)
        self.boxes_combi2state, self.boxes_state2combi = utils.create_boxes_combinatorics_conversion_dictionaries(self.num_spaces)

        self.boxes_state = self.get_state_of_boxes()
        self.agent_state = self.get_state_of_agent()

        assert self.num_spaces < 100
        assert self.agent_state > 0
        assert len(self.pos2index.keys()) == self.num_spaces
        assert len(self.boxes_combi2state.keys()) == math.comb(self.num_spaces,self.num_boxes)

        self.goal_state = self.get_goal_state()

        self.to_be_visited = []
        self.visited_nodes = {}

    def read_map(self):
        map_file = open(self.map_file_path, 'r')
        lines = map_file.readlines()
        map_rows = [line.replace('\n', '') for line in lines]
        self.rows = len(map_rows)
        self.cols = len(map_rows[0])
        self.environment = np.chararray((self.rows, self.cols), unicode=True)
        for y, row in enumerate(map_rows):
            for x, el in enumerate(row):
                self.environment[y][x] = el

    def stringified_pos(self, pos: Pos):
        return utils.double_digit_stringify_int(pos.y) + utils.double_digit_stringify_int(pos.x)

    def print_environment(self,node: Node):
        for row in range(self.rows):
            for col in range(self.cols):
                el = Pos(col,row)
                if self.pos2index.get(self.stringified_pos(el)) is None:
                    self.environment[row][col] = WALL
                else:
                    self.environment[row][col] = PASSAGE

        agent_state = round((node.state % 1) * 100)
        agent_pos = self.get_pos_from_index(agent_state)

        boxes_state = math.floor(node.state)
        boxes_combi = self.boxes_state2combi[boxes_state]
        boxes_positions = self.get_positions_of_boxes(boxes_combi)

        self.environment[agent_pos.y][agent_pos.x] = AGENT

        for box_pos in boxes_positions:
            self.environment[box_pos.y][box_pos.x] = BOX

        print(self.environment)

    def get_pos_from_index(self,index):
        pos = self.index2pos[index]
        row = int(pos[:2])
        col = int(pos[2:])
        return Pos(col, row)

    def get_state_of_boxes(self):
        box_pos = ''
        for row in range(self.rows):
            for col in range(self.cols):
                if self.environment[row][col] == BOX:
                    row_key = utils.double_digit_stringify_int(row)
                    col_key = utils.double_digit_stringify_int(col)
                    key = row_key + col_key
                    index = self.pos2index[key]
                    index_key = utils.double_digit_stringify_int(index)
                    box_pos += index_key
        return self.boxes_combi2state[box_pos]

    def get_state_of_agent(self):
        agent_index = 0
        for row in range(self.rows):
            for col in range(self.cols):
                if self.environment[row][col] == AGENT:
                    row_key = utils.double_digit_stringify_int(row)
                    col_key = utils.double_digit_stringify_int(col)
                    key = row_key + col_key
                    agent_index = self.pos2index[key]

        return agent_index

    def get_goal_state(self):
        goal_pos = ''
        for row in range(self.rows):
            for col in range(self.cols):
                if self.environment[row][col] == GOAL:
                    row_key = utils.double_digit_stringify_int(row)
                    col_key = utils.double_digit_stringify_int(col)
                    key = row_key + col_key
                    index = self.pos2index[key]
                    index_key = utils.double_digit_stringify_int(index)
                    goal_pos += index_key
        return self.boxes_combi2state[goal_pos]

    def get_positions_of_boxes(self,index: str):
        box_indeces = [int(index[i:i + 2]) for i in range(0, len(index), 2)]
        box_positions = []
        for box_index in box_indeces:
            box_positions.append(self.get_pos_from_index(box_index))
        return box_positions

    def get_combi_from_box_positions(self, positions):
        combi = ''
        for pos in positions:
            combi += utils.double_digit_stringify_int(self.pos2index.get(self.stringified_pos(pos),99))
        return utils.get_sorted_indeces(combi)

    def generate_children(self, node: Node):
        agent_state = round((node.state % 1) * 100)
        agent_pos = self.get_pos_from_index(agent_state)

        boxes_state = math.floor(node.state)
        boxes_combi = self.boxes_state2combi[boxes_state]
        boxes_positions = self.get_positions_of_boxes(boxes_combi)

        children = []

        for move in self.moves:
            next_agent_pos = agent_pos + move
            new_agent_state = self.pos2index.get(self.stringified_pos(next_agent_pos))
            if new_agent_state is None:
                continue

            new_boxes_positions = []
            for box_pos in boxes_positions:
                if next_agent_pos == box_pos:
                    new_box_pos = box_pos + move
                    new_boxes_positions.append(new_box_pos)
                else:
                    new_boxes_positions.append(box_pos)

            combi = self.get_combi_from_box_positions(new_boxes_positions)

            new_boxes_state = self.boxes_combi2state.get(combi)
            if new_boxes_state is None:
                continue

            new_state = new_boxes_state + new_agent_state / 100
            children.append(Node(new_state,node.depth + 1))

        return children

            # TODO Don't care about checking game physics. All possible combinations and positions have been generated.
            #  Look up in dictionary. If dictionary returns default value then the position is illegal. (out of bounds)
            #  Move boxes if agent index == box index. If new box combinations does not exist in dictionary. It is
            #  invalid.

    def BFS(self):
        init_state = self.boxes_state + self.agent_state / 100
        depth = 0
        root = Node(init_state,depth)
        self.to_be_visited.append(root)

        while self.to_be_visited:
            #print(self.to_be_visited)
            #print(self.visited_nodes)
            c_node = self.to_be_visited.pop(0)
            # TODO maybe make own stack
            #print(c_node)
            #self.print_environment(c_node)
            self.visited_nodes[c_node.state] = 1
            if math.floor(c_node.state) == self.goal_state:
                print("Found goal state. WIN :)")
                break

            children = self.generate_children(c_node)

            # appending the new node to the to be visited list will make it a breath first search (FIFO)
            # adding the new node to the front of the to be visited list will make it depth first search (LIFO)
            for child in children:
                if child.depth > depth:
                    print(depth)
                    print(len(self.visited_nodes.keys()))
                    depth = child.depth
                if self.visited_nodes.get(child.state) is None:
                    self.to_be_visited.append(child)

s = Search('../map.txt')
s.BFS()
