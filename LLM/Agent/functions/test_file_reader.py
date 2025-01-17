import unittest
import os
from file_reader import FileReader

class TestFileReader(unittest.TestCase):

    def setUp(self):
        # Setup temporary directory and files for testing
        self.base_path = './test_directory'
        os.makedirs(self.base_path, exist_ok=True)

        # Create test files
        with open(os.path.join(self.base_path, 'file1.txt'), 'w') as f:
            f.write('Hello, this is the content of file1.')

        with open(os.path.join(self.base_path, 'file2.txt'), 'w') as f:
            f.write('This is another file with some text.')

        self.sub_dir = os.path.join(self.base_path, 'sub_dir')
        os.makedirs(self.sub_dir, exist_ok=True)

        with open(os.path.join(self.sub_dir, 'file3.txt'), 'w') as f:
            f.write('Content of file in sub directory.')

        self.file_reader = FileReader(self.base_path, max_depth=2, max_read_size=1024)

    def tearDown(self):
        # Cleanup after tests
        os.remove(os.path.join(self.base_path, 'file1.txt'))
        os.remove(os.path.join(self.base_path, 'file2.txt'))
        os.remove(os.path.join(self.sub_dir, 'file3.txt'))
        os.rmdir(self.sub_dir)
        os.rmdir(self.base_path)

    def test_list_directory(self):
        contents = self.file_reader.list_directory()
        print(contents)
        self.assertIn('file1.txt', contents)
        self.assertIn('file2.txt', contents)

    def test_read_file(self):
        content = self.file_reader.read_file(os.path.join(self.base_path, 'file1.txt'))
        self.assertEqual(content.decode('utf-8'), 'Hello, this is the content of file1.')

if __name__ == '__main__':
    unittest.main()