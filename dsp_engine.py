import math
import numpy as np


class DSPEngine:

    def __init__(self):

        pass

    # ==========================================
    # Distance
    # ==========================================

    def calculate_distance(

        self,

        listener_position,

        source_position,

    ):

        listener_x, listener_y = listener_position

        source_x, source_y = source_position

        distance = math.hypot(

            source_x - listener_x,

            source_y - listener_y,

        )

        return distance

    # ==========================================
    # Distance Attenuation
    # ==========================================

    def calculate_gain(

        self,

        distance,

    ):

        gain = 1.0 / (

            1.0 + 0.02 * distance

        )

        gain = max(

            gain,

            0.05,

        )

        return gain

    # ==========================================
    # Stereo Pan
    # ==========================================

    def calculate_pan(

        self,

        listener_position,

        source_position,

        map_width,

    ):

        listener_x, _ = listener_position

        source_x, _ = source_position

        dx = source_x - listener_x

        pan = dx / (

            map_width / 2

        )

        pan = max(

            -1.0,

            min(

                1.0,

                pan,

            ),

        )

        return pan

    # ==========================================
    # Equal Power Panning
    # ==========================================

    def apply_panning(

        self,

        mono_audio,

        pan,

    ):

        angle = (

            pan + 1.0

        ) * math.pi / 4.0

        left_gain = math.cos(

            angle

        )

        right_gain = math.sin(

            angle

        )

        left_channel = (

            mono_audio * left_gain

        )

        right_channel = (

            mono_audio * right_gain

        )

        stereo_audio = np.hstack(

            (

                left_channel,

                right_channel,

            )

        )

        return stereo_audio

    # ==========================================
    # DSP Pipeline
    # ==========================================

    def process(

        self,

        audio_buffer,

        listener_position,

        source_position,

        map_width,

    ):

        distance = self.calculate_distance(

            listener_position,

            source_position,

        )

        gain = self.calculate_gain(

            distance

        )

        attenuated_audio = (

            audio_buffer * gain

        )

        pan = self.calculate_pan(

            listener_position,

            source_position,

            map_width,

        )

        stereo_audio = self.apply_panning(

            attenuated_audio,

            pan,

        )

        return stereo_audio