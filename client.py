
import sys

from prompt_works import interact

from prompt_works.audio.record import Record
from prompt_works.interactions import transcriptions



def delete_lines(n):
    for i in range(n):
        sys.stdout.write('\033[F\033[2K')
        sys.stdout.flush()



def start():
    conversation = interact.Interact()
    while True: 
        print('--------------------------------------------------------------------')
        print('Press Enter to start recording or type a question:')
        text = input('\n\033[93m')
        if text == '':
            delete_lines(1)
            record = Record()
            delete_lines(2)
            text = transcriptions(record.output_file).text
            print(f'{text}\033[0m',)
        elif text == 'exit': exit()
        print(f'\n\033[94m{conversation.respond(text)}\033[0m\n')



if __name__ == '__main__':
    start()