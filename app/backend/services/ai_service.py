import os
import openai
import base64
import json

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_room_for_mess(image_path):
    """
    Analyzes an image using GPT-4 Vision and returns a list of cleaning tasks.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        return []

    client = openai.OpenAI(api_key=api_key)
    
    base64_image = encode_image(image_path)
    
    prompt_text = os.getenv(
        "PROMPT",
        "Analyze the provided image of a room and identify items that are out of place or contribute to messiness. "
        "Return a JSON-formatted array of strings, where each string is a specific cleaning task. For example: "
        '["Pick up the clothes on the floor", "Clear the desk of papers", "Make the bed"]'
    )

    try:
        response = client.chat.completions.create(
            model=os.getenv("AI_MODEL", "gpt-4-vision-preview"),
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        },
                    ],
                }
            ],
            max_tokens=300,
        )
        
        content = response.choices[0].message.content
        # The response might be inside a code block
        if content.startswith("```json"):
            content = content.strip("```json\n").strip("```")
            
        tasks = json.loads(content)
        return tasks
    except openai.APIError as e:
        print(f"Error calling OpenAI API: {e}")
        return []
    except (json.JSONDecodeError, TypeError):
        print(f"Error decoding JSON from response: {content}")
        return []