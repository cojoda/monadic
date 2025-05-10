import pyaudio

from dataclasses import dataclass



@dataclass
class RecordConfig:
    chunk:    int = 1024
    format:   int = pyaudio.paInt16
    channels: int = 1
    rate:     int = 44100
    filename: str = 'data/audio/recording/output.wav'



@dataclass
class Completion:
    mini:     str = 'gpt-4.1-mini'
    nano:     str = 'gpt-4.1-nano'
    default:  str = mini
    top_n:    int = 3
    recent_n: int = 5


COMPLETION_MINI    = 'gpt-4.1-mini'
COMPLETION_NANO    = 'gpt-4.1-nano'
COMPLETION_DEFAULT = COMPLETION_MINI
EMBEDDING_DEFAULT  = 'text-embedding-3-small'
TOP_N    = 3
RECENT_N = 5
