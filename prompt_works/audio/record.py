import pyaudio
import wave
from threading import Thread

from ..config import RecordConfig




class Record:

    def __init__(self):
        self.config = RecordConfig
        self.recording = False
        self.frames = []
        self.output_file = self.config.filename
        thread = Thread(target = self.keyboard)
        thread.start()
        self.listen()
        thread.join()
        self.save()


    def listen(self):
        self.recording = True
        audio = pyaudio.PyAudio()
        stream = audio.open(format=self.config.format,
                            channels=self.config.channels,
                            rate=self.config.rate,
                            input=True,
                            frames_per_buffer=self.config.chunk)
        print('Recording... Press Enter to stop.')
        while self.recording:
            data = stream.read(self.config.chunk)
            self.frames.append(data)
        stream.stop_stream()
        stream.close()
        audio.terminate()


    def keyboard(self):
        input()
        self.recording = False


    def save(self):
        wf = wave.open(self.output_file, 'wb')
        wf.setnchannels(self.config.channels)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(self.config.format))
        wf.setframerate(self.config.rate)
        wf.writeframes(b''.join(self.frames))
