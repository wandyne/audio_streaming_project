import numpy as np

from audio_capture import AudioCapture
from audio_playback import AudioPlayback
from audio_network import AudioNetwork
from dsp_engine import DSPEngine

from config import (
    BLOCK_SIZE,
    INPUT_CHANNELS,
    MIC_THRESHOLD,
    MAP_WIDTH,
)


class VoiceEngine:

    def __init__(
        self,
        local_ip,
        local_port,
        remote_ip,
        remote_port,
    ):

        self.capture = AudioCapture()

        self.playback = AudioPlayback()

        self.network = AudioNetwork(
            local_ip=local_ip,
            local_port=local_port,
            remote_ip=remote_ip,
            remote_port=remote_port,
        )

        self.dsp = DSPEngine()

        self.last_volume = 0.0

    # -----------------------------------

    def start(self):

        self.capture.start()

        self.playback.start()

    # -----------------------------------

    def stop(self):

        self.capture.stop()

        self.playback.stop()

    # -----------------------------------

    def calculate_volume(
        self,
        audio_buffer,
    ):

        rms = np.sqrt(
            np.mean(
                audio_buffer ** 2
            )
        )

        return float(rms)

    # -----------------------------------

    def capture_frame(self):

        return self.capture.read()

    # -----------------------------------

    def send_voice(self):

        frame = self.capture_frame()

        volume = self.calculate_volume(
            frame
        )

        self.last_volume = volume

        making_noise = (
            volume >= MIC_THRESHOLD
        )

        # Chỉ gửi khi có tiếng nói
        if making_noise:

            self.network.send_audio(
                frame
            )

        return making_noise

    # -----------------------------------

    def receive_voice(
        self,
        listener_position,
        source_position,
    ):

        frame = self.network.receive_audio(

            block_size=BLOCK_SIZE,

            channels=INPUT_CHANNELS,

        )

        if frame is None:

            return

        processed = self.dsp.process(

            audio_buffer=frame,

            listener_position=listener_position,

            source_position=source_position,

            map_width=MAP_WIDTH,

        )

        self.playback.play(

            processed

        )

    # -----------------------------------

    def update(
        self,
        listener_position,
        source_position,
    ):

        making_noise = self.send_voice()

        self.receive_voice(

            listener_position,

            source_position,

        )

        return making_noise

    # -----------------------------------

    def get_current_volume(self):

        return self.last_volume