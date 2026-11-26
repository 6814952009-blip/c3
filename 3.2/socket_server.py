import os
import socketserver

MAX_MESSAGE_BYTES = 4096


class MessageHandler(socketserver.StreamRequestHandler):
    def handle(self):
        request = self.rfile.readline(MAX_MESSAGE_BYTES + 2)
        if not request.endswith(b"\n") or len(request) > MAX_MESSAGE_BYTES + 1:
            self.wfile.write(b"ERROR: invalid message\n")
            return

        try:
            message = request[:-1].decode("utf-8")
        except UnicodeDecodeError:
            self.wfile.write(b"ERROR: message must be UTF-8\n")
            return

        response = f"Socket server received: {message}\n"
        self.wfile.write(response.encode("utf-8"))


class ThreadedTCPServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    host = os.environ.get("SOCKET_HOST", "0.0.0.0")
    port = int(os.environ.get("SOCKET_PORT", "9000"))
    with ThreadedTCPServer((host, port), MessageHandler) as server:
        print(f"Socket server listening on {host}:{port}", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
