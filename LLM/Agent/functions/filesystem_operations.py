import os

def write_to_file(path: str, content: str) -> None:
    try:
        # 创建包含文件的目录（如果不存在）
        os.makedirs(os.path.dirname(path), exist_ok=True)

        # 打开文件并写入内容
        with open(path, 'w') as file:
            file.write(content)
    except Exception as e:
        print(f"An error occurred while writing to the file: {e}")

