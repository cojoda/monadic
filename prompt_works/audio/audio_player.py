import pyaudio
import wave


def play_audio(filename='data/audio/recording/output.wav'):
    wf = wave.open(filename, 'rb')
    p  = pyaudio.PyAudio()

    stream = p.open(format  =p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate    =wf.getframerate(),
                    output  =True)

    data = wf.readframes(1024)
    while data:
        stream.write(data)
        data = wf.readframes(1024)

    stream.stop_stream()
    stream.close()
    p.terminate()


play_audio()
