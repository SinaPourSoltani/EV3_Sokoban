#!/usr/bin/python
import ev3dev.ev3 as ev3
import signal
from time import sleep

# defines
STOP_SPEED = 0
CRUISE_SPEED = 60
ADJUST_SPEED = 100
TURN_SPEED = 50

# directions
FORWARD = 1
REVERSE = -1

# orientations
LEFT = 0
UP = 1
RIGHT = 2
DOWN = 3

class EV3:
    def __init__(self,start_orientation):
        self.current_orientation = start_orientation

        self.m_left = ''
        self.m_right = ''
        self.setup_IO()

        signal.signal(signal.SIGINT, self.signal_handler)

    def signal_handler(sig, frame):
        print('Shutting down gracefully')
        self.m_left.duty_cycle_sp = 0
        self.m_right.duty_cycle_sp = 0
        exit(0)

    def setup_IO(self):
        self.m_left = ev3.LargeMotor('outA')
        self.m_right = ev3.LargeMotor('outD')
        self.m_right.polarity = "normal"
        self.m_left.polarity = "normal"
        self.m_right.duty_cycle_sp = STOP_SPEED
        self.m_left.duty_cycle_sp = STOP_SPEED
        self.m_left.run_direct()
        self.m_right.run_direct()

    def move_forward(self):
        self.set_speed(self.m_left,CRUISE_SPEED,FORWARD)
        self.set_speed(self.m_right,CRUISE_SPEED,FORWARD)
        # TODO use sensor to detect line of next position
        sleep(3)
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

    def set_speed(self,moter,speed,dir=FORWARD):
        moter.duty_cycle_sp = dir * speed

    def turn_right(self):
        self.set_speed(self.m_left,TURN_SPEED,FORWARD)
        self.set_speed(self.m_right,TURN_SPEED,REVERSE)
        # TODO maybe change to check for lines
        sleep(0.65)
        self.park()

    def turn_left(self):
        self.set_speed(self.m_left, TURN_SPEED, REVERSE)
        self.set_speed(self.m_right, TURN_SPEED, FORWARD)
        # TODO maybe change to check for lines
        sleep(0.65)
        self.park()

eve = EV3(LEFT)
eve.move_forward()
sleep(1)
