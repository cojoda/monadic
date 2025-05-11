import os
import sys

from monadic import config

from monadic import interactive_session
from monadic.audio import audio_recorder
from monadic.interactions import transcriptions



logger = config.logging.getLogger(__name__)



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




def get_input():
    print('Press Enter to start recording or type a question:', end=f'\n\n{config.YEL}')
    text = input()
    print(f'{config.CLR}', end='')

    if text == '':
        delete_lines(3)
        print('\n\n', end='')
        recording = audio_recorder.Record()
        delete_lines(2)
        text = transcriptions(recording.output_file).text
        print(f'{config.YEL}{text}{config.CLR}\n')
    elif text == 'audit':
        delete_lines(3)
        print(f'\n\n{text}\n\n')
        if config.logging.getLogger().getEffectiveLevel() == config.logging.WARNING:
            config.logging.getLogger().setLevel(config.logging.INFO)
            logger.info("Audit logging enabled")
        else:
            logger.info("Audit logging disabled")
            config.logging.getLogger().setLevel(config.logging.WARNING)
        return text
    elif text in ('clear', 'exit'):
        if text == 'clear':
            clear_screen()
        return text
    else:
        delete_lines(3)
        print(f'\n\n{config.YEL}{text}{config.CLR}\n')
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
            print(f'\n{config.YEL}{text}{config.CLR}')

        response = conversation.respond(text)
        print(f'\n{config.BLU}{response}{config.CLR}\n\n')  # Blue response



if __name__ == '__main__':
    start()
