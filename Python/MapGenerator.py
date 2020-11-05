from defines import *
import random
import numpy as np
from utilities import Pos

class MapGenerator:
    def __init__(self, row, col):
        self.rows = row
        self.cols = col
        self.environment = np.chararray((self.rows, self.cols), unicode=True)

        self.moves = [Pos(-1, 0), Pos(0, -1), Pos(1, 0), Pos(0, 1)]

        self.generate_map()


    def write_txt_file(self):
        with open("generated_map.txt", 'w') as file:
            file = open("generated_map.txt", 'w')
            for row in range(self.rows):
                for col in range(self.cols):
                    file.write(self.environment[row][col])
                file.write('\n')

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


    def generate_map(self):
        num_boxes = random.randint(1,2)
        num_goals = num_boxes

        for row in range(self.rows):
            self.environment[row][0] = WALL
            self.environment[row][self.cols-1] = WALL

        for col in range(self.cols):
            self.environment[0][col] = WALL
            self.environment[self.rows-1][col] = WALL


        for row in range(1,self.rows - 1):
            for col in range(1, self.cols - 1):
                if random.uniform(0,1) > 0.9:
                    self.environment[row][col] = WALL
                else:
                    self.environment[row][col] = PASSAGE

        for goal in range(num_goals):
            goal_placed = False
            while not goal_placed:
                x_rand = random.randint(1, self.cols - 2)
                y_rand = random.randint(1, self.rows - 2)
                if self.environment[y_rand][x_rand] != WALL and self.environment[y_rand][x_rand] != GOAL :
                    self.environment[y_rand][x_rand] = GOAL
                    goal_placed = True


        corners = self.detect_corners()

        for box in range(num_boxes):
            box_placed= False
            while not box_placed:
                x_rand = random.randint(1, self.cols - 2)
                y_rand = random.randint(1, self.rows - 2)
                pos = Pos(x_rand,y_rand)
                corner_exist = False
                for corner in corners:
                    if pos == corner:
                        corner_exist = True
                        break
                if self.environment[y_rand][x_rand] != WALL and self.environment[y_rand][x_rand] != BOX and self.environment[y_rand][x_rand] != GOAL and not corner_exist:
                    self.environment[y_rand][x_rand] = BOX
                    box_placed = True


        agent_placed = False
        while not agent_placed:
            x_rand = random.randint(1, self.cols - 2)
            y_rand = random.randint(1, self.rows - 2)
            if self.environment[y_rand][x_rand] == PASSAGE:
                self.environment[y_rand][x_rand] = AGENT
                agent_placed = True
        print("# Boxes:",num_boxes)
        print("# Goals:",num_goals)
        print(self.environment)
        self.write_txt_file()
