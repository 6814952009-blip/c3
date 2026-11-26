import os
import socket

from flask import Flask, render_template, request

app = Flask(__name__)

SOCKET_HOST = os.environ.get("SOCKET_HOST", "127.0.0.1")
SOCKET_PORT = int(os.environ.get("SOCKET_PORT", "9000"))
SOCKET_TIMEOUT = float(os.environ.get("SOCKET_TIMEOUT", "5"))
MAX_MESSAGE_BYTES = 4096
MAX_RESPONSE_BYTES = MAX_MESSAGE_BYTES + 128


def read_socket_response(connection):
    response = bytearray()
    while len(response) <= MAX_RESPONSE_BYTES:
        chunk = connection.recv(min(1024, MAX_RESPONSE_BYTES + 1 - len(response)))
        if not chunk:
            break
        if b"\n" in chunk:
            response.extend(chunk.split(b"\n", 1)[0])
            return response.decode("utf-8")
        response.extend(chunk)
    raise ValueError("The socket server returned an invalid response.")


def send_to_socket_server(message):
    with socket.create_connection(
        (SOCKET_HOST, SOCKET_PORT), timeout=SOCKET_TIMEOUT
    ) as connection:
        connection.settimeout(SOCKET_TIMEOUT)
        connection.sendall(message.encode("utf-8") + b"\n")
        return read_socket_response(connection)


@app.route("/", methods=["GET", "POST"])
def index():
    message = ""
    result = None
    error = None
    status = 200

    if request.method == "POST":
        message = request.form.get("message", "").strip()
        message_bytes = message.encode("utf-8")

        if not message:
            error = "Please enter a message."
            status = 400
        elif len(message_bytes) > MAX_MESSAGE_BYTES:
            error = f"Message must be {MAX_MESSAGE_BYTES} bytes or fewer."
            status = 400
        elif "\n" in message or "\r" in message:
            error = "Messages must fit on a single line."
            status = 400
        else:
            try:
                result = send_to_socket_server(message)
            except (OSError, UnicodeDecodeError, ValueError):
                app.logger.exception("Unable to get a valid response from socket server")
                error = "The message service is temporarily unavailable. Please try again."
                status = 502

    return render_template(
        "index.html", message=message, result=result, error=error
    ), status


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
