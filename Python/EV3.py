#!/usr/bin/python
import ev3dev.ev3 as ev3
import signal
from time import sleep

# defines
STOP_SPEED = 0
CRUISE_SPEED = 60
ADJUST_SPEED = CRUISE_SPEED * 1.2
TURN_SPEED = 30

END = 'X'

TURN_TIME = 1.1

# colors
BLACK = 1
WHITE = 0
COLOR_THRESHOLD = 30

# directions
FORWARD = 1
REVERSE = -1

# orientations
LEFT = 0
UP = 1
RIGHT = 2
DOWN = 3

ORI2INDEX = {
    'l': LEFT,
    'u': UP,
    'r': RIGHT,
    'd': DOWN,
    'L': LEFT,
    'U': UP,
    'R': RIGHT,
    'D': DOWN,
}

INDEX2ORI = {
    LEFT:   'LEFT',
    UP:     'UP',
    RIGHT:  'RIGHT',
    DOWN:   'DOWN',
}

class EV3:
    def __init__(self, start_orientation, solution):
        self.current_orientation = start_orientation

        self.m_left = ''
        self.m_right = ''
        self.cs_left = ''
        self.cs_right = ''
        self.setup_IO()
        self.IS_PUSHING = False

        signal.signal(signal.SIGINT, self.signal_handler)
        self.execute(solution)

    def signal_handler(self, sig, frame):
        print('Shutting down gracefully')
        self.m_left.duty_cycle_sp = 0
        self.m_right.duty_cycle_sp = 0
        exit(0)

    def setup_IO(self):
        self.cs_left = ev3.ColorSensor('in1')
        self.cs_right = ev3.ColorSensor('in4')

        self.m_left = ev3.LargeMotor('outC')
        self.m_right = ev3.LargeMotor('outD')
        self.m_right.polarity = "normal"
        self.m_left.polarity = "normal"
        self.m_right.duty_cycle_sp = STOP_SPEED
        self.m_left.duty_cycle_sp = STOP_SPEED
        #self.m_left.ramp_up_sp = 2000
        #self.m_right.ramp_up_sp = 5000
        self.m_left.run_direct()
        self.m_right.run_direct()

    def line_follower(self):
        while not (self.cs_left.value() < COLOR_THRESHOLD and self.cs_right.value() < COLOR_THRESHOLD):
            #print("CSL",self.cs_left.value())
            #print("CSR",self.cs_right.value())
            if self.cs_left.value() < COLOR_THRESHOLD: #== BLACK:
                self.set_speed(self.m_right,ADJUST_SPEED)
            elif self.cs_right.value() < COLOR_THRESHOLD: #== BLACK:
                self.set_speed(self.m_left, ADJUST_SPEED)
            else:
                self.set_speed(self.m_left, CRUISE_SPEED)
                self.set_speed(self.m_right, CRUISE_SPEED)

    def check_next(self, current_move, next_move):
        if current_move != next_move:
            self.IS_PUSHING = False
            self.move_backward()
        else:
            self.IS_PUSHING = True

    def move_forward(self):
        self.set_speed(self.m_left,CRUISE_SPEED,FORWARD)
        self.set_speed(self.m_right,CRUISE_SPEED,FORWARD)
        # TODO use sensor to detect line of next position
        self.line_follower()
        sleep(0.1)
        self.park()

    def move_backward(self):
        self.set_speed(self.m_left,CRUISE_SPEED,REVERSE)
        self.set_speed(self.m_right,CRUISE_SPEED,REVERSE)
        # TODO use sensor to detect line of next position
        sleep(3)
        self.park()

    def park(self):
        self.set_speed(self.m_right,STOP_SPEED)
        self.set_speed(self.m_left,STOP_SPEED)
        sleep(0.1)

    def set_speed(self,moter,speed,dir=FORWARD):
        moter.duty_cycle_sp = dir * speed

    def turn_right(self):
        self.set_speed(self.m_left,TURN_SPEED,FORWARD)
        self.set_speed(self.m_right,TURN_SPEED,REVERSE)
        # TODO maybe change to check for lines
        while not self.cs_right.value() < COLOR_THRESHOLD:
            pass
        #sleep(TURN_TIME)
        self.park()

    def turn_left(self):
        self.set_speed(self.m_left, TURN_SPEED, REVERSE)
        self.set_speed(self.m_right, TURN_SPEED, FORWARD)
        # TODO maybe change to check for lines
        while not self.cs_left.value() < COLOR_THRESHOLD:
            pass
        #sleep(TURN_TIME)
        self.park()

    def turn_around(self):
        self.set_speed(self.m_left, TURN_SPEED, REVERSE)
        self.set_speed(self.m_right, TURN_SPEED, FORWARD)
        rotations = 0
        while rotations < 2:
            if self.cs_left.value() < COLOR_THRESHOLD:
                rotations += 1
                sleep(0.5)

        self.park()

        #self.turn_left()
        #self.turn_left()

    def set_orientation(self, ori):
        ori_index = ORI2INDEX[ori]
        turn = self.current_orientation - ori_index

        if turn == -1 or turn == 3:
            self.turn_right()
        elif turn == 1 or turn == -3:
            self.turn_left()
        elif turn == -2 or turn == 2:
            self.turn_around()

        self.current_orientation = ori_index

    def execute(self, solution):
        for i, move in enumerate(solution):
            print(INDEX2ORI[self.current_orientation], move)
            if move != END:
                self.set_orientation(move)
                if move.islower():
                    self.move_forward()
                else:
                    self.move_forward() if self.IS_PUSHING else self.move_forward(); self.move_forward()
                    self.check_next(move, solution[i+1])
            else:
                self.park()

solution = "uudd" + END
eve = EV3(DOWN,solution)
