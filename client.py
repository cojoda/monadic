from monadic import config
import os
import sys


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



def skip_lines(n):
    print('', end=('\n'*n))



def print_color(text:str, color):
    print(f'{color}{text}\033[0m')



def get_input():
    print('Press Enter to start recording or type a question:')
    skip_lines(1)
    print(f'{config.YEL}', end='')
    text = input()
    print(f'{config.CLR}', end='')

    if text == 'exit': return text
    
    if text == '':
        delete_lines(3)
        skip_lines(2)
        text = transcribe()
        print_color(text, config.YEL)
        skip_lines(2)
    elif text == 'audit':
        return text
        # delete_lines(3)
        # skip_lines(2)
        # print(f'{text}')
        # skip_lines(2)
        # toggle_audit()
    elif text == 'clear':
        clear_screen()
    else:
        delete_lines(3)
        skip_lines(2)
        print_color(text, config.YEL)
        skip_lines(2)
    return text



# Load script from command line args supplied filename
def get_script():
    try:
        file = open(sys.argv[1], 'r', encoding='utf-8')
        script = file.read().splitlines()
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



# Toggle debug logging (off by default)
def toggle_audit():
    if config.logging.getLogger().getEffectiveLevel() == config.logging.WARNING:
        config.logging.getLogger().setLevel(config.logging.INFO)
        logger.info("Audit logging enabled")
    else:
        logger.info("Audit logging disabled")
        config.logging.getLogger().setLevel(config.logging.WARNING)
    



def start():
    conversation = interactive_session.Interact()

    # CLI arg supplied input file?
    script = get_script() if len(sys.argv) > 1 else False

    while True:
        print('--------------------------------------------------------------------')

        if script:
            text = script.pop(0)
            skip_lines(2)
            print_color(text, config.YEL)
            skip_lines(2)
        else:
            text = get_input()
        
        if text == 'audit':
            delete_lines(3)
            skip_lines(2)
            print(f'{text}')
            skip_lines(2)
            toggle_audit()
            continue
        if text in ('clear'):
            conversation = interactive_session.Interact()
            continue
        if text == 'exit':
            return
            

        # Querry LLM
        response = conversation.respond(text)
        skip_lines(1)
        print_color(response, config.BLU)
        skip_lines(2)



if __name__ == '__main__':
    start()
