import socket
import threading
import mysql.connector

class BattleShipServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)

        self.clients = []
        self.user_data = {}
        self.game_data = {}

        self.db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="n0m3l0",
            database="battle_naval",
            port='3308'
        )

        self.listen_thread = threading.Thread(target=self.listen_for_clients)
        self.listen_thread.start()

    def listen_for_clients(self):
        while True:
            client_socket, addr = self.server_socket.accept()
            self.clients.append(client_socket)
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                self.process_message(client_socket, message)
            except Exception as e:
                print(f"Error receiving message: {e}")
                self.clients.remove(client_socket)
                client_socket.close()
                break

    def process_message(self, client_socket, message):
        if message.startswith("USERNAME"):
            _, username = message.split()
            self.check_username(client_socket, username)
        elif message.startswith("SHIP_POSITIONS"):
            positions = message[len("SHIP_POSITIONS "):]
            self.save_ship_positions(client_socket, positions)
        elif message.startswith("ATTACK"):
            _, x, y = message.split()
            self.handle_attack(client_socket, int(x), int(y))

    def check_username(self, client_socket, username):
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()
        if result:
            client_socket.send("USERNAME_TAKEN".encode('utf-8'))
        else:
            cursor.execute("INSERT INTO users (username) VALUES (%s)", (username,))
            self.db.commit()
            self.user_data[client_socket] = username
            opponent_socket = self.get_opponent_socket(client_socket)
            if opponent_socket:
                self.start_game(client_socket, opponent_socket)
            else:
                client_socket.send(f"USERNAME_SUCCESS {username} waiting".encode('utf-8'))

    def get_opponent_socket(self, client_socket):
        for sock in self.clients:
            if sock != client_socket and sock not in self.user_data:
                return sock
        return None

    def start_game(self, client1, client2):
        self.user_data[client1] = "player1"
        self.user_data[client2] = "player2"
        self.game_data[client1] = {"opponent": client2, "turn": True, "ships": {}, "attacks": {}}
        self.game_data[client2] = {"opponent": client1, "turn": False, "ships": {}, "attacks": {}}
        client1.send(f"START_GAME player2 {True}".encode('utf-8'))
        client2.send(f"START_GAME player1 {False}".encode('utf-8'))

    def save_ship_positions(self, client_socket, positions):
        self.game_data[client_socket]['ships'] = self.parse_positions(positions)
        opponent_socket = self.game_data[client_socket]['opponent']
        if 'ships' in self.game_data[opponent_socket]:
            self.start_turn(client_socket, opponent_socket)

    def parse_positions(self, positions):
        ship_positions = {}
        for part in positions.split(" "):
            ship, *coords = part.split(" ")
            ship_positions[ship] = [(int(coord.split(",")[0]), int(coord.split(",")[1])) for coord in coords]
        return ship_positions

    def handle_attack(self, client_socket, x, y):
        if self.game_data[client_socket]['turn']:
            opponent_socket = self.game_data[client_socket]['opponent']
            if (x, y) not in self.game_data[client_socket]['attacks']:
                self.game_data[client_socket]['attacks'][(x, y)] = True
                result = "MISS"
                for ship, positions in self.game_data[opponent_socket]['ships'].items():
                    if (x, y) in positions:
                        result = "HIT"
                        break
                client_socket.send(f"ATTACK_RESULT {x} {y} {result}".encode('utf-8'))
                opponent_socket.send(f"ATTACK_NOTIFICATION {x} {y} {result}".encode('utf-8'))
                self.switch_turns(client_socket, opponent_socket)

    def switch_turns(self, client_socket, opponent_socket):
        self.game_data[client_socket]['turn'] = False
        self.game_data[opponent_socket]['turn'] = True
        client_socket.send(f"UPDATE_TURN False".encode('utf-8'))
        opponent_socket.send(f"UPDATE_TURN True".encode('utf-8'))

if __name__ == "__main__":
    server = BattleShipServer("127.0.0.1", 12346)
