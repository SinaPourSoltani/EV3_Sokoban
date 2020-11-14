#!/usr/bin/python
import ev3dev.ev3 as ev3
import signal
import math
import time
from time import sleep

# defines
STOP_SPEED = 0
MAX_SPEED = 1050
CALIBRATION_SPEED = 50
CRUISE_SPEED = 400
ADJUST_SPEED = CRUISE_SPEED * 1.5
TURN_SPEED = 500

WHEEL_DIAMETER = 0.08
WHEEL_CIRCUMFERENCE = WHEEL_DIAMETER * math.pi
INTERWHEEL_DISTANCE = 0.1565
WHEEL_SENSOR_DISTANCE = 0.062

FIELD_LENGTH = 0.297


ONE_FIELD_ANGLE = 360 * FIELD_LENGTH / WHEEL_CIRCUMFERENCE
ONE_TURN_ANGLE = 360 * (INTERWHEEL_DISTANCE * math.pi / 4) / WHEEL_CIRCUMFERENCE
WHEEL_TO_SENSOR_ANGLE = 360 * WHEEL_SENSOR_DISTANCE / WHEEL_CIRCUMFERENCE
DEPOSIT_ANGLE = 3/5 * ONE_FIELD_ANGLE
CALIBRATION_ANGLE = 2/5 * ONE_FIELD_ANGLE


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


class EV3:
    def __init__(self, start_orientation, solution, with_calibration=False):
        self.current_orientation = start_orientation

        self.m_left = ''
        self.m_right = ''
        self.cs_left = ''
        self.cs_right = ''
        self.setup_IO()
        self.IS_PUSHING = False

        signal.signal(signal.SIGINT, self.signal_handler)
        if with_calibration:
            self.calibrate()
            for i in range(5):
                print("Starting in", 5-i)
                sleep(1)
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

    def calibrate(self):
        csl_values = []
        csr_values = []
        self.set_wheel(self.m_right, CALIBRATION_ANGLE, CALIBRATION_SPEED, REVERSE)
        self.set_wheel(self.m_left, CALIBRATION_ANGLE, CALIBRATION_SPEED, REVERSE)
        while self.m_left.state == ['running']:
            csl_values.append(self.cs_left.value())
            csr_values.append(self.cs_right.value())
        self.set_wheel(self.m_right, CALIBRATION_ANGLE, CALIBRATION_SPEED, FORWARD)
        self.set_wheel(self.m_left, CALIBRATION_ANGLE, CALIBRATION_SPEED, FORWARD)
        while self.m_left.state == ['running']:
            csl_values.append(self.cs_left.value())
            csr_values.append(self.cs_right.value())

        max_val = max(max(csr_values), max(csl_values))
        min_val = min(min(csr_values), min(csl_values))

        print("Initial color threshold",COLOR_THRESHOLD)
        global COLOR_THRESHOLD
        COLOR_THRESHOLD = min_val + (max_val - min_val) / 2

        print("Calibrated color threshold",COLOR_THRESHOLD)
        '''with open('cs_values.txt', 'w') as file:
            file.write("CSR\n")
            file.write("[")
            for v in csr_values:
                file.write(str(v))
                file.write(" ")
            file.write("]")
            file.write("\n")

            file.write("CSL\n")
            file.write("[")
            for v in csl_values:
                file.write(str(v))
                file.write(" ")
            file.write("]")
            file.write("\n")'''

    def wait_while(self):
        self.m_right.wait_while('running')
        self.m_left.wait_while('running')

    def line_follower(self, num_moves, dir=FORWARD):
        '''
        self.set_speed(self.m_left, STOP_SPEED)
        self.set_speed(self.m_right, STOP_SPEED)
        while True:
            print("CSL", self.cs_left.value())
            print("CSR", self.cs_right.value())
        '''
        fields_moved = 0
        while fields_moved < num_moves:
            sleep(0.1)
            while not (self.cs_left.value() < COLOR_THRESHOLD and self.cs_right.value() < COLOR_THRESHOLD):
                if self.cs_left.value() < COLOR_THRESHOLD:
                    self.m_right.run_forever(speed_sp=dir*ADJUST_SPEED)
                elif self.cs_right.value() < COLOR_THRESHOLD:
                    self.m_left.run_forever(speed_sp=dir*ADJUST_SPEED)
                else:
                    self.m_left.run_forever(speed_sp=dir*CRUISE_SPEED)
                    self.m_right.run_forever(speed_sp=dir*CRUISE_SPEED)
            fields_moved += 1

        self.set_wheel(self.m_right, WHEEL_TO_SENSOR_ANGLE, CRUISE_SPEED, dir)
        self.set_wheel(self.m_left, WHEEL_TO_SENSOR_ANGLE, CRUISE_SPEED, dir)
        self.wait_while()

    def check_next(self, current_move, next_move):
        self.IS_PUSHING = current_move == next_move

    def move_forward(self, num_times=1):
        print("Moving forward x", num_times)
        self.line_follower(num_times, FORWARD)
        self.park()

    def move_backward(self):
        print("Moving backwards.")
        self.line_follower(2, REVERSE)
        self.park()

    def deposit(self):
        self.set_wheel(self.m_right, DEPOSIT_ANGLE, CRUISE_SPEED, FORWARD)
        self.set_wheel(self.m_left, DEPOSIT_ANGLE, CRUISE_SPEED, FORWARD)
        self.wait_while()
        self.set_wheel(self.m_right, DEPOSIT_ANGLE, CRUISE_SPEED, REVERSE)
        self.set_wheel(self.m_left, DEPOSIT_ANGLE, CRUISE_SPEED, REVERSE)
        self.wait_while()
        self.park()

    def park(self):
        print("Parking.")
        self.m_right.stop(stop_action='hold')
        self.m_left.stop(stop_action='hold')

    def set_speed(self,motor,speed,dir=FORWARD):
        motor.duty_cycle_sp = dir * speed

    def set_wheel(self,motor,angle,speed,dir):
        motor.run_to_rel_pos(position_sp=dir*angle, speed_sp=speed, stop_action="hold")

    def turn(self, direction, amount=1):
        print("Turning", INDEX2ORI[direction])
        self.set_wheel(self.m_right, amount * ONE_TURN_ANGLE, TURN_SPEED, FORWARD if direction is LEFT else REVERSE)
        self.set_wheel(self.m_left, amount * ONE_TURN_ANGLE, TURN_SPEED, REVERSE if direction is LEFT else FORWARD)
        self.wait_while()
        self.park()

    def set_orientation(self, ori):
        ori_index = ORI2INDEX[ori]
        print("Setting orientation to", INDEX2ORI[ori_index])
        turn = self.current_orientation - ori_index

        if turn == -1 or turn == 3:
            self.turn(RIGHT)
        elif turn == 1 or turn == -3:
            self.turn(LEFT)
        elif turn == -2 or turn == 2:
            self.turn(LEFT, 2)

        self.current_orientation = ori_index

    def execute(self, solution):
        start = time.time()
        index_of_move = -1
        for i, move in enumerate(solution):
            print("NEW MOVE:",INDEX2ORI[self.current_orientation], move, "-------------------")
            if move != END:
                if i <= index_of_move:
                    continue
                index_of_move = i
                num_consecutive_moves = 1
                while move.lower() == solution[index_of_move + 1].lower():
                    num_consecutive_moves += 1
                    index_of_move += 1

                self.set_orientation(move)
                if num_consecutive_moves > 1:
                    self.move_forward(num_consecutive_moves)
                    if solution[index_of_move].isupper():
                        self.deposit()
                else:
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
        print("Execution time:", time.time() - start)

sltn = "llllUddlluRRRRRdrUUruulldRRlddlluLuulldRurDDullDRdRRRdrUUruurrdLulDulldRddlllluurDldRRRdrUUdlllldlluRRRRRdrU" + END
#sltn = "urrd" + END
eve = EV3(LEFT, sltn, with_calibration=True)

'''
TIMES:
5:25 
5:01 : TURN SPEED 250 -> 500
3:43 : CRUISE SPEED 200 -> 300
3:43 : CONSECUTIVE MOVES
3:04 : WITH CALIBRATION CRUISE SPEED 300 -> 400

'''