import sys

from prompt_works import interactive_session
from prompt_works.audio import audio_recorder
from prompt_works.interactions import transcriptions



def delete_lines(n):
    for _ in range(n):
        sys.stdout.write('\033[F\033[2K')
        sys.stdout.flush()



def get_input():
    print('Press Enter to start recording or type a question:')
    text = input('\n\033[93m')
    print('\033[0m',end=None)
    if text == '':
        delete_lines(1)
        record = audio_recorder.Record()
        delete_lines(2)
        text = transcriptions(record.output_file).text
        print(f'{text}\033[0m',)
    elif text == 'exit': exit()
    return text



def get_script():
    try:
        file = open(sys.argv[1], 'r', encoding='utf-8')
        script = file.read().splitlines()
        file.close()
        return script
    except:
        return False



def start():
    conversation = interactive_session.Interact()

    script = False
    if len(sys.argv) > 1: script = get_script()
        
    while True:
        print('--------------------------------------------------------------------')
        if script is False:
            text = get_input()
        else:
            if len(script) == 0: return
            text = script.pop(0)
            print(f'\n\033[93m{text}\033[0m',)
        print(f'\n\033[94m{conversation.respond(text)}\033[0m\n')



if __name__ == '__main__':
    start()
