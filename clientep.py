import socket
import threading
import tkinter as tk
from tkinter import messagebox

class BattleShipClient:
    def __init__(self, host, port):
        self.root = tk.Tk()
        self.root.title("Battleship")

        self.host = host
        self.port = port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.host, self.port))

        self.username = tk.StringVar()
        self.password = tk.StringVar()
        self.opponent = None
        self.turn = None

        self.placing_ships = True
        self.ships_to_place = {"Carrier": 5, "Battleship": 4, "Cruiser": 3, "Submarine": 3, "Destroyer": 2}
        self.current_ship = None
        self.current_ship_length = 0
        self.horizontal = True
        self.ship_positions = {}

        self.setup_gui()
        self.receive_thread = threading.Thread(target=self.receive_messages)
        self.receive_thread.start()
        self.username_label = tk.Label(self.info_frame, textvariable=self.username)
        self.username_label.pack()


    def setup_gui(self):
        self.login_frame = tk.Frame(self.root)
        tk.Label(self.login_frame, text="Username:").grid(row=0, column=0)
        tk.Entry(self.login_frame, textvariable=self.username).grid(row=0, column=1)
        tk.Label(self.login_frame, text="Password:").grid(row=1, column=0)
        tk.Entry(self.login_frame, textvariable=self.password, show="*").grid(row=1, column=1)
        tk.Button(self.login_frame, text="Login", command=self.login).grid(row=2, columnspan=2)
        self.login_frame.pack()

        self.main_frame = tk.Frame(self.root)
        self.board_frame = tk.Frame(self.main_frame)
        self.buttons = [[None for _ in range(10)] for _ in range(10)]
        for i in range(10):
            for j in range(10):
                button = tk.Button(self.board_frame, text="", width=2, height=1, command=lambda x=i, y=j: self.on_board_click(x, y))
                button.grid(row=i, column=j)
                self.buttons[i][j] = button
        self.board_frame.pack(side=tk.LEFT)

        self.info_frame = tk.Frame(self.main_frame)
        self.turn_label = tk.Label(self.info_frame, text="")
        self.turn_label.pack()
        self.info_frame.pack(side=tk.RIGHT)

        self.main_frame.pack()

        self.ship_frame = tk.Frame(self.root)
        self.ship_var = tk.StringVar()
        self.ship_var.set("Select Ship")
        self.ship_menu = tk.OptionMenu(self.ship_frame, self.ship_var, *self.ships_to_place.keys(), command=self.highlight_ship)
        self.ship_menu.pack(side=tk.LEFT)
        self.rotate_button = tk.Button(self.ship_frame, text="Rotate", command=self.rotate_ship)
        self.rotate_button.pack(side=tk.LEFT)
        self.confirm_button = tk.Button(self.ship_frame, text="Confirm Placement", command=self.confirm_placement)
        self.confirm_button.pack(side=tk.LEFT)
        # Añade un botón para eliminar un barco
        self.remove_button = tk.Button(self.ship_frame, text="Eliminar barco", command=self.remove_ship)
        self.remove_button.pack(side=tk.LEFT)
        self.ship_frame.pack()
            
    def highlight_ship(self, value):
        ship = value
        if ship in self.ship_positions:
            # Resalta el barco en el tablero
            for x, y in self.ship_positions[ship]:
                self.buttons[x][y].config(bg="yellow")

    def confirm_placement(self):
        ship = self.ship_var.get()
        if not ship or ship not in self.ships_to_place:
            tk.messagebox.showwarning("Advertencia", "Por favor, selecciona un barco para colocar.")
            return
        if ship in self.ship_positions:
            self.ships_to_place.pop(ship)
            self.current_ship = None
            self.current_ship_length = 0
            self.ship_var.set("Select Ship")
            if not self.ships_to_place:
                self.placing_ships = False
                self.send_positions_to_server()
            # Actualiza las opciones del menú de barcos después de confirmar la colocación
            self.update_ship_menu_options()


    def set_current_ship(self, value):
        self.current_ship = value
        self.current_ship_length = self.ships_to_place[self.current_ship]
        # Inicializa las posiciones del barco actual a una lista vacía
        self.ship_positions[self.current_ship] = []

    def on_board_click(self, x, y):
        if self.placing_ships and self.current_ship:
            if self.horizontal:
                if y + self.current_ship_length <= 10 and all(self.buttons[x][y + i]['bg'] != 'blue' for i in range(self.current_ship_length)):
                    for i in range(self.current_ship_length):
                        self.buttons[x][y + i].config(bg="blue")
                    # Añade las posiciones del barco a self.ship_positions
                    self.ship_positions[self.current_ship].extend([(x, y + i) for i in range(self.current_ship_length)])
            else:
                if x + self.current_ship_length <= 10 and all(self.buttons[x + i][y]['bg'] != 'blue' for i in range(self.current_ship_length)):
                    for i in range(self.current_ship_length):
                        self.buttons[x + i][y].config(bg="blue")
                    # Añade las posiciones del barco a self.ship_positions
                    self.ship_positions[self.current_ship].extend([(x + i, y) for i in range(self.current_ship_length)])


    def update_ship_menu_options(self):
        # Obtiene las opciones actuales del menú
        menu = self.ship_menu['menu']
        menu.delete(0, 'end')
        # Añade los barcos restantes a las opciones del menú
        for ship in self.ships_to_place.keys():
            menu.add_command(label=ship, command=tk._setit(self.ship_var, ship, self.set_current_ship))

    def remove_ship(self):
        ship = self.ship_var.get()
        if ship in self.ship_positions:
            # Elimina el barco del tablero
            for x, y in self.ship_positions[ship]:
                self.buttons[x][y].config(bg="white")
            # Elimina el barco de los barcos colocados
            self.ship_positions.pop(ship)
            # Añade el barco de nuevo a los barcos por colocar
            self.ships_to_place[ship] = len(self.ship_positions[ship])
            # Actualiza las opciones del menú de barcos
            self.update_ship_menu_options()
        else:
            tk.messagebox.showwarning("Advertencia", "Por favor, selecciona un barco para eliminar.")


    def on_board_click(self, x, y):
        if self.placing_ships and self.current_ship:
            if self.horizontal:
                if y + self.current_ship_length <= 10 and all(self.buttons[x][y + i]['bg'] != 'blue' for i in range(self.current_ship_length)):
                    for i in range(self.current_ship_length):
                        self.buttons[x][y + i].config(bg="blue")
                    self.ship_positions[self.current_ship] = [(x, y + i) for i in range(self.current_ship_length)]
            else:
                if x + self.current_ship_length <= 10 and all(self.buttons[x + i][y]['bg'] != 'blue' for i in range(self.current_ship_length)):
                    for i in range(self.current_ship_length):
                        self.buttons[x + i][y].config(bg="blue")
                    self.ship_positions[self.current_ship] = [(x + i, y) for i in range(self.current_ship_length)]



    def rotate_ship(self):
        self.horizontal = not self.horizontal


    def send_positions_to_server(self):
        positions = "SHIP_POSITIONS " + " ".join([f"{ship} {' '.join([f'{x},{y}' for x, y in positions])}" for ship, positions in self.ship_positions.items()])
        self.client_socket.send(positions.encode('utf-8'))

    def login(self):
        self.client_socket.send(f"LOGIN {self.username.get()} {self.password.get()}".encode('utf-8'))

    def receive_messages(self):
        while True:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if message.startswith("LOGIN_SUCCESS"):
                    self.login_frame.pack_forget()
                    self.main_frame.pack()
                    self.ship_frame.pack()
                elif message.startswith("START_GAME"):
                    _, self.opponent, self.turn = message.split()
                    self.update_turn_label()
                elif message.startswith("ATTACK_RESULT"):
                    _, x, y, result = message.split()
                    x, y = int(x), int(y)
                    self.buttons[x][y].config(text=result)
                elif message.startswith("ATTACK_NOTIFICATION"):
                    _, x, y, result = message.split()
                    x, y = int(x), int(y)
                    self.buttons[x][y].config(text=result, bg="red" if result == "HIT" else "white")
                elif message.startswith("UPDATE_TURN"):
                    _, self.turn = message.split()
                    self.update_turn_label()
            except Exception as e:
                print(f"Error receiving message: {e}")
                break

    def update_turn_label(self):
        self.turn_label.config(text=f"Turn: {self.turn}")
        
    def attack(self, x, y):
        self.client_socket.send(f"ATTACK {x} {y}".encode('utf-8'))


    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    client = BattleShipClient("127.0.0.1", 5000)
    client.run()