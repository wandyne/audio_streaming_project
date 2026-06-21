from audio_capture import AudioCapture
from audio_network import AudioNetwork


capture = AudioCapture()

network = AudioNetwork(

    local_ip="127.0.0.1",

    local_port=6000,

    remote_ip="127.0.0.1",

    remote_port=6001,

)

capture.start()

print("Sending Audio...")

try:

    while True:

        frame = capture.read()

        network.send_audio(

            frame

        )

except KeyboardInterrupt:

    capture.stop()