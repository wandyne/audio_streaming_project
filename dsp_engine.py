import math
import numpy as np


class DSPEngine:

    def __init__(self):
        self.previous_gain = 1.0
        self.previous_pan = 0.0
        self.filter_state = 0.0

        # ITD parameters
        self.sample_rate = 44100
        self.head_radius = 0.0875
        self.speed_of_sound = 343.0

    # ==========================================
    # Distance
    # ==========================================

    def calculate_distance(self, listener_position, source_position):
        lx, ly = listener_position
        sx, sy = source_position
        return math.hypot(sx - lx, sy - ly)

    # ==========================================
    # Distance Attenuation
    # ==========================================

    def calculate_gain(self, distance):
        gain = 1.0 / (1.0 + 0.02 * distance)
        return max(gain, 0.05)

    # ==========================================
    # Air Absorption
    # ==========================================

    def apply_air_absorption(self, audio, distance):
        gamma = 0.01
        alpha = 1.0 - 1.0 / (1.0 + gamma * distance)

        output = np.zeros_like(audio)

        for i in range(len(audio)):
            self.filter_state = (
                (1.0 - alpha) * audio[i]
                + alpha * self.filter_state
            )
            output[i] = self.filter_state

        return output

    # ==========================================
    # Gain Interpolation
    # ==========================================

    def apply_gain_interpolation(self, audio, target_gain):
        gain_curve = np.linspace(
            self.previous_gain,
            target_gain,
            len(audio),
        )

        output = audio * gain_curve.reshape(-1, 1)

        self.previous_gain = target_gain

        return output

    # ==========================================
    # Pan
    # ==========================================

    def calculate_pan(
        self,
        listener_position,
        source_position,
        map_width,
    ):
        listener_x, _ = listener_position
        source_x, _ = source_position

        pan = (source_x - listener_x) / (map_width / 2)

        return max(
            -1.0,
            min(1.0, pan),
        )

    # ==========================================
    # ITD (Woodworth Model)
    # ==========================================

    def calculate_itd(self, pan):

        theta = pan * (np.pi / 2)

        itd = (
            self.head_radius
            * (theta + np.sin(theta))
            / self.speed_of_sound
        )

        return itd

    def apply_itd(
        self,
        left,
        right,
        pan,
    ):
        itd = self.calculate_itd(pan)

        delay_samples = int(
            round(
                abs(itd)
                * self.sample_rate
            )
        )

        if delay_samples <= 0:
            return left, right

        if delay_samples >= len(left):
            return left, right

        if pan < 0:

            right = np.concatenate(
                (
                    np.zeros(
                        delay_samples,
                        dtype=np.float32,
                    ),
                    right[:-delay_samples],
                )
            )

        elif pan > 0:

            left = np.concatenate(
                (
                    np.zeros(
                        delay_samples,
                        dtype=np.float32,
                    ),
                    left[:-delay_samples],
                )
            )

        return left, right

    # ==========================================
    # ILD (Equal Power Panning)
    # ==========================================

    def apply_panning(
        self,
        mono_audio,
        target_pan,
    ):
        pan_curve = np.linspace(
            self.previous_pan,
            target_pan,
            len(mono_audio),
        )

        angle = (pan_curve + 1.0) * np.pi / 4.0

        left_gain = np.cos(angle)
        right_gain = np.sin(angle)

        left = mono_audio[:, 0] * left_gain
        right = mono_audio[:, 0] * right_gain

        # Apply ITD
        left, right = self.apply_itd(
            left,
            right,
            target_pan,
        )

        self.previous_pan = target_pan

        return np.column_stack(
            (
                left,
                right,
            )
        )

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
            distance,
        )

        filtered_audio = self.apply_air_absorption(
            audio_buffer,
            distance,
        )

        attenuated_audio = self.apply_gain_interpolation(
            filtered_audio,
            gain,
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

        return stereo_audio.astype(np.float32)