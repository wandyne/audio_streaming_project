# Realtime Spatial Audio Streaming System using Python for Multiplayer Blind-Seek Games

## Overview

This project implements a real-time spatial audio streaming system built entirely from classical Digital Signal Processing (DSP) techniques in Python.

The system was developed as a Digital Signal Processing course project at the School of Electrical and Electronic Engineering (SEEE), Hanoi University of Science and Technology (HUST).

The goal is to demonstrate that fundamental spatial audio cues can be synthesized efficiently without relying on heavy AI models, HRTFs, or commercial audio engines.

The project integrates the DSP engine into a multiplayer "Blind Goat Hunt" game where:

* The Hunter relies primarily on spatial audio cues.
* The Goat streams live microphone audio.
* Audio is transmitted using UDP.
* Spatialization is performed locally on the receiving client.

---

## Main Features

### Real-Time Audio Streaming

* Live microphone capture
* UDP audio transmission
* Low-latency audio playback
* Voice Activity Detection (VAD)

### Spatial Audio DSP

The DSP engine implements:

* Interaural Time Difference (ITD)
* Interaural Level Difference (ILD)
* Distance Attenuation
* Air Absorption Filtering
* Parameter Interpolation Smoothing
* Fractional Delay Processing

### Networking

Dual-channel UDP architecture:

1. Game State Channel

   * JSON packets
   * Player positions
   * Events and game state

2. Audio Channel

   * Raw float32 PCM frames
   * Direct client-to-client audio transport

### Gameplay

Blind Goat Hunt:

* Hunter is visually restricted
* Goat streams live voice
* Hunter locates Goat using spatial audio
* Asymmetric balancing:

  * Goat speed = 1/3 Hunter speed

---

## System Architecture

Microphone (Goat)

↓

Audio Capture

↓

Voice Activity Detection (VAD)

↓

UDP Audio Transmission

↓

Jitter Buffer

↓

Distance Attenuation

↓

Air Absorption Filter

↓

Parameter Interpolation

↓

ITD + ILD Spatializer

↓

Stereo Playback (Hunter)

---

## DSP Pipeline

### 1. Jitter Buffer

Incoming UDP packets are buffered to absorb network jitter and maintain stable playback.

### 2. Distance Attenuation

Volume decreases as distance increases:

A(d) = 1 / (1 + k*d)

### 3. Air Absorption

A first-order low-pass filter simulates the natural attenuation of high-frequency components over distance.

### 4. Parameter Interpolation

Gain, panning coefficients, and delay parameters are smoothly interpolated between frames to eliminate audible clicks.

### 5. Spatialization

The mono microphone signal is converted into stereo using:

* ITD (Interaural Time Difference)
* ILD (Interaural Level Difference)

---

## Project Structure

```text
server.py              # Game server

client.py              # Main game client

voice_engine.py        # Audio pipeline manager

audio_capture.py       # Microphone capture

audio_network.py       # UDP audio transport

audio_playback.py      # Audio playback

dsp_engine.py          # Spatial audio DSP engine

network.py             # JSON game networking

game_objects.py        # Map and gameplay objects

menu.py                # Startup menu

settings.py            # Game configuration

config.py              # Audio configuration
```

## Requirements

Python 3.10+

Install dependencies:

```bash
pip install -r requirements.txt
```

Recommended packages:

```bash
pip install numpy scipy sounddevice pygame-ce
```

## Running the Project

### Start the Server

```bash
python server.py --host 0.0.0.0 --port 5000
```

### Start Hunter Client

```bash
python client.py
```

Choose:

* Role: Hunter
* Server IP

### Start Goat Client

```bash
python client.py
```

Choose:

* Role: Goat
* Server IP

---

## Audio Configuration

Default configuration:

```python
SAMPLE_RATE = 44100
BLOCK_SIZE = 512
INPUT_CHANNELS = 1
OUTPUT_CHANNELS = 2
MIC_THRESHOLD = 0.02
```

Configuration file:

```text
config.py
```

---

## Experimental Results

The system was evaluated under a Local Area Network (LAN) environment.

Reported results:

| Buffer Size  | End-to-End Latency |
| ------------ | ------------------ |
| 256 Samples  | 25–30 ms           |
| 1024 Samples | >85 ms             |

The project report identifies 256 samples as the optimal trade-off between latency and stability.

---

## Current Limitations

* Single audio source
* Fixed jitter buffer depth
* UDP packet loss not corrected
* LAN deployment only
* No NAT traversal support

---

## Future Work

* Multi-user audio mixing
* Adaptive jitter buffering
* Internet deployment (STUN/TURN)
* Additional spatial audio effects
* Performance optimization

---

## Authors

Team 03

* Tran Diep Linh
* Le Cong Hai Quan
* Nguyen Phuong Anh
* Pham Thi Thuy Hang
* Nguyen Phuong Trang

School of Electrical and Electronic Engineering (SEEE)

Hanoi University of Science and Technology (HUST)

---

## License

Educational and research purposes only.