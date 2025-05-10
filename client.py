import logging
import os
import sys

from monadic import interactive_session
from monadic.audio import audio_recorder
from monadic.interactions import transcriptions



logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)



def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')



def delete_lines(n):
    for _ in range(n):
        sys.stdout.write('\033[F\033[2K')
        sys.stdout.flush()



def get_script():
    try:
        file = open(sys.argv[1], 'r', encoding='utf-8')
        script = file.read().splitlines()
        file.close()
        return script
    except:
        return False

YEL = '\033[93m'
BLU = '\033[94m'
CLR = '\033[0m'

def get_input():
    print('Press Enter to start recording or type a question:', end=f'\n\n{YEL}')
    text = input()
    print(f'{CLR}', end='')  # Reset color

    if text == '':
        delete_lines(4)
        print('\n\n', end='')
        recording = audio_recorder.Record()
        delete_lines(2)
        text = transcriptions(recording.output_file).text
        print(f'{YEL}{text}{CLR}\n')
    elif text == 'audit':
        delete_lines(3)
        print(f'\n\n{text}\n\n')
        if logging.getLogger().getEffectiveLevel() == logging.WARNING:
            logging.getLogger().setLevel(logging.DEBUG)
            logger.info("Audit logging enabled")
        else:
            logger.info("Audit logging disabled")
            logging.getLogger().setLevel(logging.WARNING)
        return text
    elif text in ('clear', 'exit'):
        if text == 'clear':
            clear_screen()
        return text
    else:
        delete_lines(3)
        print(f'\n\n{YEL}{text}{CLR}\n')

    return text


def start():
    conversation = interactive_session.Interact()
    script = get_script() if len(sys.argv) > 1 else False

    while True:
        print('--------------------------------------------------------------------')

        if not script:
            text = get_input()
            if text in ('audit', 'clear'):
                if text == 'clear':
                    conversation = interactive_session.Interact()
                continue
            if text == 'exit':
                return
        else:
            if not script:
                return
            text = script.pop(0)
            print(f'\n{YEL}{text}{CLR}')

        response = conversation.respond(text)
        print(f'\n{BLU}{response}{CLR}\n\n')  # Blue response



if __name__ == '__main__':
    start()
