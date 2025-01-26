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

def extract_code_snippet(content: str, language: str = "python") -> str:
    """
    Extract code snippet from the content.
    
    Args:
        content (str):  Content to extract code snippet from llm response
        language (str): Language of the code snippet, defaults to "python"
        
    Returns:
        str: The extracted code snippet
    """
    
    if not content:
        return ""
        
    # Try to match code block with specified language
    pattern = rf'```{language}\s*(.*?)```'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # If no language-specific block found, try generic code block
    pattern = r'```\s*(.*?)```'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # If no code block found, return the original content
    return content.strip()