import os

class FileReader:
    def __init__(self, base_path, max_depth=1, max_read_size=1024):
        self.base_path = base_path
        self.max_depth = max_depth
        self.max_read_size = max_read_size

    def list_directory(self, path=None, current_depth=0):
        """List contents of a directory up to a certain depth."""
        if path is None:
            path = self.base_path

        if current_depth > self.max_depth:
            return []

        try:
            entries = os.listdir(path)
        except OSError as e:
            print(f"Error reading directory {path}: {e}")
            return []

        result = []
        for entry in entries:
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path) and current_depth < self.max_depth:
                result.append({
                    "directory": entry,
                    "contents": self.list_directory(full_path, current_depth + 1)
                })
            else:
                result.append(entry)
        return result

    def read_file(self, file_path, start=0, read_size=None):
        """Read a file from a specific path with a certain byte size."""
        if read_size is None:
            read_size = self.max_read_size

        try:
            with open(file_path, 'rb') as file:
                file.seek(start)
                data = file.read(read_size)
                return data
        except OSError as e:
            print(f"Error reading file {file_path}: {e}")
            return None