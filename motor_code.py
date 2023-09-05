import RPi.GPIO as GPIO
import time, signal
from DRV8825 import DRV8825
from pynput import keyboard
from picamera import PiCamera

def on_press(key):
    try:
        print('alphanumeric key {0} pressed'.format(key.char))
        if key.char == 'w':
            print("Going Forward")
    except AttributeError:
        print('special key {0} pressed'.format(key))
        

def on_release(key):
    print('{0} released'.format(key))
    if key == keyboard.Key.enter:
        # Stop listener
        return False

# Collect events until released
#with keyboard.Listener(
#        on_press=on_press,
#        on_release=on_release) as listener:
#            listener.join()

# ...or, in a non-blocking fashion:
#listener = keyboard.Listener(
#    on_press=on_press,
#    on_release=on_release)
#listener.start()

def main():
    Motor1 = DRV8825(step_angle=1.8 ,dir_pin=13, step_pin=19, enable_pin=12, mode_pins=(16, 17, 20))
    Motor2 = DRV8825(step_angle=1.8 ,dir_pin=24, step_pin=18, enable_pin=4, mode_pins=(21, 22, 27))
    
    try:
        user_interface(Motor1, Motor2)
    except Exception as e:
        GPIO.cleanup()
        print("\nMotor stop")
        print(f"Error {e}")
        Motor1.Stop()
        Motor2.Stop()
        exit()
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("\nMotor stop")
        Motor1.Stop()
        Motor2.Stop()
        exit()

def user_interface(film_motor, takeup_motor):
    # Setup with camera controls
    film_motor.SetMicroStep('softward','1/4step')
    
    # film_motor.TurnStep(Dir='forward', degrees=360)

          
    mode = 0
    camera = PiCamera()
    camera.resolution = (4056, 3040)
    camera.start_preview()
    index = 0
    with keyboard.Events() as events:
        for event in events:
            if event.key == keyboard.Key.esc:
                mode += 1
            else:
                print(f"Mode: {mode}")
                if event.key == keyboard.KeyCode().from_char('w'):
                    if mode == 0:      
                        print("Moving frames!") 
                        film_motor.TurnFrames('forward', 1)                         
                    elif mode == 2:
                        film_motor.LoopSetup('forward')
                        move_motor_contiuously(film_motor)  
    
                if event.key == keyboard.KeyCode().from_char('s'):
                    if mode == 0:
                        pass
                    elif mode == 2:
                        dir = 'backward'
                        film_motor.LoopSetup(dir)
                        move_motor_contiuously(film_motor, dir)  
                        #if 'Released' in event
                            #Stop Motor
                        #Run motor backward
                        
                if event.key == keyboard.KeyCode().from_char('c'):
                    if mode == 2:
                        # Camera warm-up time
                        time.sleep(2)
                        camera.capture(f'foo{index}.png')
                        index += 1

                        print("Moving frames!") 
                        film_motor.TurnFrames('forward', 1)
                        film_motor.Stop()                         
                  

                        # Take a picture then next frame
                        # Move take up motor
                        # Update frame counter

                # Press enter to get to next mode
                # Mode 0 - Moving film forward to get first frame
                # Mode 2 - Taking pictures and moving frame manually
                # Mode 4 - Automatic picture taking
                # Mode 6 - Reverse both motors to start

                        
                print('Receivedevent {}'.format(event))
                
                
def move_motor_contiuously(motor, dir='forward'):
    motor.LoopSetup(dir)
    motor.digital_write(motor.step_pin, True)
    time.sleep(motor.delay)
    motor.digital_write(motor.step_pin, False)
                
def setup_motors():
    try:
       Motor1 = DRV8825(step_angle=1.8 ,dir_pin=13, step_pin=19, enable_pin=12, mode_pins=(16, 17, 20))
       Motor2 = DRV8825(step_angle=1.8 ,dir_pin=24, step_pin=18, enable_pin=4, mode_pins=(21, 22, 27))
        
       return (Motor1, Motor2) 
       """
        # 1.8 degree: nema23, nema14
        # softward Control :
        # 'fullstep': A cycle = 200 steps
        # 'halfstep': A cycle = 200 * 2 steps
        # '1/4step': A cycle = 200 * 4 steps
        # '1/8step': A cycle = 200 * 8 steps
        # '1/16step': A cycle = 200 * 16 steps
        # '1/32step': A cycle = 200 * 32 steps
       """
#        Motor1.SetMicroStep('softward','1/4step')
#        Motor1.TurnStep(Dir='forward', degrees=1944)
#        time.sleep(0.5)
#        Motor1.TurnStep(Dir='backward', degrees=1944)
#        Motor1.Stop()
#         
#        Motor2.SetMicroStep('softward','1/4step')
#        Motor2.TurnStep(Dir='forward', degrees=2)
#        time.sleep(0.5)
#        Motor2.TurnStep(Dir='backward', degrees=2)
#        Motor2.Stop()
        
    except:
        GPIO.cleanup()
        print("\nMotor stop")
        Motor1.Stop()
        Motor2.Stop()
        exit()
        
    
if __name__ == "__main__":
    main()