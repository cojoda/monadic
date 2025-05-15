import pyaudio
import threading
import wave

from monadic import config



class Record:

    def __init__(self):
        self.config      = config.RecordConfig
        self.frames      = []
        self.output_file = self.config.filename
        self.stop_event  = threading.Event()

        listener_thread = threading.Thread(target=self.listen)
        listener_thread.start()

        # Main thread waits for Enter
        input("Recording... Press Enter to stop.\n")
        self.stop_event.set()

        listener_thread.join()
        self.save()


    def listen(self):
        audio = pyaudio.PyAudio()
        stream = audio.open(format           =self.config.format,
                            channels         =self.config.channels,
                            rate             =self.config.rate,
                            input            =True,
                            frames_per_buffer=self.config.chunk)
        
        while not self.stop_event.is_set():
            data = stream.read(self.config.chunk)
            self.frames.append(data)

        stream.stop_stream()
        stream.close()
        audio.terminate()


    def save(self):
        wf = wave.open(self.output_file, 'wb')
        wf.setnchannels(self.config.channels)
        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(self.config.format))
        wf.setframerate(self.config.rate)
        wf.writeframes(b''.join(self.frames))
