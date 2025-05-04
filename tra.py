from openai import OpenAI
import os
from dotenv import load_dotenv
import logging
import textwrap
import shutil
import numpy

MODEL_DEFAULT = "gpt-4.1-nano"
compress_str  = 'Input: [SOURCE], Objective: [type e.g., topic/sentiment/object]. Identify up to 3 best words representing primary [Objective]. Prefer words from SOURCE if suitable.'

columns = shutil.get_terminal_size().columns
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


logging.basicConfig(level=logging.WARNING, format=">>> %(message)s")


class Service(OpenAI):
    def __init__(self, model    = MODEL_DEFAULT,
                 system_content = '',
                 audit          = True,
                 log            = False):
        self.model = model
        # self.conversation = [{"role": "system", "content": system_content}]
        self.audit = audit
        self.prompt_tokens=0
        self.completion_tokens=0
        self.total_tokens=0
        self.log = log
        self.hello = []
        if(self.log): logging.getLogger("httpx").setLevel(logging.INFO)


    def exchange(self, request):
        if self.log: logging.info("Calling API...")
        conversation = [{'role': 'system', 'content': ''}]
        new_embed = chat.get_embedding(request)
        neighbors = self.get_neighbors(new_embed)
        if neighbors:
            for neighbor in neighbors:
                conversation.append({'role': 'assistnant', 'content': neighbor[1]})
        conversation.append({'role': 'user', 'content': request})
        reply = client.chat.completions.create(
            messages         = conversation,
            model            = self.model,
            max_tokens       = 600,
            stream           = False,
            timeout          = 30,
            stop             = None,
            n                = 1,
            top_p            = 1.0,
            temperature      = 0.3,
            frequency_penalty= 0.0,
            presence_penalty = 0.0,
            logit_bias       = {}
        )
        if self.audit: self.update_usage(reply.usage)
        return reply
    
    def get_embedding(self, text):
        response = client.embeddings.create(
            model='text-embedding-3-small',
            input=text
        )
        return [{'vector': response.data[0].embedding, 'chunk': text}]
    
    def update_usage(self, usage):
        self.prompt_tokens     += usage.prompt_tokens
        self.completion_tokens += usage.completion_tokens
        self.total_tokens      += usage.total_tokens

    def get_distance(self, emb_1, emb_2):
        a = numpy.array(emb_1)
        b = numpy.array(emb_2)
        dot_product = numpy.dot(a,b)
        norm_1 = numpy.linalg.norm(a)
        norm_2 = numpy.linalg.norm(b)
        if norm_1 == 0 or norm_2 == 0: return 0.0
        return dot_product / (norm_1 * norm_2)

    def get_neighbors(self, embed):
        if len(self.hello) < 2: return
        distances = []
        for item in self.hello:
            distances.append(self.get_distance(embed[0], item[0]))
        distances.sort(key=lambda d: abs(d))
        return distances[0:3]


    

if __name__ == "__main__":
    chat = Service(MODEL_DEFAULT, '', True, True)
    while True:
        user_content = input("Ask anything: ").strip()
        reply = chat.exchange(user_content)
        print(f'{chat.model}: {textwrap.fill(reply.choices[0].message.content, width=columns)}')
        # except Exception as e:
        #     logging.error(f"API call failed: {e}")
