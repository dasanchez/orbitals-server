from prompt_toolkit.widgets import Button

class ToggleButton:
    def __init__(self, clicked_result):
        self.button = Button("Start", handler=self.clicked)
        self.forward = clicked_result
        self.pressed=False
    def clicked(self):
        self.pressed = not self.pressed
        if self.pressed:
            self.button.text = "Stop"
        else:
            self.button.text = "Start"
        self.forward(self.pressed)
    def btn(self):
        return self.button