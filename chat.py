from openai import OpenAI
import heapq
import os
import numpy
import json


api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)


COMPLETION_DEFAULT = 'gpt-4.1-mini'
COMPLETION_NANO    = 'gpt-4.1-nano'
EMBEDDING_DEFAULT  = 'text-embedding-3-small'
TOP_N    = 3
RECENT_N = 5


responses = lambda text: client.responses.create(
    input            =text,
    model            =COMPLETION_DEFAULT,
    max_output_tokens=1000,
    timeout          =30,
    temperature      =0.3,
    top_p            =0.3
)


embeddings = lambda text: client.embeddings.create(
    model=EMBEDDING_DEFAULT,
    input=text
)



class Discussion:


    def __init__(self):
        self.dialogue = []


    def call(self, service, data):
        return service(data)
    

    def exchange(self, input):
        transcription = self.transcribe('user',input)
        history = f'[{self.get_history(transcription)}{{role: user, content: {input}}}]'
        output = self.call(responses, history).output_text
        self.transcribe('assistant' ,output)
        return output
    

    def transcribe(self, role, text):
        embedding = self.call(embeddings, text).data[0].embedding
        neighbors = self.get_neighbors(embedding)
        self.dialogue.append({'role': role,'chunk': text, 'vector': embedding, 'neighbors': neighbors})
        return self.dialogue[-1]
    

    def get_history(self, item):
        neighbors = item['neighbors']
        return ','.join(
            f'{{role: {self.dialogue[n['index']]['role']}, content: {self.dialogue[n['index']]['chunk']}}}'
            for n in neighbors) + ','
    

    # TODO: fully replace get_history with JSON friendly version
    def get_json_history(self, item):
        history = [{'role': self.dialogue[n['index']]['role'],
                    'content': self.dialogue[n['index']]['chunk']} for n in item['neighbors']]
        return json.dumps(history)

    
    def get_neighbors(self, target_item):
        dialogue_len = len(self.dialogue)
        cutoff = max(0, dialogue_len - RECENT_N)
        past_neighbor_candidates = [{'distance': self.distance(target_item, entry['vector']),
                                     'index': i}
            for i, entry in enumerate(self.dialogue[:cutoff])
        ]
        top_past_neighbors = heapq.nsmallest(TOP_N, past_neighbor_candidates, key=lambda n: n['distance'])
        recent_neighbors = [{'distance': self.distance(target_item, entry['vector']),
                             'index': i}
            for i, entry in enumerate(self.dialogue[cutoff:], start=cutoff)
        ]
        combined_neighbors = top_past_neighbors + recent_neighbors
        combined_neighbors.sort(key=lambda n: n['index'])
        return combined_neighbors[:TOP_N+RECENT_N]
    
        

    def distance(self, v1, v2):
        a = numpy.array(v1)
        b = numpy.array(v2)
        dot_product = numpy.dot(a,b)
        norm_1 = numpy.linalg.norm(a)
        norm_2 = numpy.linalg.norm(b)
        if norm_1 == 0 or norm_2 == 0: return 0.0
        return dot_product / (norm_1 * norm_2)




discussion = Discussion()
# Load the file
# with open('test3.json', 'r') as f:
#     test_data = json.load(f)
# for item in test_data:
#     text = item['text']

while True: 
    print('--------------------------------------------------------------------')
    text = input('Ask anything: ').strip()
    # print(f'Ask anything: {text}')
    print(f'\n{discussion.exchange(text)}\n')
