from monadic import config

import os
import sys

from monadic import session_manager
from monadic.audio import audio_recorder, audio_player
from monadic.interactions import transcriptions, speech



logger = config.logging.getLogger(__name__)



def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')



def delete_lines(n):
    for _ in range(n):
        sys.stdout.write('\033[F\033[2K')
        sys.stdout.flush()

    
def skip_lines(n):
    print('', end=('\n'*n))




def print_color(text:str, color):
    print(f'{color}{text}\033[0m')



def get_input():

    # input
    print('Press Enter to start recording or type a question:')
    skip_lines(1)
    print(f'{config.YEL}', end='')
    text = input()
    print(f'{config.CLR}', end='')

    # command keywords
    if text in ['audit', 'clear', 'exit']: return text
    
    if text == '':
        return text
    else:
        # LLM query
        delete_lines(3)
        skip_lines(2)
        print_color(text, config.YEL)
        skip_lines(2)

    return text



# Load script from command line args supplied filename
def get_dialogue():
    try:
        file = open(sys.argv[1], 'r', encoding='utf-8')
        script = file.read().splitlines()
        file.close()
        return script
    except:
        return False
    

def get_monologue():
    try:
        file = open(sys.argv[2], 'r', encoding='utf-8')
        script = file.read()
        file.close()
        return script
    except:
        return False



# Start audio recording for transcription
def transcribe():
    recording = audio_recorder.Record()
    delete_lines(2)
    text = transcriptions(recording.output_file).text
    return text


def tts(text):
    speech(text)
    audio_player.play_audio()


# Toggle debug logging (off by default)
def toggle_audit():
    if config.logging.getLogger().getEffectiveLevel() == config.logging.WARNING:
        config.logging.getLogger().setLevel(config.logging.INFO)
        logger.info(f'{config.MON}Audit logging enabled{config.CLR}')
    else:
        logger.info(f'{config.MON}Audit logging disabled{config.CLR}')
        config.logging.getLogger().setLevel(config.logging.WARNING)



def start():
    session = session_manager.Session()
    speak = False

    # CLI arg supplied input file?
    dialogue = get_dialogue() if len(sys.argv) == 2 else False
    monologue = get_monologue() if len(sys.argv) == 3  and sys.argv[1] == '-m' else False
    

    while True:
        print('--------------------------------------------------------------------')

        # input source
        if dialogue:
            text = dialogue.pop(0)
            skip_lines(2)
            print_color(text, config.YEL)
            skip_lines(2)
        elif monologue:
            text = monologue
            skip_lines(2)
            print_color(text, config.YEL)
            skip_lines(2)
        else:
            text = get_input()
        
        # command handling
        if text == '':
            # transcribe audio
            delete_lines(3)
            skip_lines(2)
            text = transcribe() # keep here to ensure transcribe can only be called from manual input and NEVER file script!
            print_color(text, config.YEL)
            skip_lines(2)
            speak = True
        if text == 'audit':
            delete_lines(3)
            skip_lines(2)
            print(f'{text}')
            skip_lines(2)
            toggle_audit()
            continue
        elif text in ('clear'):
            session = session_manager.Session()
            clear_screen()
            continue
        elif text == 'exit':
            return
            
        # Querry LLM
        response = session.respond(text)
        skip_lines(1)
        print_color(response, config.BLU)
        skip_lines(2)

        if speak is True:
            tts(response)
            speak = False

        if monologue:
            return


if __name__ == '__main__':
    start()
