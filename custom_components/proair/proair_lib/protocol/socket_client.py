"""Client TCP socket per comunicazione locale con centralina ProAir."""

import json
import logging
import socket
import time

logger = logging.getLogger(__name__)

BUFFER_SIZE = 1000
CONNECT_TIMEOUT = 1.0       # secondi
READ_TIMEOUT = 1.0           # secondi
RETRY_PAUSE = 0.8            # 800ms tra tentativi di connessione
TIMEOUT_RETRY_PAUSE = 0.5   # 500ms tra tentativi per timeout
MAX_CONNECT_RETRIES = 2
MAX_TIMEOUT_RETRIES = 3


class SocketError(Exception):
    """Errore di comunicazione socket."""
    pass


class SocketClient:
    """Client TCP per comunicazione locale con centralina ProAir."""

    def __init__(self, host: str, port: int = 1235, timeout: float = 3.0):
        self.host = host
        self.port = port
        self.timeout = timeout

    def send_command(self, command_json: str) -> dict:
        """Invia un comando JSON e riceve la risposta.

        Apre una nuova connessione TCP per ogni comando (come fa l'app originale),
        invia il JSON, riceve la risposta, chiude la connessione.
        """
        last_error = None

        for attempt in range(1, MAX_TIMEOUT_RETRIES + 1):
            try:
                result = self._try_send(command_json)
                return result
            except (socket.timeout, TimeoutError) as e:
                last_error = e
                logger.warning(
                    "Timeout (tentativo %d/%d): %s",
                    attempt, MAX_TIMEOUT_RETRIES, e,
                )
                if attempt < MAX_TIMEOUT_RETRIES:
                    time.sleep(TIMEOUT_RETRY_PAUSE)
            except (ConnectionError, OSError) as e:
                last_error = e
                logger.warning(
                    "Errore connessione (tentativo %d/%d): %s",
                    attempt, MAX_TIMEOUT_RETRIES, e,
                )
                if attempt < MAX_TIMEOUT_RETRIES:
                    time.sleep(RETRY_PAUSE)

        raise SocketError(
            f"Comunicazione fallita dopo {MAX_TIMEOUT_RETRIES} tentativi: {last_error}"
        )

    def _try_send(self, command_json: str) -> dict:
        """Singolo tentativo di invio comando e ricezione risposta."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)

        try:
            logger.debug("Connessione a %s:%d ...", self.host, self.port)
            sock.connect((self.host, self.port))

            # Invio comando
            logger.debug("TX: %s", command_json)
            sock.sendall(command_json.encode("utf-8"))

            # Ricezione risposta
            response_data = b""
            while True:
                chunk = sock.recv(BUFFER_SIZE)
                if not chunk:
                    break
                response_data += chunk
                if len(chunk) < BUFFER_SIZE:
                    break
                # Se il buffer è pieno, aspetta 100ms e rilegge
                time.sleep(0.1)

            response_str = response_data.decode("utf-8")
            logger.debug("RX: %s", response_str)

            if not response_str:
                raise SocketError("Risposta vuota dalla centralina")

            return json.loads(response_str)

        finally:
            sock.close()

    def __repr__(self) -> str:
        return f"SocketClient({self.host}:{self.port})"
