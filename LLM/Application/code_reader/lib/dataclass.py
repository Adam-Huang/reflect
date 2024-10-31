#!/usr/bin/env python3

"""
data.py
"""

from dataclasses import dataclass, field, asdict, fields
from typing import List, Dict, Union

# --- base classes ---
@dataclass
class LineRegion:
    """Represents a region in a text defined by start and end line numbers."""
    start: int = 0
    end: int = 0

@dataclass
class Description:
    """Represents a description of textual content"""
    uri: str = "" # 一般表示 文件uri
    region: LineRegion = field(default_factory=LineRegion)
    description: str = ""
    labels: List[str] = field(default_factory=list)

# --- code related classes ---
@dataclass
class DefinitionReferences:
    """Represents the definition and references of a code element."""
    definition: LineRegion = field(default_factory=LineRegion)
    references: List[LineRegion] = field(default_factory=list)

@dataclass
class FunctionInfo(DefinitionReferences, Description):
    """Represents information about a function, including its name, line number, variables, and description."""
    name: str = ""
    docstring: str = ""
    variables: Dict[str, DefinitionReferences] = field(default_factory=dict) # key 是变量名

@dataclass
class ClassInfo(FunctionInfo):
    """Represents information about a class, including its functions."""
    functions: Dict[str, FunctionInfo] = field(default_factory=dict)

@dataclass
class PythonFileStructure(Description):
    """Represents the structure of a Python file, including imports, classes, functions, and variables."""
    imports: List[List[int]] = field(default_factory=list)
    classes: Dict[str, ClassInfo] = field(default_factory=dict)
    functions: Dict[str, FunctionInfo] = field(default_factory=dict) # key 是函数名
    variables: Dict[str, DefinitionReferences] = field(default_factory=dict) # key 是变量名

# --- general project classes ---
@dataclass
class FileDescription(Description):
    """Represents the description of a single file in the project"""
    file_type: str = ""
    relative_path: str = ""
    attribution: Dict[str, str] = field(default_factory=dict)
    full_read: bool = True
    dependencies: List[str] = field(default_factory=list)
    snippet: List[Description] = field(default_factory=list)

@dataclass
class DirectoryDescription(Description):
    relative_path: str = ""
    files: Dict[str, Union[PythonFileStructure, FileDescription]] = field(default_factory=dict)
    subdirectories: Dict[str, 'DirectoryDescription'] = field(default_factory=dict) # key 是目录名

@dataclass
class ProjectDescription(DirectoryDescription):
    """Represents the description of an entire project"""
    iteration_order: List[str] = field(default_factory=list)
    version: str = ""
