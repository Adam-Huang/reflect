"""
Function registry system for dynamically loading functions from this directory.
"""
import importlib
import os
import inspect
from typing import Dict, Any, Callable

# Global registry to store all functions
function_registry: Dict[str, Callable] = {}

def register_function(name: str, func: Callable) -> None:
    """Register a function in the global registry."""
    function_registry[name] = func

def get_function(name: str) -> Callable:
    """Get a function from the registry."""
    return function_registry.get(name)

def list_functions() -> Dict[str, Callable]:
    """List all registered functions."""
    return function_registry.copy()

def auto_register_functions() -> None:
    """
    Automatically discover and register all functions in this directory.
    Looks for functions that have a specific decorator or naming convention.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Get all Python files in the directory
    for filename in os.listdir(current_dir):
        if filename.endswith('.py') and not filename.startswith('test_') and filename != '__init__.py':
            module_name = filename[:-3]  # Remove .py extension
            
            # Import the module
            module = importlib.import_module(f'.{module_name}', package=__package__)
            
            # Look for all functions in the module
            for name, obj in inspect.getmembers(module):
                # Register only functions that don't start with underscore
                if inspect.isfunction(obj) and not name.startswith('_'):
                    register_function(f"{module_name}.{name}", obj)

# Automatically register all functions when this package is imported
auto_register_functions()
