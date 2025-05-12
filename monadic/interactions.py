import logging

from . import services
from . import config



logger = logging.getLogger(__name__)



def log_interanction(input):
    logger.info('\n'+config.MON+'},\n'.join(str(input).split('},'))+config.CLR)



def responses(input):
    log_interanction(input)
    return services.openai_client.responses.create(
        input            =input,
        model            =config.COMPLETION_DEFAULT,
        max_output_tokens=1000,
        timeout          =30,
        temperature      =0.3,
        top_p            =0.3
    )



def embeddings(input):
    log_interanction(f'openai_client.embeddings.create: {len(input)} embeddings requested')
    return services.openai_client.embeddings.create(
        model=config.EMBEDDING_DEFAULT,
        input=input
    )



def transcriptions(filename):
    with open(filename, 'rb') as audio_file:
        return services.openai_client.audio.transcriptions.create(
            model='gpt-4o-transcribe',
            file =audio_file
        )
