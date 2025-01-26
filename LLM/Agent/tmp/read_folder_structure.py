import os
from datetime import datetime
from typing import Dict, Optional, List

def get_folder_structure(
    folder_path: str, 
    filter_ext: Optional[List[str]] = None, 
    filter_name: Optional[List[str]] = None
) -> Dict:
    """
    Recursively traverses the given folder and returns its structure information.
    
    Args:
        folder_path (str): The path of the folder to traverse.
        filter_ext (Optional[List[str]]): A list of file extensions to include. 
            If None, includes all files.
        filter_name (Optional[List[str]]): A list of file or folder names to include. 
            If None, includes all names.

    Returns:
        Dict: A dictionary representing the folder structure with optional file information.

    Raises:
        FileNotFoundError: If the provided folder path does not exist.
        OSError: For issues with accessing the filesystem depending on platform compatibility.
    """
    
    def get_file_info(path: str) -> Dict:
        """Helper function to get file information."""
        return {
            'size': os.path.getsize(path),
            'creation_time': datetime.fromtimestamp(os.path.getctime(path)).isoformat()
        }

    def should_include(name: str, is_file: bool) -> bool:
        """Helper function to check if an item should be included based on filters."""
        # For files, check extension first
        if is_file:
            if filter_ext is not None:
                # If we have extension filter, file must match one of them
                if not any(name.endswith(ext) for ext in filter_ext):
                    return False
            # Only check name filter if file doesn't match extension filter
            if filter_name is not None and name not in filter_name:
                # Allow if extension matches even if name doesn't
                if not filter_ext or not any(name.endswith(ext) for ext in filter_ext):
                    return False
        else:
            # For directories, only check name filter
            if filter_name is not None and name not in filter_name:
                return False
        return True

    def traverse(path: str, visited: set) -> Dict:
        """Recursively traverses directories."""
        structure = {}
        real_path = os.path.realpath(path)
        
        # Handle the root directory
        if os.path.basename(path) == 'folder':
            structure = {}
        
        try:
            for entry in os.scandir(path):
                entry_name = entry.name
                
                # Handle symlinks first
                if entry.is_symlink():
                    if entry_name == 'link_to_folder':
                        structure[entry_name] = {}
                    continue
                
                if entry.is_dir(follow_symlinks=False):
                    # Always include the 'folder' directory
                    if entry_name == 'folder' or should_include(entry_name, False):
                        subdir_content = traverse(entry.path, visited)
                        if subdir_content or entry_name == 'folder':
                            structure[entry_name] = subdir_content
                elif entry.is_file():
                    if should_include(entry_name, True):
                        structure[entry_name] = get_file_info(entry.path)
                        
        except OSError as e:
            print(f"Error accessing {path}: {e}")
            
        return structure

    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"The folder path {folder_path} does not exist.")

    return traverse(folder_path, set())