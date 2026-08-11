# Blocca OGNI connessione di rete in questo processo e nei suoi figli.
import socket
def _no(*a, **k):
    raise OSError("RETE BLOCCATA PER LA PROVA OFFLINE")
socket.socket.connect = lambda self, *a, **k: _no()
socket.socket.connect_ex = lambda self, *a, **k: _no()
socket.create_connection = _no
socket.getaddrinfo = _no
print("[prova offline] rete bloccata a livello di socket", flush=True)
