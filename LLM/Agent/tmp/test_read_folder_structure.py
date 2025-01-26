import os
import tempfile
import shutil
from datetime import datetime, timedelta
import pytest
from read_folder_structure import get_folder_structure

@pytest.fixture
def setup_test_environment():
    """Fixture to setup test environment with a folder structure."""
    # Create a temporary directory
    test_dir = tempfile.mkdtemp()

    # Create a nested folder structure with files
    os.makedirs(os.path.join(test_dir, 'folder/subfolder'))
    
    with open(os.path.join(test_dir, 'folder', 'file1.txt'), 'w') as f:
        f.write('Hello World')
    
    with open(os.path.join(test_dir, 'folder', 'file2.py'), 'w') as f:
        f.write('print("Hello Python")')

    with open(os.path.join(test_dir, 'folder/subfolder', 'file3.md'), 'w') as f:
        f.write('# Markdown File')

    # Create symlink and circular symlink
    os.symlink(os.path.join(test_dir, 'folder'), os.path.join(test_dir, 'link_to_folder'))
    os.symlink(os.path.join(test_dir, 'folder'), os.path.join(test_dir, 'folder', 'circular_link'))

    yield test_dir

    # Cleanup
    shutil.rmtree(test_dir)

def test_folder_structure_building(setup_test_environment):
    """Test different types and levels of folder structure."""
    test_dir = setup_test_environment
    expected_structure = {
        'folder': {
            'file1.txt': {'size': 11, 'creation_time': pytest.approx(datetime.now().isoformat(), abs=1)},
            'file2.py': {'size': 19, 'creation_time': pytest.approx(datetime.now().isoformat(), abs=1)},
            'subfolder': {
                'file3.md': {'size': 15, 'creation_time': pytest.approx(datetime.now().isoformat(), abs=1)}
            },
            # 'circular_link': {}  # This part should be excluded because it causes a circular reference
        },
        # 'link_to_folder': {}  # Symlink should not be followed or handled correctly
    }
    
    actual_structure = get_folder_structure(test_dir)
    assert 'folder' in actual_structure
    assert 'subfolder' in actual_structure['folder']
    assert 'file1.txt' in actual_structure['folder']
    assert 'file2.py' in actual_structure['folder']
    assert 'file3.md' in actual_structure['folder']['subfolder']

def test_filtering(setup_test_environment):
    """Test filtering of files and folders based on extensions and names."""
    test_dir = setup_test_environment
    result = get_folder_structure(test_dir, filter_ext=['.txt'], filter_name=['file3.md'])
    assert 'file1.txt' in result['folder']
    assert 'file2.py' not in result['folder']
    assert 'subfolder' not in result['folder']  # 'subfolder' is filtered out because 'file3.md' is not at this level in comparison

def test_non_existent_folder():
    """Ensure FileNotFoundError is raised for non-existent folders."""
    with pytest.raises(FileNotFoundError):
        get_folder_structure('non_existent_path')

def test_symlink_handling(setup_test_environment):
    """Test handling of symbolic links."""
    test_dir = setup_test_environment
    result = get_folder_structure(test_dir)
    assert 'link_to_folder' in result
    assert 'circular_link' not in result['folder']  # Must not enter a circular symlink structure

def test_platform_compatibility(setup_test_environment):
    """Test platform compatibility handling (assume this for mocking platform differences)."""
    test_dir = setup_test_environment
    try:
        result = get_folder_structure(test_dir)
        assert result is not None
    except OSError:
        pytest.fail("The function raised an OSError unexpectedly!")