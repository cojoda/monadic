import pyaudio
import wave



def play_audio(filename='data/audio/recording/input.wav'):
    wf = wave.open(filename, 'rb')
    silence_chunk = b'\x00' * 1024 * wf.getsampwidth() * wf.getnchannels()
    p  = pyaudio.PyAudio()

    stream = p.open(format  =p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate    =wf.getframerate(),
                    output  =True)

    # Prime the output buffer with a short silence to avoid start‑clicks
    stream.write(silence_chunk)

    data = wf.readframes(1024)
    while data:
        stream.write(data)
        data = wf.readframes(1024)

    # Flush with a short silence to avoid end‑clicks
    stream.write(silence_chunk)

    stream.stop_stream()
    stream.close()
    p.terminate()
