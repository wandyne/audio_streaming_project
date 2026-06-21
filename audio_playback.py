import sounddevice as sd

from config import (
    SAMPLE_RATE,
    OUTPUT_CHANNELS,
    DTYPE,
)


class AudioPlayback:

    def __init__(self):

        self.stream = sd.OutputStream(

            samplerate=SAMPLE_RATE,

            channels=OUTPUT_CHANNELS,

            dtype=DTYPE,

        )

    def start(self):

        self.stream.start()

    def stop(self):

        self.stream.stop()

        self.stream.close()

    def play(self, audio):

        if audio.ndim != 2:

            raise ValueError(
                "Audio must have shape (N, 2)."
            )

        if audio.shape[1] != OUTPUT_CHANNELS:

            raise ValueError(

                f"Expected {OUTPUT_CHANNELS} channels "

                f"but got {audio.shape[1]}"

            )

        self.stream.write(audio)