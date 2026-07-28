import base64
import select
import socket
import socketserver
import threading

from config import PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS


class _Server(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


class _Forwarder(socketserver.BaseRequestHandler):
    def handle(self):
        up = None
        try:
            self.request.settimeout(30)
            data = b""
            while b"\r\n\r\n" not in data and len(data) < 65536:
                chunk = self.request.recv(4096)
                if not chunk:
                    return
                data += chunk
            up = socket.create_connection((self.server.host, self.server.port), timeout=30)
            head, _, body = data.partition(b"\r\n\r\n")
            lines = [l for l in head.split(b"\r\n") if not l.lower().startswith(b"proxy-authorization:")]
            lines.insert(1, self.server.auth)
            up.sendall(b"\r\n".join(lines) + b"\r\n\r\n" + body)
            socks = [self.request, up]
            for s in socks:
                s.setblocking(False)
            while True:
                r, _, e = select.select(socks, [], socks, 60)
                if e or not r:
                    return
                for s in r:
                    d = s.recv(65536)
                    if not d:
                        return
                    (up if s is self.request else self.request).sendall(d)
        except Exception:
            pass
        finally:
            if up:
                up.close()


def start_proxy():
    tok = base64.b64encode(f"{PROXY_USER}:{PROXY_PASS}".encode()).decode()
    srv = _Server(("127.0.0.1", 0), _Forwarder)
    srv.host, srv.port = PROXY_HOST, PROXY_PORT
    srv.auth = f"Proxy-Authorization: Basic {tok}".encode()
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv
