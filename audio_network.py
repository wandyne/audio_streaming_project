import socket
from collections import deque
import numpy as np


class AudioNetwork:

    def __init__(
        self,
        local_ip,
        local_port,
        remote_ip,
        remote_port,
    ):

        self.sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
        )

        self.sock.bind(
            (
                local_ip,
                local_port,
            )
        )

        self.sock.setblocking(False)

        self.remote_address = (
            remote_ip,
            remote_port,
        )

        self.jitter_buffer = deque(maxlen=3)

    def send_audio(
        self,
        audio_buffer,
    ):

        try:

            payload = audio_buffer.astype(
                np.float32
            ).tobytes()

            self.sock.sendto(
                payload,
                self.remote_address,
            )

        except OSError:

            pass

    def receive_audio(
        self,
        block_size,
        channels,
    ):

        while True:

            try:

                data, _ = self.sock.recvfrom(
                    65536
                )

            except BlockingIOError:

                break

            except OSError:

                break

            try:

                audio = np.frombuffer(
                    data,
                    dtype=np.float32,
                )

                expected_samples = (
                    block_size
                    * channels
                )

                if len(audio) != expected_samples:

                    continue

                audio = audio.reshape(
                    (
                        block_size,
                        channels,
                    )
                )

                self.jitter_buffer.append(
                    audio
                )

            except Exception:

                continue

        if len(self.jitter_buffer) < 3:

            return None

        return self.jitter_buffer.popleft()

    def get_jitter_depth(self):

        return len(
            self.jitter_buffer
        )

    def clear_buffer(self):

        self.jitter_buffer.clear()

    def close(self):

        try:

            self.sock.close()

        except OSError:

            pass