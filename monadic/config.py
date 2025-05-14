import logging
import pyaudio
import time

from dataclasses import dataclass



logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)


# ANSI Colors
YEL = '\033[93m'
BLU = '\033[94m'
RED = '\033[31m'
GRN = '\033[32m' 
CYN = '\033[36m'
MAG = '\033[35m'
GRY = '\033[90m' 

# Reset Color
CLR = '\033[0m'

# Client Output Colors
USR = YEL # User Output
MOD = BLU # Main Model Output

# Logging Colors
MON = GRN # monadic core logs
HIS = CYN # monadic.history logs
CON = MAG # monadic.context logs
AUD = GRY # monadic.audio logs
CLI = RED # client.py logs



TIMESTAMP = time.strftime('%Y%m%d-%H%M%S')

@dataclass
class EvalEmbed:
    plot_dir = f'evaluation/results/embeddings/run-{TIMESTAMP}'
    plot_file_prefix = 'tsne'


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
    top_n:    int = 2
    recent_n: int = 2



COMPLETION_MINI    = 'gpt-4.1-mini'
COMPLETION_NANO    = 'gpt-4.1-nano'
COMPLETION_DEFAULT = COMPLETION_MINI
EMBEDDING_DEFAULT  = 'text-embedding-3-small'
TOP_N    = 2
RECENT_N = 3
