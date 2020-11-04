#!/usr/bin/python
import ev3dev.ev3 as ev3
import signal
from time import sleep

# defines
STOP_SPEED = 0
CRUISE_SPEED = 40
ADJUST_SPEED = CRUISE_SPEED * 1.4
TURN_SPEED = 30

END = 'X'

# delays
DELAY_LINE_DETECTED = 0.25
DELAY_PRE_TURN = 0.1
DELAY_POST_TURN = 0.2

# colors
BLACK = 1
WHITE = 0
COLOR_THRESHOLD = 10

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

# TODO Use wheel rotations instead of speed for rotations so that speeds can be increased invariant of delay times

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
        self.m_left.run_direct()
        self.m_right.run_direct()

    def line_follower(self, dir=FORWARD):
        '''
        self.set_speed(self.m_left, STOP_SPEED)
        self.set_speed(self.m_right, STOP_SPEED)
        while True:
            print("CSL", self.cs_left.value())
            print("CSR", self.cs_right.value())
        '''
        while not (self.cs_left.value() < COLOR_THRESHOLD and self.cs_right.value() < COLOR_THRESHOLD):
            if self.cs_left.value() < COLOR_THRESHOLD: #== BLACK:
                self.set_speed(self.m_right,ADJUST_SPEED,dir)
            elif self.cs_right.value() < COLOR_THRESHOLD: #== BLACK:
                self.set_speed(self.m_left, ADJUST_SPEED,dir)
            else:
                self.set_speed(self.m_left, CRUISE_SPEED,dir)
                self.set_speed(self.m_right, CRUISE_SPEED,dir)

    def check_next(self, current_move, next_move):
        self.IS_PUSHING = current_move == next_move

    def move_forward(self):
        print("Moving forward.")
        # TODO use sensor to detect line of next position
        self.line_follower()
        sleep(DELAY_LINE_DETECTED)
        self.park()

    def move_backward(self):
        print("Moving backwards.")
        # TODO use sensor to detect line of next position
        self.line_follower(REVERSE)
        sleep(DELAY_LINE_DETECTED)
        self.line_follower(REVERSE)
        self.park()

    def deposit(self):
        self.move_forward()
        self.move_backward()

    def park(self):
        print("Parking.")
        self.set_speed(self.m_right,STOP_SPEED)
        self.set_speed(self.m_left,STOP_SPEED)
        sleep(0.1)

    def set_speed(self,moter,speed,dir=FORWARD):
        moter.duty_cycle_sp = dir * speed

    def turn_right(self):
        print("Turning right.")
        self.set_speed(self.m_left,TURN_SPEED,FORWARD)
        self.set_speed(self.m_right,TURN_SPEED,REVERSE)
        # TODO maybe change to check for lines
        sleep(DELAY_PRE_TURN)
        while self.cs_right.value() > COLOR_THRESHOLD:
            pass
        sleep(DELAY_POST_TURN)
        self.park()

    def turn_left(self):
        print("Turning left")
        self.set_speed(self.m_left, TURN_SPEED, REVERSE)
        self.set_speed(self.m_right, TURN_SPEED, FORWARD)
        # TODO maybe change to check for lines
        sleep(DELAY_PRE_TURN)
        while self.cs_left.value() > COLOR_THRESHOLD:
            pass
        sleep(DELAY_POST_TURN)
        self.park()

    def turn_around(self):
        print("Turning around.")
        self.set_speed(self.m_left, TURN_SPEED, REVERSE)
        self.set_speed(self.m_right, TURN_SPEED, FORWARD)
        rotations = 0
        while rotations < 2:
            if self.cs_left.value() < COLOR_THRESHOLD:
                rotations += 1
                sleep(DELAY_POST_TURN)

        self.park()

    def set_orientation(self, ori):
        ori_index = ORI2INDEX[ori]
        print("Setting orientation to", INDEX2ORI[ori_index])
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
            print("NEW MOVE:",INDEX2ORI[self.current_orientation], move, "-------------------")
            if move != END:
                self.set_orientation(move)
                if move.islower():
                    self.move_forward()
                else:
                    self.check_next(move, solution[i + 1])
                    if self.IS_PUSHING:
                        self.move_forward()
                    else:
                        self.move_forward()
                        self.deposit()

            else:
                self.park()

#solution = "llllUddlluRRRRRdrUUruulldRRlddlluLuulldRurDDullDRdRRRdrUUruurrdLulDulldRddlllluurDldRRRdrUUdlllldlluRRRRRdrU" + END
solution = "uRRlld"
eve = EV3(DOWN,solution)
