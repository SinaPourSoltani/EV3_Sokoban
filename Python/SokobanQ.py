from dataclasses import dataclass
import numpy as np
import pygame
from pygame.locals import *
import time
import math
import random

# DEFINES
AGENT = 'M'
CAN = 'J'
GOAL = 'G'
GOAL_FILLED = 'F'
WALL = 'X'
PASSAGE = '.'

# ACTIONS
LEFT = 0
UP = 1
RIGHT = 2
DOWN = 3
possible_actions = [LEFT,UP,RIGHT,DOWN]

WHITE, BLACK = (255,255,255), (0,0,0),
GREEN, ORANGE = (20,200,20), (255,150,10)
GREY, PURPLE = (100,100,100), (60,15,180)
RED = (255,0,0)

discount_rate = 0.9
epsilon = 0.1
alpha = 0.4


@dataclass
class State:
    x: int
    y: int

    def move(self, a):
        if a == UP:
            self.y -= 1
        elif a == DOWN:
            self.y += 1
        elif a == LEFT:
            self.x -= 1
        elif a == RIGHT:
            self.x += 1

    def copy(self):
        return State(self.x,self.y)

    def equals(self,other):
        return self.x == other.x and self.y == other.y


@dataclass
class AgentState(State):
    def __init__(self,x,y,is_outside_environment):
        super().__init__(x,y)
        self.is_outside_environment = is_outside_environment

    def copy_agent(self):
        return AgentState(self.x,self.y,self.is_outside_environment)


@dataclass
class CanState(State):
    def __init__(self,x,y,id):
        super().__init__(x,y)
        self.id = id

    def copy_can(self):
        return CanState(self.x,self.y,self.id)


@dataclass
class GoalState(State):
    def __init__(self,x,y,is_filled):
        super().__init__(x,y)
        self.is_filled = is_filled


TERMINAL_STATE = AgentState(-1,-1,True)


class SokobanQ:
    def __init__(self, map_file_path):
        self.map_file_path = map_file_path
        self.rows = 0
        self.cols = 0
        self.environment = []
        self.read_map()
        self.print_environment()

        self.state = TERMINAL_STATE
        self.goal_states = []
        self.can_states = []

        self.set_initial_states()

        self.display = Display((self.cols,self.rows))
        self.display.update(self.environment,self.state)
        self.start_game()

    def read_map(self):
        map_file = open(self.map_file_path, 'r')
        lines = map_file.readlines()
        map_rows = [line.replace('\n', '') for line in lines]
        self.rows = len(map_rows)
        self.cols = len(map_rows[0])
        self.environment = np.chararray((self.rows,self.cols),unicode=True)
        for y, row in enumerate(map_rows):
            for x, el in enumerate(row):
                self.environment[y][x] = el

    def update_environment(self):
        for row in range(self.rows):
            for col in range(self.cols):
                if self.environment[row][col] != WALL:
                    self.environment[row][col] = PASSAGE

        for cs in self.can_states:
            self.environment[cs.y][cs.x] = CAN

        for gs in self.goal_states:
            self.environment[gs.y][gs.x] = GOAL_FILLED if gs.is_filled else GOAL

    def print_environment(self):
        print(self.environment)

    def set_initial_states(self):
        can_id = 0
        for row in range(self.rows):
            for col in range(self.cols):
                if self.environment[row][col] == CAN:
                    self.can_states.append(CanState(col,row,can_id))
                    can_id += 1
                elif self.environment[row][col] == GOAL:
                    self.goal_states.append(GoalState(col,row,False))
                elif self.environment[row][col] == AGENT:
                    self.environment[row][col] = PASSAGE
                    self.state = AgentState(col,row,False)

    def update_states(self):
        num_goals_filled = 0
        for gs in self.goal_states:
            can_on_goal = False
            for cs in self.can_states:
                if gs.equals(cs):
                    can_on_goal = True
            num_goals_filled += 1 if can_on_goal else 0
            gs.is_filled = can_on_goal

        if num_goals_filled == len(self.goal_states):
            print("WON")

    def get_can_id_from_state(self,s):
        for can in self.can_states:
            if can.equals(s):
                return can.id

    def get_next_state(self, s, a):
        next_s = s.copy_agent()
        next_s.move(a)

        if self.environment[next_s.y][next_s.x] == WALL:
            return s

        if self.environment[next_s.y][next_s.x] == CAN or self.environment[next_s.y][next_s.x] == GOAL_FILLED:
            can_id = self.get_can_id_from_state(next_s)
            next_can = self.can_states[can_id].copy_can()
            next_can.move(a)

            if self.environment[next_can.y][next_can.x] == WALL or self.environment[next_can.y][next_can.x] == CAN or self.environment[next_can.y][next_can.x] == GOAL_FILLED:
                return s
            elif self.environment[next_can.y][next_can.x] == PASSAGE or self.environment[next_can.y][next_can.x] == GOAL:
                self.can_states[can_id] = next_can
                return next_s

        return next_s

    def start_game(self):
        while True:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN:
                    print(self.environment)
                    if event.key == pygame.K_UP:
                        self.state = self.get_next_state(self.state,UP)
                    if event.key == pygame.K_DOWN:
                        self.state = self.get_next_state(self.state,DOWN)
                    if event.key == pygame.K_LEFT:
                        self.state = self.get_next_state(self.state,LEFT)
                    if event.key == pygame.K_RIGHT:
                        self.state = self.get_next_state(self.state,RIGHT)

            self.update_states()
            self.update_environment()
            self.display.update(self.environment, self.state)
            pygame.time.Clock().tick(30)

class Display:
    def __init__(self, grid_size):
        self.grid_size = grid_size
        self.tile_size = 80

        self.window_width = grid_size[0] * self.tile_size
        self.window_height = grid_size[1] * self.tile_size

        pygame.init()
        self.display = pygame.display.set_mode((self.window_width, self.window_height))

    def draw_grid(self):
        for row in range(self.grid_size[1]):
            for col in range(self.grid_size[0]):
                pygame.draw.rect(self.display, BLACK,[col * self.tile_size, row * self.tile_size, self.tile_size, self.tile_size],1)

    def update(self, environment,state):
        self.display.fill(WHITE)
        self.draw_grid()

        for row in range(self.grid_size[1]):
            for col in range(self.grid_size[0]):
                el = environment[row][col]
                if el == WALL:
                    pygame.draw.rect(self.display, GREY, [col * self.tile_size, row * self.tile_size, self.tile_size, self.tile_size])
                elif el == CAN:
                    pygame.draw.rect(self.display, ORANGE, [col * self.tile_size + self.tile_size * 0.1, row * self.tile_size + self.tile_size * 0.1, self.tile_size * 0.8, self.tile_size * 0.8])
                elif el == GOAL:
                    pygame.draw.rect(self.display, RED, [col * self.tile_size + self.tile_size * 0.1, row * self.tile_size + self.tile_size * 0.1, self.tile_size * 0.8, self.tile_size * 0.8])
                elif el == GOAL_FILLED:
                    pygame.draw.rect(self.display, GREEN, [col * self.tile_size + self.tile_size * 0.1, row * self.tile_size + self.tile_size * 0.1, self.tile_size * 0.8, self.tile_size * 0.8])

        col = state.x
        row = state.y
        pygame.draw.circle(self.display, PURPLE, (col * self.tile_size + 0.5 * self.tile_size, row * self.tile_size + 0.5 * self.tile_size), self.tile_size * 0.3)

        pygame.display.update()

sokoban = SokobanQ("../map.txt")
