import socket
import threading
import mysql.connector

class BattleShipServer:
    def __init__(self, host, port):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)
        self.clients = {}
        self.players = []
        self.turn = 0

        self.db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="n0m3l0",
            database="battle_naval",
            port='3308'
        )

    def handle_client(self, client_socket, addr):
        print(f"Connection from {addr}")
        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                if message.startswith("LOGIN"):
                    username, password = message.split()[1:]
                    if self.login(username, password):
                        self.clients[client_socket] = username
                        client_socket.send(f"LOGIN_SUCCESS {username}".encode('utf-8'))
                        self.players.append(client_socket)
                        if len(self.players) == 2:
                            self.start_game()
                    else:
                        client_socket.send("LOGIN_FAILED".encode('utf-8'))
                elif message.startswith("SHIP_POSITIONS"):
                    self.handle_ship_positions(client_socket, message)
                elif message.startswith("ATTACK"):
                    self.handle_attack(client_socket, message)
            except Exception as e:
                print(f"Error handling client {addr}: {e}")
                break
        client_socket.close()

    def login(self, username, password):
        cursor = self.db.cursor()
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        result = cursor.fetchone()
        return result is not None

    def start_game(self):
        self.turn = 0
        for i, client in enumerate(self.players):
            client.send(f"START_GAME {self.clients[self.players[1-i]]} {'YOUR_TURN' if i == 0 else 'OPPONENT_TURN'}".encode('utf-8'))

    def handle_ship_positions(self, client_socket, message):
        # Procesar la posición de los barcos
        pass

    def handle_attack(self, client_socket, message):
        _, x, y = message.split()
        x, y = int(x), int(y)
        opponent = self.players[1 - self.players.index(client_socket)]
        opponent.send(f"ATTACK_NOTIFICATION {x} {y}".encode('utf-8'))
        # Aquí se debería determinar si fue un HIT o MISS y notificar a ambos jugadores
        result = "HIT" if (x + y) % 2 == 0 else "MISS"
        client_socket.send(f"ATTACK_RESULT {x} {y} {result}".encode('utf-8'))
        self.turn = 1 - self.turn
        for client in self.players:
            client.send(f"UPDATE_TURN {'YOUR_TURN' if client == self.players[self.turn] else 'OPPONENT_TURN'}".encode('utf-8'))

    def run(self):
        print("Server started...")
        while True:
            client_socket, addr = self.server_socket.accept()
            client_handler = threading.Thread(target=self.handle_client, args=(client_socket, addr))
            client_handler.start()

if __name__ == "__main__":
    server = BattleShipServer("127.0.0.1", 5000)
    server.run()
