#!/usr/bin/env python3
"""
directory_parser.py

This script analyzes a specified directory, parses the content of Python files,
and populates data classes that describe the structure and elements within each file.
"""

import os
import ast
import json
from typing import List, Dict
from lib.dataclass import (
    LineRegion, 
    FunctionInfo, 
    ClassInfo, 
    PythonFileStructure, 
    FileDescription, 
    DirectoryDescription, 
    ProjectDescription
)
from dataclasses import asdict

def parse_python_file(file_path: str) -> PythonFileStructure:
    """Parse a Python file to extract its structural information."""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.readlines()

    # Initialize the PythonFileStructure object
    py_file_structure = PythonFileStructure(uri=file_path)

    # Parse the AST of the file
    file_ast = ast.parse(''.join(content), filename=file_path)

    # Extract imports, classes, and function definitions
    for node in ast.walk(file_ast):
        if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            # Collect import line numbers
            py_file_structure.imports.append([node.lineno, node.end_lineno])
        
        elif isinstance(node, ast.FunctionDef):
            # Collect function information
            func_info = FunctionInfo(
                name=node.name,
                definition=LineRegion(start=node.lineno, end=node.end_lineno),
                description=ast.get_docstring(node) or ""
            )
            py_file_structure.functions[node.name] = func_info
        
        elif isinstance(node, ast.ClassDef):
            # Collect class information
            class_info = ClassInfo(
                name=node.name,
                definition=LineRegion(start=node.lineno, end=node.end_lineno),
                description=ast.get_docstring(node) or ""
            )
            # Collect functions within the class
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    method_info = FunctionInfo(
                        name=item.name,
                        definition=LineRegion(start=item.lineno, end=item.end_lineno),
                        description=ast.get_docstring(item) or ""
                    )
                    class_info.functions[item.name] = method_info
            py_file_structure.classes[node.name] = class_info
    
    return py_file_structure


def analyze_directory(directory_path: str) -> ProjectDescription:
    """Analyze a directory to describe its Python files and structure."""

    def analyze_recursive(current_path: str, parent_dir_description: DirectoryDescription = None) -> DirectoryDescription:
        relative_dir_path = os.path.relpath(current_path, directory_path)
        if "__pycache__" in relative_dir_path:
            return None
            
        dir_description = DirectoryDescription(relative_path=relative_dir_path)
        
        # Process all files in current directory
        for file in os.listdir(current_path):
            file_path = os.path.join(current_path, file)
            if os.path.isfile(file_path):
                relative_file_path = os.path.relpath(file_path, directory_path)
                if file.endswith('.py'):
                    python_file_structure = parse_python_file(file_path)
                    python_file_structure.uri = file_path
                    python_file_structure.relative_path = relative_file_path
                    dir_description.files[relative_file_path] = python_file_structure
                else:
                    file_structure = FileDescription(
                        uri=file_path,
                        relative_path=relative_file_path,
                        file_type=file.split('.')[-1],
                    )
                    dir_description.files[relative_file_path] = file_structure
            
            # Recursively process subdirectories
            elif os.path.isdir(file_path):
                sub_dir_description = analyze_recursive(file_path, dir_description)
                if sub_dir_description:
                    dir_description.subdirectories[file] = sub_dir_description
        
        return dir_description
    
    root_dir_description = analyze_recursive(directory_path)
    
    project_description = ProjectDescription(
        relative_path=root_dir_description.relative_path,
        files=root_dir_description.files,
        subdirectories=root_dir_description.subdirectories,
        version="0.0.1"
    )
    return project_description


def main(directory_path: str, output_path: str):
    """Main function to execute the directory parsing."""
    project_description = analyze_directory(directory_path)
    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(asdict(project_description), file, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description="Parse a directory and extract metadata from Python files."
    )
    parser.add_argument(
        '--directory',
        type=str,
        help='The path to the directory to be analyzed.'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='The path to the output file.'
    )
    args = parser.parse_args()
    main(args.directory, args.output)