import os
import openai
from typing import Dict, Any, List, Type
from pydantic import BaseModel

# Ensure API key is set
if "OPENAI_API_KEY" not in os.environ:
    raise EnvironmentError("OPENAI_API_KEY environment variable not set.")

# Initialize the async client
client = openai.AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

async def get_structured_completion(
    prompt_input: List[Dict[str, str]],
    schema: Type[BaseModel],
    model: str = "gpt-5-nano"
) -> Dict[str, Any]:
    """
    Calls the OpenAI Responses API with a Pydantic schema to get a structured completion.

    Returns:
        A dictionary containing the parsed Pydantic object and token usage.
    """
    try:
        response = await client.responses.parse(
            model=model,
            instructions="## MANDATE ## THINK HARD",
            input=prompt_input,
            text_format=schema,
        )

        if response.output_parsed:
            return {
                "parsed_content": response.output_parsed,
                "tokens": response.usage.total_tokens
            }
        else:
            # This can happen in cases of refusal, etc.
            print("Error: Failed to get parsed output from LLM.")
            return {"parsed_content": None, "tokens": response.usage.total_tokens}

    except Exception as e:
        print(f"An error occurred with the LLM provider: {e}")
        return {"parsed_content": None, "tokens": 0}