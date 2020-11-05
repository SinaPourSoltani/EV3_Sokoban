from copy import deepcopy
import pygame
from pygame.locals import *
from defines import *
from utilities import Pos
from utilities import Utilities as utils


class Simulation:
    def __init__(self, env, agent_pos: Pos, solution: str):
        self.env = env
        self.init_env = env
        self.rows, self.cols = env.shape
        self.agent_pos = agent_pos
        self.init_agent_pos = agent_pos
        self.solution = solution

        self.move2dir, self.dir2move = utils.create_move_and_dir_dictionaries()
        self.display = Display((self.cols, self.rows))
        self.display.update(self.env, self.agent_pos)

    def set_environment(self, move: Pos):
        self.agent_pos += move

        if self.env[self.agent_pos.y][self.agent_pos.x] == BOX or self.env[self.agent_pos.y][self.agent_pos.x] == GOAL_FILLED:
            self.env[self.agent_pos.y][self.agent_pos.x] = GOAL if self.env[self.agent_pos.y][self.agent_pos.x] == GOAL_FILLED else PASSAGE

            if self.env[self.agent_pos.y + move.y][self.agent_pos.x + move.x] == GOAL:
                self.env[self.agent_pos.y + move.y][self.agent_pos.x + move.x] = GOAL_FILLED
            else:
                self.env[self.agent_pos.y + move.y][self.agent_pos.x + move.x] = BOX

    def run(self):
        is_running = True
        while is_running:
            for event in pygame.event.get():
                if event.type == QUIT or event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    is_running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.env = deepcopy(self.init_env)
                        self.agent_pos = self.init_agent_pos
                        self.display.update(self.env,self.agent_pos)
                        for c in self.solution:
                            move = self.dir2move[c]
                            self.set_environment(move)
                            self.display.update(self.env, self.agent_pos)
                            pygame.time.Clock().tick(15)



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
                pygame.draw.rect(self.display, BLACK,
                                 [col * self.tile_size, row * self.tile_size, self.tile_size, self.tile_size], 1)

    def update(self, environment, agent_pos: Pos, trail=None):
        self.display.fill(WHITE)
        self.draw_grid()

        for row in range(self.grid_size[1]):
            for col in range(self.grid_size[0]):
                el = environment[row][col]
                if el == WALL:
                    pygame.draw.rect(self.display, GREY,
                                     [col * self.tile_size, row * self.tile_size, self.tile_size, self.tile_size])
                elif el == BOX:
                    pygame.draw.rect(self.display, ORANGE, [col * self.tile_size + self.tile_size * 0.1,
                                                            row * self.tile_size + self.tile_size * 0.1,
                                                            self.tile_size * 0.8, self.tile_size * 0.8])
                elif el == GOAL:
                    pygame.draw.rect(self.display, RED, [col * self.tile_size + self.tile_size * 0.1,
                                                         row * self.tile_size + self.tile_size * 0.1,
                                                         self.tile_size * 0.8, self.tile_size * 0.8])
                elif el == GOAL_FILLED:
                    pygame.draw.rect(self.display, GREEN, [col * self.tile_size + self.tile_size * 0.1,
                                                           row * self.tile_size + self.tile_size * 0.1,
                                                           self.tile_size * 0.8, self.tile_size * 0.8])

        if trail is not None:
            for i, pos in enumerate(trail):
                col = pos.x
                row = pos.y

                pygame.draw.circle(self.display, PURPLE,
                                   (int(col * self.tile_size + 0.5 * self.tile_size),
                                    int(row * self.tile_size + 0.5 * self.tile_size)),
                                   int(self.tile_size * 0.3))

                s = pygame.Surface((self.tile_size, self.tile_size))  # the size of your rect
                s.set_alpha(130 + i * 8)
                s.fill((255, 255, 255))
                self.display.blit(s, (col * self.tile_size,
                                    row * self.tile_size))

        col = agent_pos.x
        row = agent_pos.y
        pygame.draw.circle(self.display, PURPLE,
                           (int(col * self.tile_size + 0.5 * self.tile_size),
                            int(row * self.tile_size + 0.5 * self.tile_size)),
                           int(self.tile_size * 0.3))

        pygame.display.update()

