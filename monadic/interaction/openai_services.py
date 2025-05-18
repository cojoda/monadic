import logging

from monadic import services
from monadic import config



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


def speech(input):
    # instructions = """Accent/Affect: Warm, refined, and gently instructive, reminiscent of a friendly art instructor.\n\nTone: Calm, encouraging, and articulate, clearly describing each step with patience.\n\nPacing: Slow and deliberate, pausing often to allow the listener to follow instructions comfortably.\n\nEmotion: Cheerful, supportive, and pleasantly enthusiastic; convey genuine enjoyment and appreciation of art.\n\nPronunciation: Clearly articulate artistic terminology (e.g., \"brushstrokes,\" \"landscape,\" \"palette\") with gentle emphasis.\n\nPersonality Affect: Friendly and approachable with a hint of sophistication; speak confidently and reassuringly, guiding users through each painting step patiently and warmly."""
    with services.openai_client.audio.speech.with_streaming_response.create(
        model='gpt-4o-mini-tts',
        voice='coral',
        input=input,
        # instructions=instructions,
        response_format='wav',
    ) as responses:
        responses.stream_to_file('data/audio/recording/input.wav')
