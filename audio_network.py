import socket
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

    # ======================================

    # Send Audio

    # ======================================

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

    # ======================================

    # Receive Audio

    # ======================================

    def receive_audio(

        self,

        block_size,

        channels,

    ):

        try:

            data, _ = self.sock.recvfrom(

                65536

            )

        except BlockingIOError:

            return None

        except OSError:

            return None

        audio = np.frombuffer(

            data,

            dtype=np.float32,

        )

        audio = audio.reshape(

            (

                block_size,

                channels,

            )

        )

        return audio