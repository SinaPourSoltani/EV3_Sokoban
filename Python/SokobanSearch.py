from __future__ import annotations
from _collections import deque
import numpy as np
import math
import time
from dataclasses import dataclass

from utilities import Utilities as utils
from utilities import Pos
from defines import *
from simulation import Simulation
from simulation import Display
import pygame
from pygame.locals import *

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
    parent_node: Node
    state: float
    depth: int
    # boxes_state + agent_state / 100


def wait():
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                exit()
            if event.type == KEYDOWN and event.key == K_SPACE:
                return

class Search:
    def __init__(self, map_file_path):
        self.map_file_path = map_file_path
        self.rows = 0
        self.cols = 0
        self.environment = []

        self.moves = [Pos(-1, 0), Pos(0, -1), Pos(1, 0), Pos(0, 1)]

        self.num_boxes, self.num_spaces = self.read_map()

        self.corners = self.detect_corners()

        self.pos2index, self.index2pos = utils.create_space_and_index_conversion_dictionaries(self.rows, self.cols, self.environment)
        self.boxes_positions2state, self.boxes_state2positions = utils.create_boxes_combinatorics_conversion_dictionaries(self.num_spaces,self.index2pos,self.corners)
        self.move2dir, self.dir2move = utils.create_move_and_dir_dictionaries()

        self.boxes_state = self.get_state_of_boxes()
        self.agent_state = self.get_state_of_agent()

        assert self.num_spaces < 100
        assert self.agent_state > 0
        assert len(self.pos2index.keys()) == self.num_spaces
        assert len(self.boxes_positions2state.keys()) == math.comb(self.num_spaces,self.num_boxes)

        self.goal_state = self.get_goal_state()

        self.display = Display((self.cols, self.rows))
        self.display.update(self.environment, self.index2pos[self.agent_state])

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

        num_boxes = num_spaces = 0
        for y, row in enumerate(map_rows):
            for x, el in enumerate(row):
                if self.environment[y][x] == BOX:
                    num_boxes += 1
                if self.environment[y][x] != WALL:
                    num_spaces += 1
        return num_boxes, num_spaces

    def detect_corners(self):
        corners = []
        for y in range(self.rows):
            for x in range(self.cols):
                if self.environment[y][x] != WALL and self.environment[y][x] != GOAL:
                    num_surrounding_walls = 0
                    env_pos = Pos(x,y)
                    for move in self.moves:
                        surrounding_space = env_pos + move
                        if self.environment[surrounding_space.y][surrounding_space.x] == WALL:
                            num_surrounding_walls += 1
                    if num_surrounding_walls >= 2:
                        corners.append(env_pos)
        return corners

    def print_environment(self,node: Node):
        for row in range(self.rows):
            for col in range(self.cols):
                el = Pos(col,row)
                if self.pos2index.get(el) is None:
                    self.environment[row][col] = WALL
                else:
                    self.environment[row][col] = PASSAGE

        agent_state = round((node.state % 1) * 100)
        agent_pos = self.index2pos[agent_state]

        boxes_state = math.floor(node.state)
        boxes_positions = self.boxes_state2positions[boxes_state]

        self.environment[agent_pos.y][agent_pos.x] = AGENT

        for box_pos in boxes_positions:
            self.environment[box_pos.y][box_pos.x] = BOX

        print(self.environment)

    def get_state_of_boxes(self):
        box_positions = ()
        for row in range(self.rows):
            for col in range(self.cols):
                if self.environment[row][col] == BOX:
                    key = Pos(col, row),
                    box_positions += key
        box_positions = tuple(sorted(box_positions))
        return self.boxes_positions2state[box_positions]

    def get_state_of_agent(self):
        agent_index = 0
        for row in range(self.rows):
            for col in range(self.cols):
                if self.environment[row][col] == AGENT:
                    key = Pos(col, row)
                    agent_index = self.pos2index[key]
        return agent_index

    def get_goal_state(self):
        goal_positions = ()
        for row in range(self.rows):
            for col in range(self.cols):
                if self.environment[row][col] == GOAL:
                    key = Pos(col, row),
                    goal_positions += key
        goal_positions = tuple(sorted(goal_positions))
        return self.boxes_positions2state[goal_positions]

    def generate_children(self, node: Node):
        agent_state = round((node.state % 1) * 100)
        agent_pos = self.index2pos[agent_state]

        boxes_state = math.floor(node.state)
        boxes_positions = self.boxes_state2positions[boxes_state]

        children = []

        for move in self.moves:
            next_agent_pos = agent_pos + move
            new_agent_state = self.pos2index.get(next_agent_pos)
            if new_agent_state is None:
                continue

            new_boxes_positions = ()
            for box_pos in boxes_positions:
                if next_agent_pos == box_pos:
                    new_box_pos = box_pos + move
                    new_boxes_positions += new_box_pos,
                else:
                    new_boxes_positions += box_pos,

            new_boxes_positions = tuple(sorted(new_boxes_positions))
            new_boxes_state = self.boxes_positions2state.get(new_boxes_positions)
            # If new_boxes_state is None it means that the boxes positions are not possible
            # if new_boxes_state is negative it indicates a deadlock
            if new_boxes_state is None or new_boxes_state < 0:
                continue

            new_state = new_boxes_state + new_agent_state / 100
            children.append(Node(node, new_state, node.depth + 1))

        return children

            # TODO Don't care about checking game physics. All possible combinations and positions have been generated.
            #  Look up in dictionary. If dictionary returns default value then the position is illegal. (out of bounds)
            #  Move boxes if agent index == box index. If new box combinations does not exist in dictionary. It is
            #  invalid.

    def find_path(self, node: Node):
        visited_states = [node.state]
        while node.parent_node is not None:
            node = node.parent_node
            visited_states.append(node.state)

        visited_states.reverse()

        moves = ""
        for i, state in enumerate(visited_states):
            if i != len(visited_states) - 1:
                agent_index = round((state % 1) * 100)
                agent_pos = self.index2pos[agent_index]

                next_state = visited_states[i+1]
                next_agent_index = round((next_state % 1) * 100)
                next_agent_pos = self.index2pos[next_agent_index]

                move = next_agent_pos - agent_pos

                boxes_moved = math.floor(next_state) != math.floor(state)

                dir = self.move2dir[move] if boxes_moved else self.move2dir[move].lower()
                moves += dir
        return moves

    def trail(self, node: Node):
        trail = []

        c_node = node
        while c_node.parent_node is not None:
            c_node = c_node.parent_node
            agent_state = round((c_node.state % 1) * 100)
            agent_pos = self.index2pos[agent_state]
            trail.append(agent_pos)

        return trail

    def solution_found(self, solution: str):
        print("Solution:", solution)
        sim = Simulation(self.environment, self.index2pos[self.agent_state], solution)
        print("Press SPACE to run simulation.")
        sim.run()

    def BFS(self):
        init_state = self.boxes_state + self.agent_state / 100
        depth = 0
        root = Node(None, init_state, depth)
        to_be_visited = deque([root])
        to_be_visited_lookup = {}
        visited_nodes = {}


        while to_be_visited:
            #print(to_be_visited)
            #print(self.to_be_visited)
            #print(self.visited_nodes)

            c_node = to_be_visited.popleft()

            #print("Prnt",c_node.parent_node.state if c_node.parent_node is not None else "None")
            #print("Crnt", c_node.state)
            #self.print_environment(c_node)
            #indexx = round((c_node.state % 1) * 100)
            #poss = self.index2pos[indexx]
            #trail = self.trail(c_node)
            #print("Agent_i:",indexx, "_pos:",poss)
            #self.display.update(self.environment, poss, trail)
            #wait()

            visited_nodes[c_node.state] = 1
            if math.floor(c_node.state) == self.goal_state:
                print("Found goal state. WIN :)")
                solution = self.find_path(c_node)
                self.solution_found(solution)
                break

            children = self.generate_children(c_node)

            # appending the new node to the to be visited list will make it a breath first search (FIFO)
            # adding the new node to the front of the to be visited list will make it depth first search (LIFO)
            # appendleft for DFS
            for child in children:
                if child.depth > depth:
                    print(depth)
                    print(len(visited_nodes.keys()))
                    depth = child.depth
                if visited_nodes.get(child.state) is None:
                    # check look up of to_be_visited states to avoid adding duplicate states
                    if to_be_visited_lookup.get(child.state) is None:
                        to_be_visited.appendleft(child)
                        to_be_visited_lookup[child.state] = 1

        print(visited_nodes)

s = Search('../map.txt')
s.BFS()
