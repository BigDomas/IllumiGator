import arcade
from menus import draw_title_menu, InGameMenu
from util import util
import Shapes
import numpy

class GameObject(arcade.Window):
    def __init__(self):
        super().__init__(util.WINDOW_WIDTH, util.WINDOW_HEIGHT, util.WINDOW_TITLE)
        self.background = None
        self.set_mouse_visible(False)
        arcade.set_background_color(arcade.color.SKY_BLUE)
        self.elem_list = None
        self.game_menu = None
    
    def setup(self):
        self.game_state = 'menu'
        self.elem_list = [Shapes.Rectangle(numpy.array([2.5, util.WINDOW_HEIGHT // 2]), numpy.array([5, util.WINDOW_HEIGHT]))]
        self.game_menu = InGameMenu(0)

    def on_draw(self):
        self.clear()
        print(self.game_state)

        if self.game_state == 'menu':
            draw_title_menu()
        elif self.game_state == 'game' or self.game_state == 'paused':
            for elem in self.elem_list:
                elem.draw()
            if self.game_state == 'paused':
                self.game_menu.draw()
    
    def on_key_press(self, key, key_modifiers):
        if self.game_state == 'menu':
            if key == arcade.key.ENTER:
                self.game_state = 'game'
            if key == arcade.key.ESCAPE:
                arcade.close_window()

        elif self.game_state == 'game':
            if key == arcade.key.ESCAPE:
                self.game_state = 'paused'

        elif self.game_state == 'paused':
            if key == arcade.key.ESCAPE:
                self.game_state = 'game'
            if key == arcade.key.DOWN:
                self.game_menu.increment_selection()
            if key == arcade.key.UP:
                self.game_menu.decrement_selection()
            if key == arcade.key.ENTER:
                if self.game_menu.selection == 0:
                    self.game_state = 'game'
                elif self.game_menu.selection == 1:
                    self.game_state = 'menu'

def main():
    window = GameObject()
    window.setup()
    arcade.run()

if __name__ == "__main__":
    main()