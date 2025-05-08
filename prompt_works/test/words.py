from openai import OpenAI
import os
import re


EMBEDDING_DEFAULT  = 'text-embedding-3-small'
embeddings = lambda text: client.embeddings.create(
    model=EMBEDDING_DEFAULT,
    input=text
)


def call(service, data):
        return service(data)

api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI()



def get_words(text):
    result = []
    words = re.findall(r'\b\w+\b', text.lower())
    print(f'word count: {len(words)}')
    for word in words:
        if len(word) >= 4: result.append(word)
    return result



def get_frequency(words):
    result = []
    frequency = {}
    for word in words:
        if word in frequency:
            frequency[word] += 1
        else:
            frequency[word] = 1
    for word, frequency in frequency.items():
        result.append({'word': word, 'frequency': frequency})
    return result


def get_solo_words(list):
    return [item['word'] for item in list if item['frequency'] <=5]


# def get_low_frequency(frequency_list):
#     frequency_sorted = [j['word'] for j in sorted(frequency_list, key=lambda i: i['frequency'])]
#     return frequency_sorted[:len(frequency_sorted) // 5]


import random

def shuffle_word_list(words):

    return random.sample(words, k=len(words))
    
    

f = open('prompt_works/test/frequency.txt', 'r')
text = f.read()

words = get_words(text)
frequency = get_frequency(words)

from prompt_works.test.freq_highlight import colorize_text_in_terminal

frequency = shuffle_word_list(frequency)


colorize_text_in_terminal(text, [item['word'] for item in frequency if item['frequency'] == 1])