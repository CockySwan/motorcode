import time, signal, os, json
import RPi.GPIO as GPIO
from DRV8825 import DRV8825
from pynput import keyboard
from picamera import PiCamera
from PIL import Image, UnidentifiedImageError

def main():
    settings = user_settings()
    Motor1 = DRV8825(step_angle=1.8 ,dir_pin=13, step_pin=19, enable_pin=12, mode_pins=(16, 17, 20))
    Motor2 = DRV8825(step_angle=1.8 ,dir_pin=24, step_pin=18, enable_pin=4, mode_pins=(21, 22, 27))

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
        settings["file_extension"] = input("(Default:\".png\") File Extension: ") or '.png'
        with open(settings_file, 'w') as file:
            json.dump(settings, file)
    else:
        with open(settings_file, 'r') as file:
            settings = json.load(file)
    
    settings['subfolder'] = input("(Default: \"Movie1\")") or "Movie1"
    settings['movie_folder'] = f"{settings['folder']}/{settings['subfolder']}"
    settings['film_type'] = input("Super 8? [y/n] (Default: n)").lower() or 'n'
    settings['film_length'] = input("What is your reel length in ft? (Default: 50)") or 50


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
    film_motor.SetMicroStep('softward','1/4step')
    takeup_motor.SetMicroStep('softward', 'fullstep')
    
    # Tweaking motor delay
    film_motor.delay = 1/1350

          
    mode = 0

    settings['index'] = -1

    if 'latest_pic' in settings:
        image_path = f'{settings["movie_folder"]}/{settings["latest_pic"]}{settings["file_extension"]}'
        valid = True
        try:
            with Image.open(image_path, 'r') as im:
                im.verify()            
        except:
            valid = False

        if valid:
            settings['latest_pic'] += 1

        settings['index'] = settings['latest_pic']

        print(f"Reverse Film by {settings['index']} frames")
        for i in range(settings['index']):
            dir = 'backward'
            # takeup_motor.TurnStep(dir, 4)
            # takeup_motor.Stop() 

            film_motor.TurnFrames(dir, 1)
            film_motor.Stop()

        # print(valid, settings['latest_pic'])

    with keyboard.Events() as events:
        for event in events:
            if 'Press' in str(event):
                if event.key == keyboard.Key.esc:
                        break
                else:
                    if event.key == keyboard.KeyCode().from_char('w'):
                        dir = 'forward'
                        move_motors(film_motor, takeup_motor, dir, 0)
        
                    if event.key == keyboard.KeyCode().from_char('s'):
                        dir = 'backward'
                        move_motors(film_motor, takeup_motor, dir, 0)

  
                    print('Receivedevent {}'.format(event))
      

def move_motors(film_motor, takeup_motor, dir, mode):
    if mode == 0: 
        for i in range(10):     
            takeup_motor.TurnStep(dir, 4)                         
            film_motor.TurnFrames(dir, 1)


    
if __name__ == "__main__":
    main()
