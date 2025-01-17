import subprocess
from typing import Dict

def execute_shell_command(command: str) -> Dict[str, str]:
    """
    Execute a shell command and capture its standard output and standard error.

    Args:
        command (str): The shell command to execute.

    Returns:
        Dict[str, str]: A dictionary with keys 'output' and 'error' capturing
                        the command's standard output and standard error respectively.

    Notes:
        - Caution is advised when passing user-generated input to this function to avoid
          security risks, such as command injection. It is recommended to validate or 
          restrict commands that can be executed.
    """
    if not command.strip():
        return {'output': '', 'error': 'Invalid command: Command string is empty or whitespace'}

    # Use subprocess to execute the command
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            text=True, 
            capture_output=True, 
            check=False
        )
        output = result.stdout
        error = result.stderr
    except Exception as e:
        output = ''
        error = f'Exception occurred: {str(e)}'

    return {'output': output, 'error': error}