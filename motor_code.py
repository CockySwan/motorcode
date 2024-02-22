import time, signal, os, json
import RPi.GPIO as GPIO
from DRV8825 import DRV8825
from pynput import keyboard
from picamera import PiCamera
from PIL import Image, UnidentifiedImageError

def main():
    film_motor = DRV8825(step_angle=1.8 ,dir_pin=13, step_pin=19, enable_pin=12, mode_pins=(16, 17, 20))
    takeup_motor = DRV8825(step_angle=1.8 ,dir_pin=24, step_pin=18, enable_pin=4, mode_pins=(21, 22, 27))

    # Setup with camera controls
    film_motor.SetMicroStep('softward','fullstep')
    takeup_motor.SetMicroStep('softward', 'fullstep')
    
    # Tweaking motor delay
    film_motor.delay = 1/1300

    try:
        reverse(film_motor)
        settings = user_settings()
        user_interface(film_motor=film_motor, takeup_motor=takeup_motor, settings=settings)
    except Exception as e:
        GPIO.cleanup()
        print("\nMotor stop")
        print(f"Error {e}")
        film_motor.Stop()
        takeup_motor.Stop()
        exit()
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("\nMotor stop")
        film_motor.Stop()
        takeup_motor.Stop()
        exit()

def reverse(film_motor, folder=None):
    want_to_reverse = 'not y, n, or empty'
    while not want_to_reverse.lower() in ('y', 'n', ''):
        want_to_reverse = input("Do you want to reverse [y/n] (Default 'n'): ")
    
    if want_to_reverse.lower() in ('n', ''):
        pass
    elif want_to_reverse.lower() == 'y':
        if folder == None:
            folder_or_framecount = input("Type in folder name or frame count:")
        else:
            folder_or_framecount = folder
        
        if not folder_or_framecount.isnumeric():
            folder_or_framecount = folder_to_index(folder_or_framecount) + 100

        dir = 'backward'
        print(f"Reverse Film by {folder_or_framecount} frames")
        film_motor.TurnFrames(dir, int(folder_or_framecount))
        film_motor.Stop()

def folder_to_index(folder):
    if not os.path.isdir(folder):
        settings = user_settings(just_folder=True)
        settings['subfolder'] = folder

    settings = refresh_movie_folder(settings)

    print(settings['movie_folder'])

    if os.path.isdir(settings['movie_folder']):
        dir = os.listdir(settings['movie_folder'])
        nums = sorted([ int(num.split('.')[0]) for num in dir]) #split the names and sort numbers
        if len(nums) > 0:
            index = nums[-1]
        else:
            index = 0

    return index

def user_settings(settings_file='./settings.json', just_folder=False):
    settings = {}
    if not os.path.isfile(settings_file):
        settings["folder"] = input("(Default:Current Directory) Root Folder: ") or os.getcwd()
        if not just_folder:
            settings["file_extension"] = input("(Default:\".png\") File Extension: ") or '.png'
        with open(settings_file, 'w') as file:
            json.dump(settings, file)
    else:
        with open(settings_file, 'r') as file:
            settings = json.load(file)

    settings['subfolder'] = 'Subfolder'
    settings['movie_folder'] = f"{settings['folder']}/{settings['subfolder']}"
    
    if not just_folder:
        settings['subfolder'] = input("(Default: \"Movie1\")") or "Movie1"
        settings['film_type'] = input("Super 8? [y/n] (Default: n)").lower() or 'n'
        settings['film_length'] = input("What is your reel length in ft? (Default: 50)") or 50
        settings['film_length'] = int(settings['film_length'])
    
    settings = refresh_movie_folder(settings)
    
    if not just_folder:
        not_empty = bool(not len(os.listdir(settings['movie_folder'])) == 0)
        if os.path.isdir(settings['movie_folder']) and not_empty:
            dir = os.listdir(settings['movie_folder'])
            nums = sorted([ int(num.split('.')[0]) for num in dir]) #split the names and sort numbers
            if len(nums) > 0:
                settings['latest_pic'] = nums[-1]
            
            # final_output = [ str(i)+".png" for i in nums] #append file extension and create another list.
            # print(final_output)
        else:
            if not_empty:
                os.makedirs(settings['movie_folder'])


        valid = True
        try:
            image_path = f'{settings["movie_folder"]}/{settings["latest_pic"]}{settings["file_extension"]}'
            with Image.open(image_path, 'r') as im:
                im.verify()            
        except:
            valid = False

        if valid and settings['latest_pic'] > 0:
            settings['latest_pic'] += 1
        else:
            settings['latest_pic'] = 0

        print(valid, settings['latest_pic'])

        if settings['film_type'] == 'n':
            settings['frames'] = settings['film_length'] * 80
        elif settings['film_type'] == 'y': 
            settings['frames'] = settings['film_length'] * 72
        else:
            print('Wrong film type')
            Exception()
        
        # settings['frames'] = int(frames * .99)


    return settings

def refresh_movie_folder(settings):
    settings['movie_folder'] = f"{settings['folder']}/{settings['subfolder']}"
    return settings

def user_interface(film_motor, takeup_motor, settings):

    #Starting Camera     
    mode = 0
    camera = PiCamera()
    camera.resolution = (4056, 3040)
    camera.start_preview()
    camera.rotation = 180
    # camera.zoom = (0.4, 0.3, 0.7, 0.7)
    # settings['index'] = -1

    # if 'latest_pic' in settings:
    #     image_path = f'{settings["movie_folder"]}/{settings["latest_pic"]}{settings["file_extension"]}'
    #     valid = True
    #     try:
    #         with Image.open(image_path, 'r') as im:
    #             im.verify()            
    #     except:
    #         valid = False

    #     if valid:
    #         settings['latest_pic'] += 1

    #     settings['index'] = settings['latest_pic']

        # print(valid, settings['latest_pic'])

    with keyboard.Events() as events:
        for event in events:
            if 'Press' in str(event):
                if event.key == keyboard.Key.esc:
                    mode += 1
                    if mode == 3:
                        break
                else:
                    print(f"Mode: {mode}")
                    if event.key == keyboard.KeyCode().from_char('w'):
                        dir = 'forward'
                        move_motors(film_motor, takeup_motor, dir, mode)
        
                    if event.key == keyboard.KeyCode().from_char('s'):
                        dir = 'backward'
                        move_motors(film_motor, takeup_motor, dir, mode)

                    if event.key == keyboard.KeyCode().from_char('c'):
                        if mode >= 1:
                            # Camera warm-up time
                            # settings['image'] = f'{settings["movie_folder"]}/{settings["index"]}{settings["file_extension"]}'
                            # settings['settings['index']'] = settings['index']
                            settings = new_index(settings)
                            take_picture(film_motor, takeup_motor, camera, settings)

                            # Take a picture then next frame
                            # Move take up motor
                            # Update frame counter


                    # Press enter to get to next mode
                    # Mode 0 - Moving film forward to get first frame
                    # Mode 1 - Taking pictures and moving frame manually
                    # Mode 2 - Automatic picture taking
                    # Mode 3 - Reverse both motors to start
                            
                    print('Receivedevent {}'.format(event))
    
    # if settings['film_type'] == 'n':
    #     frames = settings['film_length'] * 80
    # elif settings['film_type'] == 'y': 
    #     frames = settings['film_length'] * 72
    # else:
    #     print('Wrong film type')
    #     Exception()
    
    frames = int(settings['frames'] * .99)

    try:
        while True:
            if frames == settings['latest_pic']:
                break
            settings = new_index(settings)
            take_picture(film_motor, takeup_motor, camera, settings)

        with keyboard.Events() as events:
            for event in events:
                if 'Press' in str(event):
                    if event.key == keyboard.Key.esc:
                        break
                    if event.key == keyboard.KeyCode().from_char('c'):
                        settings = new_index(settings)
                        take_picture(film_motor, takeup_motor, camera, settings)
                    if event.key == keyboard.KeyCode().from_char('s'):
                        dir = 'backward'
                        move_motors(film_motor, takeup_motor, dir, mode=1)

            reverse(film_motor, settings['movie_folder'])
    except KeyboardInterrupt:
        film_motor.Stop()
        takeup_motor.Stop() 
        
                

def move_motors(film_motor, takeup_motor, dir, mode):
    if mode == 0:      
        film_motor.TurnFrames(dir, 15)                         
    elif mode == 1:
        film_motor.TurnFrames(dir, 1)
    elif mode == 2:
        film_motor.TurnStep(dir, 1)


def take_picture(film_motor, takeup_motor, camera, settings):
    print(settings['image'])

    dir = 'forward'
    camera.exposure_mode = 'off'
    # camera.awb_mode = 'off'
    g = camera.awb_gains
    camera.awb_mode = 'off'
    camera.awb_gains = g
    # camera.shutter_speed = camera.exposure_speed

    camera.ISO = 100
    time.sleep(2)
    camera.capture(settings['image'])
    print("Moving frames!") 
    film_motor.TurnFrames(dir, 1)
    film_motor.Stop() 
    
    takeup_steps = 4
    if settings['film_type'] == 'y': 
        takeup_steps += 1
    takeup_motor.TurnStep(dir, takeup_steps)
    takeup_motor.Stop() 

    # return settings['index'] + 1

def new_index(settings):
    settings['image'] = f'{settings["movie_folder"]}/{"{:05d}".format(settings["latest_pic"])}{settings["file_extension"]}'
    settings['latest_pic'] += 1

    return settings
    
if __name__ == "__main__":
    main()
