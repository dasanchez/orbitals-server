'''
Orbitals interactive server
Starts an instance of the Orbitals server and provides a prompt to access it.
'''

from prompt_toolkit import print_formatted_text as print
from prompt_toolkit import HTML
from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import VSplit, Window, HSplit, WindowAlign
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings
import asyncio
from or_server import OrbitalsServer

buffer1 = Buffer()  # Editable buffer.
kb = KeyBindings()

@kb.add('c-q')
def exit_(event):
    """
    Pressing Ctrl-Q will exit the user interface.

    Setting a return value means: quit the event loop that drives the user
    interface and return this value from the `Application.run()` call.
    """
    event.app.exit()

main_container = Window()

root_container = HSplit([
    # One window that holds the BufferControl with the default buffer on
    # the left.

    Window(content=FormattedTextControl(text='* ORBITALS SERVER *'), height=2, align=WindowAlign.CENTER),
    Window(char='=', height=1),

    # A vertical line in the middle. We explicitly specify the width, to
    # make sure that the layout engine will not try to divide the whole
    # width by three for all these windows. The window will simply fill its
    # content by repeating this character.
    # Window(char='|'),

    # Display the text 'Hello world' on the right.
        Window(content=BufferControl(buffer=buffer1))

])

layout = Layout(root_container)

app = Application(layout=layout, key_bindings=kb, full_screen=True)
app.run()

# print(">>> Orbitals interactive server <<<")
# print(HTML('<b><red bg="ansiwhite">This is red on white</red></b>'))

# server = OrbitalsServer(port=9001, secure=False, verbose=True, test=True)

# loop = asyncio.get_event_loop()
# await server.start_server()
# print("Server started.")
# print("Console mode available:")

# while True:
#     instruction = input("> ")
#     if instruction == 'exit':
#         exit()
#     elif instruction == 'list-players':
#         for player in server.orCluster.getUserNames():
#             print(player)
#     elif instruction == 'list-sectors':
#         for sector in server.orCluster._sectors:
#             print(sector.getSectorDetails())

