import json
import re

def json_exact(text: str) -> dict:
    """
    Extracts and parses a JSON object from a given string enclosed between ```json \n and ```.

    The function searches for a JSON block within the text and attempts to parse it into a Python
    dictionary. If the extraction or parsing fails, it gracefully handles the error and returns
    an empty dictionary.

    Args:
        text (str): The input string potentially containing a JSON block.

    Returns:
        dict: A dictionary representation of the first valid JSON object found, or an empty dictionary if none is found.
    """
    # Define the regex pattern for extracting a JSON block enclosed between ```json and ```
    pattern = r'```json\s*\n(.*?)```'

    try:
        # Search for the pattern in the input text
        match = re.search(pattern, text, re.DOTALL)

        if match:
            # Extract the JSON string found by regex
            json_string = match.group(1).strip()
            # Parse the JSON string into a Python dictionary
            return json.loads(json_string)
        else:
            # Return an empty dictionary if no match is found
            return {}

    except (json.JSONDecodeError, Exception) as e:
        # Handle JSON decoding errors or other exceptions, return an empty dictionary
        print(f"Error parsing JSON: {e}")
        return {}