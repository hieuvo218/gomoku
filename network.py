# network.py
import socket
import threading
import json

class NetworkGame:
    def __init__(self, is_host=False, host_ip="127.0.0.1", port=5050):
        self.is_host = is_host
        self.host_ip = host_ip
        self.port = port
        self.conn = None
        self.addr = None
        self.running = True
        self.listener_thread = None
        self.callback = None  # Called when move is received

    def start(self):
        if self.is_host:
            self._start_server()
        else:
            self._start_client()

    def _start_server(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.host_ip, self.port))
        s.listen(1)
        print(f"[SERVER] Waiting for connection on {self.host_ip}:{self.port} ...")
        self.conn, self.addr = s.accept()
        print("[SERVER] Connected to", self.addr)
        self.listener_thread = threading.Thread(target=self._listen, daemon=True)
        self.listener_thread.start()

    def _start_client(self):
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"[CLIENT] Connecting to {self.host_ip}:{self.port} ...")
        self.conn.connect((self.host_ip, self.port))
        print("[CLIENT] Connected to host.")
        self.listener_thread = threading.Thread(target=self._listen, daemon=True)
        self.listener_thread.start()

    def send_move(self, x, y):
        """Send move to opponent."""
        if self.conn:
            try:
                msg = json.dumps({"x": x, "y": y}).encode()
                self.conn.sendall(msg + b"\n")
            except Exception as e:
                print("[NETWORK ERROR]", e)

    def _listen(self):
        """Continuously listen for incoming moves."""
        buffer = ""
        while self.running:
            try:
                data = self.conn.recv(1024)
                if not data:
                    break
                buffer += data.decode()
                while "\n" in buffer:
                    msg, buffer = buffer.split("\n", 1)
                    move = json.loads(msg)
                    if self.callback:
                        self.callback(move)
            except Exception as e:
                print("[LISTEN ERROR]", e)
                break

    def close(self):
        self.running = False
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
