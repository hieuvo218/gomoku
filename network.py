# network.py
import socket
import threading
import json
import time

class NetworkGame:
    _connection_lock = threading.Lock()

    def __init__(self, is_host=False, host_ip="127.0.0.1", port=5050):
        self.is_host = is_host
        self.host_ip = str(host_ip).strip()
        self.port = int(port)
        self.conn = None
        self.addr = None
        self.running = True
        self.listener_thread = None
        self.callback = None
        self.name_callback = None
        self.continue_callback = None
        self.disconnect_callback = None  # ✅ NEW: Disconnect callback
        self.is_connected = False
        self.opponent_name = None
        self.listener_ready = False
        
        self._validate_network_params()
    
    def _validate_network_params(self):
        """Validate IP and port before attempting connection."""
        try:
            socket.inet_aton(self.host_ip)
        except socket.error:
            raise ValueError(f"Invalid IP address format: '{self.host_ip}'")
        
        if not (1024 <= self.port <= 65535):
            raise ValueError(f"Port must be between 1024-65535, got {self.port}")
        
        print(f"[NETWORK] Validated - IP: {self.host_ip}, Port: {self.port}")

    def start(self):
        if self.is_host:
            self._start_server()
        else:
            self._start_client()

    def _start_server(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            bind_addr = ('0.0.0.0', self.port)
            s.bind(bind_addr)
            s.listen(1)
            
            print(f"[SERVER] Listening on all interfaces, port {self.port}")
            print(f"[SERVER] Clients should connect to: {self.host_ip}:{self.port}")
            print("[SERVER] Waiting for connection...")
            
            self.conn, self.addr = s.accept()
            self.is_connected = True
            print(f"[SERVER] Connected to {self.addr}")
            
            # ✅ Start listener IMMEDIATELY after accepting connection
            self.listener_thread = threading.Thread(target=self._listen, daemon=True)
            self.listener_thread.start()
            
            # ✅ Give listener a moment to initialize
            time.sleep(0.1)
            
        except OSError as e:
            print(f"[SERVER ERROR] Failed to start server: {e}")
            if hasattr(e, 'winerror') and e.winerror == 10048:
                print(f"[SERVER ERROR] Port {self.port} is already in use!")
            raise
        except Exception as e:
            print(f"[SERVER ERROR] Unexpected error: {e}")
            raise

    def _start_client(self):
        max_retries = 5
        retry_delay = 2
        
        for attempt in range(max_retries):
            sock = None
            try:
                print(f"\n[CLIENT] Attempt {attempt + 1}/{max_retries}")
                
                # Create socket immediately before use
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                print(f"[CLIENT] Socket created: {sock}")
                
                # Set socket options
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                
                # Shorter timeout for faster retries
                sock.settimeout(5)
                
                print(f"[CLIENT] Connecting to {self.host_ip}:{self.port} ...")
                
                # Connect using explicit tuple
                address_tuple = (self.host_ip, self.port)
                print(f"[CLIENT] Address tuple: {address_tuple}, type: {type(address_tuple)}")
                
                sock.connect(address_tuple)
                
                # When connection succeeds:
                sock.settimeout(None)
                self.conn = sock
                self.is_connected = True
                print("[CLIENT] ✓ Connected successfully!")
                
                # ✅ Start listener IMMEDIATELY
                self.listener_thread = threading.Thread(target=self._listen, daemon=True)
                self.listener_thread.start()
                
                # ✅ Give listener a moment to initialize
                time.sleep(0.1)
                return
                
            except socket.timeout:
                print(f"[CLIENT] Connection timeout")
                if sock:
                    try:
                        sock.close()
                    except:
                        pass
                if attempt < max_retries - 1:
                    print(f"[CLIENT] Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    
            except ConnectionRefusedError:
                print(f"[CLIENT] Connection refused - server not running or port blocked")
                if sock:
                    try:
                        sock.close()
                    except:
                        pass
                if attempt < max_retries - 1:
                    print(f"[CLIENT] Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    
            except OSError as e:
                print(f"[CLIENT ERROR] OSError: {e}")
                if hasattr(e, 'winerror'):
                    print(f"[CLIENT ERROR] WinError code: {e.winerror}")
                
                if sock:
                    try:
                        sock.close()
                    except:
                        pass
                
                # WinError 10022 is an invalid argument - don't retry
                if hasattr(e, 'winerror') and e.winerror == 10022:
                    print("\n[CLIENT ERROR] Invalid argument detected!")
                    print("[CLIENT ERROR] This usually means:")
                    print("  1. Firewall/Antivirus blocking the connection")
                    print("  2. Network adapter issue")
                    print("  3. Socket library conflict")
                    print("\n[CLIENT] Trying alternative connection method...")
                    
                    # Try alternative method
                    if self._try_alternative_connect():
                        return
                    break
                    
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    
            except Exception as e:
                print(f"[CLIENT ERROR] Unexpected: {type(e).__name__}: {e}")
                if sock:
                    try:
                        sock.close()
                    except:
                        pass
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        
        self.is_connected = False
        raise ConnectionError(f"Failed to connect to {self.host_ip}:{self.port} after {max_retries} attempts")

    def _try_alternative_connect(self):
        """Alternative connection method using getaddrinfo"""
        try:
            print("[CLIENT] Attempting connection via getaddrinfo...")
            
            # Get address info - this resolves hostname and provides proper socket params
            addr_info = socket.getaddrinfo(
                self.host_ip, 
                self.port, 
                socket.AF_INET,  # IPv4
                socket.SOCK_STREAM  # TCP
            )
            
            print(f"[CLIENT] Address info: {addr_info}")
            
            for af, socktype, proto, canonname, sa in addr_info:
                sock = None
                try:
                    sock = socket.socket(af, socktype, proto)
                    sock.settimeout(5)
                    print(f"[CLIENT] Trying {sa}...")
                    sock.connect(sa)
                    
                    # Success!
                    sock.settimeout(None)
                    self.conn = sock
                    self.is_connected = True
                    print("[CLIENT] ✓ Connected via alternative method!")
                    
                    self.listener_thread = threading.Thread(target=self._listen, daemon=True)
                    self.listener_thread.start()
                    return True
                    
                except Exception as e:
                    print(f"[CLIENT] Failed with {sa}: {e}")
                    if sock:
                        sock.close()
                    continue
            
            return False
            
        except Exception as e:
            print(f"[CLIENT ERROR] Alternative method failed: {e}")
            return False

    def send_move(self, x, y):
        """Send move to opponent."""
        if not self.is_connected:
            print("[NETWORK] Cannot send - not connected")
            return False
            
        if self.conn:
            try:
                msg = json.dumps({"type": "move", "x": x, "y": y}).encode()
                self.conn.sendall(msg + b"\n")
                return True
            except Exception as e:
                print(f"[NETWORK ERROR] Failed to send move: {e}")
                self.is_connected = False
                return False
        return False

    def send_name(self, name):
        """Send player name to opponent."""
        if not self.is_connected:
            print("[NETWORK] Cannot send name - not connected")
            return False
            
        if self.conn:
            try:
                msg = json.dumps({"type": "name", "name": name}).encode()
                self.conn.sendall(msg + b"\n")
                print(f"[NETWORK] Sent name: {name}")
                return True
            except Exception as e:
                print(f"[NETWORK ERROR] Failed to send name: {e}")
                self.is_connected = False
                return False
        return False

    def send_continue(self):
        """Send continue signal to opponent."""
        if not self.is_connected:
            print("[NETWORK] Cannot send continue - not connected")
            return False
            
        if self.conn:
            try:
                msg = json.dumps({"type": "continue"}).encode()
                self.conn.sendall(msg + b"\n")
                print("[NETWORK] Sent continue signal")
                return True
            except Exception as e:
                print(f"[NETWORK ERROR] Failed to send continue: {e}")
                self.is_connected = False
                return False
        return False

    def _listen(self):
        """Continuously listen for incoming messages."""
        print("[NETWORK] Listener thread starting...")
        self.listener_ready = True
        self._peer_ready = False
        print("[NETWORK] ✓ Listener thread ready")
        
        buffer = ""
        while self.running and self.is_connected:
            try:
                data = self.conn.recv(1024)
                if not data:
                    print("[NETWORK] Connection closed by peer")
                    self.is_connected = False  # ✅ Set flag BEFORE callback
                    if self.disconnect_callback:
                        self.disconnect_callback("opponent_disconnected")
                    break
                
                print(f"[NETWORK] Received data: {data[:100]}")
                buffer += data.decode()
                
                while "\n" in buffer:
                    msg, buffer = buffer.split("\n", 1)
                    print(f"[NETWORK] Processing: {msg}")
                    try:
                        data = json.loads(msg)
                        msg_type = data.get("type", "move")
                        print(f"[NETWORK] Message type: {msg_type}")
                        
                        if msg_type == "ready":
                            self._peer_ready = True
                            print("[NETWORK] ✓ Received READY signal from peer")
                        
                        elif msg_type == "name":
                            self.opponent_name = data.get("name", "Opponent")
                            print(f"[NETWORK] ✓ Received opponent name: {self.opponent_name}")
                            if self.name_callback:
                                self.name_callback(self.opponent_name)
                        
                        elif msg_type == "move":
                            if self.callback:
                                self.callback({"x": data["x"], "y": data["y"]})
                        
                        elif msg_type == "continue":
                            print("[NETWORK] ✓ Opponent pressed continue")
                            if self.continue_callback:
                                self.continue_callback()
                        
                        elif msg_type == "disconnect":
                            reason = data.get("reason", "unknown")
                            print(f"[NETWORK] Opponent sent disconnect: {reason}")
                            self.is_connected = False  # ✅ Set flag BEFORE callback
                            if self.disconnect_callback:
                                self.disconnect_callback(reason)
                            return
                        
                    except json.JSONDecodeError as e:
                        print(f"[NETWORK] Invalid JSON: {e}")
                        print(f"[NETWORK] Raw message: {msg}")
                        
            except socket.timeout:
                continue
            except ConnectionResetError:
                print("[NETWORK] Connection reset by peer")
                self.is_connected = False  # ✅ Set flag BEFORE callback
                if self.disconnect_callback:
                    self.disconnect_callback("connection_reset")
                break
            except ConnectionAbortedError:
                print("[NETWORK] Connection aborted")
                self.is_connected = False  # ✅ Set flag BEFORE callback
                if self.disconnect_callback:
                    self.disconnect_callback("connection_aborted")
                break
            except OSError as e:
                # Handle WinError 10054 and similar
                if e.winerror in (10054, 10053, 10038):  # Connection closed errors
                    print(f"[NETWORK] Connection closed (WinError {e.winerror})")
                    self.is_connected = False  # ✅ Set flag BEFORE callback
                    if self.disconnect_callback:
                        self.disconnect_callback("connection_closed")
                    break
                else:
                    print(f"[LISTEN ERROR] OSError: {e}")
                    import traceback
                    traceback.print_exc()
                    self.is_connected = False
                    if self.disconnect_callback:
                        self.disconnect_callback("error")
                    break
            except Exception as e:
                print(f"[LISTEN ERROR] {e}")
                import traceback
                traceback.print_exc()
                self.is_connected = False  # ✅ Set flag BEFORE callback
                if self.disconnect_callback:
                    self.disconnect_callback("error")
                break

        self.is_connected = False
        print("[NETWORK] Listener thread stopped")

    def send_disconnect(self, reason="quit"):
        """Send disconnect notification to opponent."""
        if self.conn and self.is_connected:  # ✅ Check if still connected
            try:
                msg = json.dumps({"type": "disconnect", "reason": reason}).encode()
                self.conn.sendall(msg + b"\n")
                print(f"[NETWORK] Sent disconnect notification: {reason}")
                time.sleep(0.1)  # Give time for message to send
            except Exception as e:
                print(f"[NETWORK] Could not send disconnect (connection already closed): {e}")
        else:
            print("[NETWORK] Skip sending disconnect - already disconnected")

    def close(self):
        """Close the network connection."""
        print("[NETWORK] Closing connection...")
        
        # Only try to send disconnect if we're still connected
        if self.is_connected:
            self.send_disconnect("quit")
        
        self.running = False
        self.is_connected = False
        
        if self.conn:
            try:
                self.conn.shutdown(socket.SHUT_RDWR)
            except Exception as e:
                print(f"[NETWORK] Shutdown error (expected if already closed): {e}")
            try:
                self.conn.close()
            except Exception as e:
                print(f"[NETWORK] Close error: {e}")
        
        if self.listener_thread and self.listener_thread.is_alive():
            self.listener_thread.join(timeout=2)
        
        print("[NETWORK] Connection closed")