import json
import asyncio
from prompt_toolkit import Application
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.widgets import(
    TextArea,
    Button,
    Frame,
    Label,
    Checkbox
)
from prompt_toolkit.layout.containers import(
    VSplit,
    HSplit,
    HorizontalAlign
)
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from asyncio import get_event_loop

from toggle_button import ToggleButton
from orbitals_ws_server import Orbitals_WS_Server

class OrbitalsTerminal:
    def __init__(self):
        self.owserver = Orbitals_WS_Server(server_out=self.show_message)
        self.init_layout()
       
        self.kb = KeyBindings()
        self.kb.add("tab")(focus_next)
        self.kb.add("s-tab")(focus_previous)
        @self.kb.add('c-q')
        def _(event):
            event.app.exit()
        self.app = Application(layout = self.layout, key_bindings = self.kb, full_screen = True)
        get_event_loop().run_until_complete(self.app.run_async())

    def init_layout(self):
        self.connection_button = ToggleButton(self.toggle_connection)
        self.secure_checkbox = Checkbox(text="Secure  ")
        self.secure_checkbox.checked = False
        self.chain_label = Label(text="Chain:", width=9)
        self.chain_entry = TextArea(text="[path-to]/fullchain.pem", multiline=False, width = 64)
        self.key_label = Label(text="Key:", width=9)
        self.key_entry = TextArea(text="[path-to]/privkey.pem", multiline=False, width = 64)
        self.port_label = Label(text="Port:", width=8)
        self.port_entry = TextArea(text="9000", multiline=False)
        self.secure_container = VSplit([self.secure_checkbox,
            HSplit([
                VSplit([self.chain_label, self.chain_entry]),
                VSplit([self.key_label, self.key_entry])
                ])
            ], align=HorizontalAlign.RIGHT)
        self.port_container = HSplit([
            VSplit([
                self.port_label,
                self.port_entry
                ], align=HorizontalAlign.CENTER, width=36),
                self.connection_button.btn()
            ])
        self.status_textarea = TextArea(focusable=False, multiline=False)
        self.status_container = Frame(title="Status", body=self.status_textarea)
        self.out_message_textarea = TextArea(focusable=True, accept_handler=self.send_message, multiline=False)
        self.out_message_container = Frame(title="Outbound message | Enter to broadcast", body=self.out_message_textarea)
        self.in_messages_textarea = TextArea(focusable=True, scrollbar=True)
        self.in_messages_container = Frame(title="Inbound Messages", body=self.in_messages_textarea)
        self.frame = Frame(title="WebSockets Server Terminal | Tab to focus, Ctrl+q to exit",
            body=HSplit([
                VSplit([
                    Frame(body=self.secure_container),
                    Frame(body=self.port_container)
                    ]),
                self.status_container,
                self.out_message_container,
                self.in_messages_container
            ])
        )
        self.layout = Layout(self.frame, focused_element=self.connection_button.btn())
 
    def toggle_connection(self, start):
        if start:
            self.owserver.setPort(int(self.port_entry.text))
            if self.secure_checkbox.checked:
                get_event_loop().create_task(self.owserver.start_server(
                                            wss=True,
                                            chain=self.chain_entry.text,
                                            key=self.key_entry.text))
            else:
                get_event_loop().create_task(self.owserver.start_server())
        else:
            get_event_loop().create_task(self.owserver.stop_server())

    def send_message(self, buffer_data):
        payload = buffer_data.text
        packet = json.dumps({"type":"broadcast","msg":f"[Server] {payload}"})
        get_event_loop().create_task(self.owserver.broadcast(packet))
        self.show_message({"ev": f"[Server] {payload}"})

    def show_message(self, msg):
        if "msg" in msg:
            self.in_messages_textarea.buffer.insert_text(msg["msg"] + '\n')
        elif "status" in msg:
            self.status_textarea.text = msg["status"]
        elif "ev" in msg:
            self.in_messages_textarea.buffer.insert_text(str(msg["ev"] + '\n'))
    
_ = OrbitalsTerminal()
