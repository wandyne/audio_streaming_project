import sounddevice as sd

from config import (
    SAMPLE_RATE,
    BLOCK_SIZE,
    INPUT_CHANNELS,
    DTYPE,
)


class AudioCapture:

    def __init__(self):

        self.stream = sd.InputStream(

            samplerate=SAMPLE_RATE,

            channels=INPUT_CHANNELS,

            blocksize=BLOCK_SIZE,

            dtype=DTYPE,

        )

    def start(self):

        self.stream.start()

    def stop(self):

        self.stream.stop()

        self.stream.close()

    def read(self):

        audio_buffer, overflow = self.stream.read(
            BLOCK_SIZE
        )

        return audio_buffer.copy()