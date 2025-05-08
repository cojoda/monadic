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
client = OpenAI(api_key=api_key)


def get_words(text):
    result = []
    words = re.findall(r'\b\w+\b', text.lower())
    # print(f'word count: {len(words)}')
    for word in words:
        if len(word) >=3: result.append(word)
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
    result.sort(key=lambda i: i['frequency'])
    return result
    
    

f = open('frequency.txt', 'r')
text = f.read()    

words = get_words(text)
frequency = get_frequency(words)

# for item in frequency:
#     print(f'{item['word']}')

cutoff = len(frequency) - (len(frequency) // 20)
low_frequency = frequency[cutoff:]

low_words = []
for item in low_frequency:
     low_words.append(item['word'])

print(low_words)
e = call(embeddings, low_words)
# print(e)


# print(low_frequency)
# for item in low_frequency:
#     print(f'{item['word']}')


# for item in low_frequency:
#     e = call(embeddings, item['word'])
#     print(f'{item['word']}: {e.data[0].embedding[0]}')
