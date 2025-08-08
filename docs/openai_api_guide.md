# docs/openai_api_guide.md

# Current Available OpenAI models to use (As of August 2025)
gpt-5-mini

# Usage Example
from openai import OpenAI
from pydantic import BaseModel

client = OpenAI()

# 1. Define the Pydantic schema for the desired output.
class MySchema(BaseModel):
    name: str
    is_correct: bool

# 2. Call the API using client.responses.parse and pass the schema.
response = client.responses.parse(
    model="gpt-5-mini",
    input=[
        {"role": "system", "content": "Extract data into the schema."},
        {"role": "user", "content": "The name is 'Example' and the status is true."}
    ],
    text_format=MySchema,
)

# 3. Access the structured data.
parsed_output = response.output_parsed