import time, signal, os, json
import RPi.GPIO as GPIO
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
    settings = user_settings()
    Motor1 = DRV8825(step_angle=1.8 ,dir_pin=13, step_pin=19, enable_pin=12, mode_pins=(16, 17, 20))
    Motor2 = DRV8825(step_angle=1.8 ,dir_pin=24, step_pin=18, enable_pin=4, mode_pins=(21, 22, 27))
    # Motor2 = DRV8825(step_angle=1.8 ,dir_pin=24, step_pin=18, enable_pin=4, mode_pins=(21, 22, 27))

    try:
        user_interface(film_motor=Motor1, takeup_motor=Motor2, settings=settings)
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

def user_settings(settings_file='./settings.json'):
    settings = {}
    if not os.path.isfile(settings_file):
        settings["folder"] = input("(Default:Current Directory) Root Folder: ") or os.getcwd()
        with open(settings_file, 'w') as file:
            json.dump(settings, file)
    else:
        with open(settings_file, 'r') as file:
            settings = json.load(file)
    
    settings['subfolder'] = input("(Default: \"Movie1\")") or "Movie1"
    settings['movie_folder'] = f"{settings['folder']}/{settings['subfolder']}"
    settings['film_type'] = input("Super 8? [y/n] (Default: n)").lower() or 'n'
    settings['film_length'] = input("What is your reel length? (Default: 50)") or 50


    if os.path.isdir(settings['movie_folder']):
        dir = os.listdir(settings['movie_folder'])
        nums = sorted([ int(num.split('.')[0]) for num in dir]) #split the names and sort numbers
        settings['latest_pic'] = nums[-1]
        
        # final_output = [ str(i)+".png" for i in nums] #append file extension and create another list.
        # print(final_output)
    else:
        os.makedirs(settings['movie_folder'])


    return settings



def user_interface(film_motor, takeup_motor, settings):
    # Setup with camera controls
    film_motor.SetMicroStep('softward','fullstep')
    takeup_motor.SetMicroStep('softward', 'fullstep')
    
    # film_motor.TurnStep(Dir='forward', degrees=360)

          
    mode = 0
    camera = PiCamera()
    camera.resolution = (4056, 3040)
    camera.start_preview()
    index = 0

    if 'latest_pic' in settings:
        # print(settings['latest_pic'])
        index = settings['latest_pic']

    with keyboard.Events() as events:
        for event in events:
            if event.key == keyboard.Key.esc:
                mode += 1
                if mode == 4:
                    break
            else:
                print(f"Mode: {mode}")
                if event.key == keyboard.KeyCode().from_char('w'):
                    dir = 'forward'
                    if mode == 0:      
                        print("Moving frames!") 
                        film_motor.TurnFrames(dir, 10)                         
                    elif mode == 2:
                        # film_motor.LoopSetup('forward')
                        film_motor.TurnStep(dir, 1)

                        # move_motor_contiuously(film_motor)  
    
                if event.key == keyboard.KeyCode().from_char('s'):
                    dir = 'backward'
                    if mode == 0:
                        film_motor.LoopSetup(dir)
                        film_motor.TurnFrames(dir, 5)
                    elif mode == 2:
                        film_motor.TurnStep(dir, 1)
                        # move_motor_contiuously(film_motor, dir)  

                if event.key == keyboard.KeyCode().from_char('c'):
                    if mode == 2:
                        # Camera warm-up time
                        settings['image'] = f'{settings["movie_folder"]}/{index}.png'

                        take_picture(film_motor, takeup_motor, camera, settings)
                        index += 1

                        # Take a picture then next frame
                        # Move take up motor
                        # Update frame counter

                # Press enter to get to next mode
                # Mode 0 - Moving film forward to get first frame
                # Mode 2 - Taking pictures and moving frame manually
                # Mode 4 - Automatic picture taking
                # Mode 6 - Reverse both motors to start

                        
                print('Receivedevent {}'.format(event))
    
    if settings['film_type'] == 'n':
        frames = settings['film_length'] * 80
    elif settings['film_type'] == 'y': 
        frames = settings['film_length'] * 72
    else:
        print('Wrong film type')
        Exception()

    try:
        while True:
            if frames == index + 6:
                break
            settings['image'] = f'{settings["movie_folder"]}/{index}.png'
            take_picture(film_motor, takeup_motor, camera, settings)
            index += 1

        print(f"Reverse Film by {index} frames")
        for i in range(index):
            takeup_motor.TurnStep('backward', 6)
            takeup_motor.Stop() 

            film_motor.TurnFrames('backward', 1)
            film_motor.Stop()
    except KeyboardInterrupt:
        film_motor.Stop()
        takeup_motor.Stop() 
                



def move_motor_contiuously(motor, dir='forward'):
    motor.LoopSetup(dir)
    motor.digital_write(motor.step_pin, True)
    time.sleep(motor.delay)
    motor.digital_write(motor.step_pin, False)

def take_picture(film_motor, takeup_motor, camera, settings):
    print(settings['image'])

    dir = 'forward'
    camera.exposure_mode = 'off'
    camera.awb_mode = 'auto'
    camera.ISO = 100
    time.sleep(2)
    camera.capture(settings['image'])
    print("Moving frames!") 
    film_motor.delay = 1/800
    film_motor.TurnFrames(dir, 1)
    film_motor.Stop() 

    takeup_motor.TurnStep(dir, 3)
    takeup_motor.Stop() 
                
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