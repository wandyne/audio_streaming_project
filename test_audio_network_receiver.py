from audio_network import AudioNetwork

from audio_playback import AudioPlayback


speaker = AudioPlayback()

network = AudioNetwork(

    local_ip="127.0.0.1",

    local_port=6001,

    remote_ip="127.0.0.1",

    remote_port=6000,

)

speaker.start()

print("Receiving Audio...")

try:

    while True:

        frame = network.receive_audio(

            block_size=512,

            channels=1,

        )

        if frame is None:

            continue

        stereo = frame.repeat(

            2,

            axis=1,

        )

        speaker.play(

            stereo

        )

except KeyboardInterrupt:

    speaker.stop()