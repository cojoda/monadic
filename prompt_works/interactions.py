from . import services
from . import config



def responses(input):
    return services.openai_client.responses.create(
        input            =input,
        model            =config.COMPLETION_DEFAULT,
        max_output_tokens=1000,
        timeout          =30,
        temperature      =0.3,
        top_p            =0.3
    )


def embeddings(input):
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
