import wave
import io

def create_silent_wav(duration_ms=100):
    """
    Creates a silent mono WAV file in memory.
    Returns a BytesIO object containing the WAV data.
    """
    framerate = 44100
    sample_width = 2  # 16-bit
    num_channels = 1  # mono
    num_frames = int((duration_ms / 1000) * framerate)

    wav_file = io.BytesIO()
    with wave.open(wav_file, 'wb') as w:
        w.setnchannels(num_channels)
        w.setsampwidth(sample_width)
        w.setframerate(framerate)
        w.setnframes(num_frames)
        w.writeframes(b'\x00' * num_frames * sample_width * num_channels)

    wav_file.seek(0)
    return wav_file
