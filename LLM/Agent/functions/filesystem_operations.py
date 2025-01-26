import os

def write_to_file(path: str, content: str) -> str:
    """
    Write content to a file at the specified path.

    Args:
        path (str): The path to the file.
        content (str): The content to write to the file.

    Returns:
        str: A message indicating the success or failure of the write operation.

    Raises:
        Exception: If an error occurs while writing the file.
    """
    try:
        # 创建包含文件的目录（如果不存在）
        os.makedirs(os.path.dirname(path), exist_ok=True)

        # 打开文件并写入内容
        with open(path, 'w') as file:
            file.write(content)
        return f"Successfully wrote to file: {path}"
    except Exception as e:
        return f"An error occurred while writing to the file: {e}"

def read_file_segment(file_path, line_range=(1, 200), include_line_numbers=True):
    """
    Reads a segment of a file specified by line numbers.

    Args:
        file_path (str): Path to the file.
        line_range (tuple of two integers): The range of lines to read, default is (1, 200).
        include_line_numbers (bool): Whether to include line numbers in the output, default is True.
    
    Returns:
        str: A string containing the segment of the file read, along with additional file information.
    
    Exceptions:
        Returns an error message if the file cannot be found or read.
    """
    start_line, end_line = line_range
    if start_line < 1 or end_line < start_line:
        return "Invalid line range. Ensure that start line is >= 1 and end line >= start line."

    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
    except FileNotFoundError:
        return f"Error: The file '{file_path}' does not exist."
    except Exception as e:
        return f"Error reading file: {str(e)}"

    total_lines = len(lines)
    if total_lines < start_line:
        return (f"File has only {total_lines} lines, which is less than the start line {start_line}. "
                f"No content to display in the specified range.")

    actual_end_line = min(end_line, total_lines)
    pre_segment_lines = start_line - 1
    post_segment_lines = max(0, total_lines - actual_end_line)
    
    # Prepare the content segment
    content_lines = lines[start_line - 1:actual_end_line]
    if include_line_numbers:
        content = ''.join(f"{i+start_line}: {line}" for i, line in enumerate(content_lines))
    else:
        content = ''.join(content_lines)

    # Prepare the result with exact format matching the tests
    result = []
    result.append(f"Lines before segment: {pre_segment_lines}")
    result.append("Lines in segment:")
    if content:
        result.append(content.rstrip())  # Remove trailing newline
    result.append(f"Lines after segment: {post_segment_lines}")
    
    return '\n'.join(result) + '\n'