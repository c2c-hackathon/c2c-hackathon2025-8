import logging
import queue
import threading
import time
import typing
import random
from time import sleep as wait
from dataclasses import dataclass

import library
from matrix_button_led_controller import MatrixButtonLEDController

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)
USE_LED_HAT = True

@dataclass
class ButtonInfo:
    color: str
    sound: str
    matched: bool
    index: int



class Game:
    def __init__(self, button_pad: MatrixButtonLEDController):
        self.button_pad = button_pad
        self.button_pad.assign_button_events(self.when_pressed, self.when_held, self.when_released)
        self.buttons: typing.List[ButtonInfo] = []
        self.sounds: typing.List[str] = []
        self.colors: typing.List[str] = []
        self.speaker = library.speaker.Speaker()
        self.initialize_button_pad()
        self.started = False
        self.play_game = True
        self.queue = queue.Queue()
        self.active = 0
        self.selected = None
        self.attempts = 0

    @property
    def correct_sound(self):
        """The sound that is played when player gets a pair"""
        # OPTIONAL: change this to a different sound if you want
        return "correct_answer"

    @property
    def incorrect_sound(self):
        """The sound that is played when player makes an incorrect guess"""
        # OPTIONAL: change this to a different sound if you want
        return "incorrect"

    @property
    def end_of_game_sound(self):
        """The sound that is played when the game ends."""
        # OPTIONAL: change this to a different sound if you want
        return "end_of_game"

    def add_black_queue(self, button_number, selected_number):
        # Function to black out lights
        def add_to_queue():
            print("New Queue Created:","\n", button_number, selected_number)

            wait(.8)
            # Add a delay before hiding incorrect answers

            # Queue the first button to be deleted
            button = self.button_pad.get_button(button_number + 1)
            self.button_pad.set_button_led_color(button, "black")

            # Queue the second button to be deleted
            button = self.button_pad.get_button(selected_number + 1)
            self.button_pad.set_button_led_color(button, "black")
                

        new_thread = threading.Thread(target=add_to_queue)
        new_thread.start()

    def _background_logic_checker(self):
        while self.play_game:

            time.sleep(0.005)  # Prevents busy-waiting
            if self.queue.empty():
                continue
            button_number = self.queue.get()
            print(f"Handling button {button_number}")
            

            # Example logic: light up the button that was pressed with a constant color
            button = self.button_pad.get_button(button_number + 1)
            
            # Check for color existence in self.buttons
            try:
                color = self.buttons[button_number].color
            except:
                color = "red"

            # Getting the button color 
            self.button_pad.set_button_led_color(button, color)

            # Get previously selected button
            selected_button_data = self.buttons[self.selected - 1] if self.selected else None
            print("Self Selected: ", selected_button_data)

            # Logic to either keep color active, hide color
            

            if self.active > 1 and selected_button_data and selected_button_data.matched:
                self.selected = None
                self.active = 0
            elif self.active > 1 and selected_button_data and not selected_button_data.matched:
                self.add_black_queue(button_number, selected_button_data.index)
                self.active = 0
                self.selected = None

            self.speaker.play_preloaded_wav("bloop_x", wait_until_done=True)  # Play a sound when button is pressed
            # TODO: check your game state, and update things

    def when_pressed(self, button):
        # TODO: this is called when a button is pressed. Add what you need to here
        _logger.info(f"Button {button.pin.info.number} pressed")
        self.queue.put(button.pin.info.number - 1)
        button_data = self.buttons[button.pin.info.number - 1]
        
        print("New Selected Data: " + button_data.color)
        self.active += 1

        if self.selected != None:
            
            
            print(self.attempts)
            selected_button_data = self.buttons[self.selected - 1]
            print("Selected Data:" + selected_button_data.color)

            # If Button Is the Same
            if button.pin.info.number == self.selected:
                return

            self.attempts += 1
            # if Matched
            if button_data.color == selected_button_data.color:
                selected_button_data.matched = True
                self.speaker.play_preloaded_wav(self.correct_sound, wait_until_done=True)
            else:
                selected_button_data.matched = False
                
                self.speaker.play_preloaded_wav(self.incorrect_sound, wait_until_done=True) 

        else:
            self.selected = button.pin.info.number
           
    def when_held(self, button):
        # TODO: this is called when a button is held. Add what you need to here
        button_num = button.pin.info.number - 1
        print(str(button_num) + " Button Held")
        if button_num == 0:
            self.selected = None
            self.initialize_button_pad()
        elif button_num == 1:
            for button_data in self.buttons:
                button_data.matched = True
                # TODO: Set Colors
        

    def when_released(self, button):
        # TODO: this is called when a button is released. Add what you need to here
        pass
    
    def generate_colors(self, colors):
        color_dictionary = {}

        initial_nums = list(range(16)) # Numbers 1-16 on the button pad
        initial_colors = colors

        for i in range(8):
            # Get random choices from the initial lists
            random_color = random.choice(initial_colors)

            num1 = random.choice(initial_nums)
            initial_nums.remove(num1) # Remove number so random choice won't pick again

            num2 = random.choice(initial_nums)
            initial_nums.remove(num2) # Remove number so random choice won't pick again
            
            initial_colors.remove(random_color)

            color_dictionary.update({num1: random_color, num2: random_color})

        return color_dictionary
    
    def generate_sounds(self, sounds):
        sounds_dictionary = {}

        initial_nums = list(range(16)) # Numbers 1-16 on the button pad
        initial_sounds = sounds

        for i in range(8):
            # Get random choices from the initial lists
            random_sound = random.choice(initial_sounds)

            num1 = random.choice(initial_nums)
            initial_nums.remove(num1) # Remove number so random choice won't pick again

            num2 = random.choice(initial_nums)
            initial_nums.remove(num2) # Remove number so random choice won't pick again
            
            initial_sounds.remove(random_sound) 

            sounds_dictionary.update({num1: random_sound, num2: random_sound})

        return sounds_dictionary


            
    def initialize_button_pad(self):
        self.button_pad.clear_button_pad()
        # TODO: Set all buttons to a color, List of colors to choose from: https://github.com/waveform80/colorzero/blob/master/colorzero/tables.py#L315
        # sounds are available in the sounds directory
        self.sounds = [
            "thunder2",
            "fart_z",
            "baby_x",
            "slide_whistle_x",
            "arrow2",
            "phone_pay",
            "bloop_x",
            "car_horn_x",
        ]

        self.colors = [
            "chartreuse", 
            "aqua", 
            "red", 
            "gold", 
            "orangered", 
            "purple", 
            "pink", 
            "blue"
        ]

        color_list = self.generate_colors(self.colors)
        sound_list = self.generate_sounds(self.sounds) 
        
        new_buttons = []

        for i in range(16):
            color = color_list[i]
            sound = sound_list[i]
            index = i
            matched = False
            
            button_info = ButtonInfo(color, sound, matched, index)

            new_buttons.append(button_info)
        
        self.buttons = new_buttons


        # TODO: assign to buttons

    def _start_game(self):
        self.thread = threading.Thread(target=self._background_logic_checker)
        self.thread.start()
        # TODO: play a sound to start the game
        self.started = True

    def play(self):
        self._start_game()
        try:
            input("Press Enter to exit the game...")
        except KeyboardInterrupt:
            print("Exiting game...")
        finally:
            self.play_game = False
            self.thread.join()
            self.button_pad.cleanup()


def _main():
    button_pad = MatrixButtonLEDController(
        scan_delay=0.020, pwm_freq=10000, display_pause=0.001, use_led_hat=USE_LED_HAT
    )
    game = Game(button_pad)
    game.play()


if __name__ == "__main__":
    _main()
