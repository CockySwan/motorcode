import RPi.GPIO as GPIO
import time

MotorDir = [
    'forward',
    'backward',
]

ControlMode = [
    'hardward',
    'softward',
]

class DRV8825():
    def __init__(self, step_angle ,dir_pin, step_pin, enable_pin, mode_pins):
        self.dir_pin = dir_pin
        self.step_pin = step_pin        
        self.enable_pin = enable_pin
        self.mode_pins = mode_pins
        self.step_angle = step_angle
        self.steps_per_turn = 360 // step_angle
        self.delay = 1 / self.steps_per_turn
        self.mode = 1

        
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.dir_pin, GPIO.OUT)
        GPIO.setup(self.step_pin, GPIO.OUT)
        GPIO.setup(self.enable_pin, GPIO.OUT)
        GPIO.setup(self.mode_pins, GPIO.OUT)
        
    def degreeToSteps(self, degree):
        # 1 degree to however many steps
        degree_to_step = degree/self.step_angle
        # Added microstepping modifier
        #degree_to_step *= self.mode
        
        return int(round(degree_to_step))
        
    def digital_write(self, pin, value):
        GPIO.output(pin, value)
        
    def Stop(self):
        self.digital_write(self.enable_pin, 0)
    
    def SetMicroStep(self, mode, stepformat):
        """
        (1) mode
            'hardward' :    Use the switch on the module to control the microstep
            'software' :    Use software to control microstep pin levels
                Need to put the All switch to 0
        (2) stepformat
            ('fullstep', 'halfstep', '1/4step', '1/8step', '1/16step', '1/32step')
        """
        microstep = {'fullstep': (0, 0, 0),
                     'halfstep': (1, 0, 0),
                     '1/4step': (0, 1, 0),
                     '1/8step': (1, 1, 0),
                     '1/16step': (0, 0, 1),
                     '1/32step': (1, 0, 1)}

        print("Control mode:",mode)
        if (mode == ControlMode[1]):
            print("set pins")
            step_sel = stepformat.split('step')[0]
            if step_sel == 'full':
                mult = 1
            elif step_sel == 'half':
                mult = 2
            else:
                mult = int(step_sel.split('/')[1])
                
            self.digital_write(self.mode_pins, microstep[stepformat])
            # Microstepping modifiers
            self.delay /= mult
            #self.steps_per_turn *= mult
            self.mode = mult

    def TurnFrames(self, dir, frames):
        # Frames to degrees 
        # 1944 = 1 frame
        self.TurnStep(dir, 745 * frames)
            
    def TurnStep(self, dir, degrees):
        
        self.LoopSetup(dir)

        if (degrees == 0):
            return
        steps = self.degreeToSteps(degrees)
        print("turn step:",steps)
        for i in range(steps):
            self.digital_write(self.step_pin, True)
            time.sleep(self.delay)
            self.digital_write(self.step_pin, False)
            time.sleep(self.delay)
            
    def LoopSetup(self, Dir):
        if (Dir == MotorDir[0]):
            print("forward")
            self.digital_write(self.enable_pin, 1)
            self.digital_write(self.dir_pin, 0)
        elif (Dir == MotorDir[1]):
            print("backward")
            self.digital_write(self.enable_pin, 1)
            self.digital_write(self.dir_pin, 1)
        else:
            print("the dir must be : 'forward' or 'backward'")
            return

