import os
import unittest
import tempfile
from unittest import mock
from filesystem_operations import write_to_file

class TestWriteToFile(unittest.TestCase):

    def setUp(self):
        # 创建一个临时目录
        self.test_dir = tempfile.TemporaryDirectory()
        self.test_file_path = os.path.join(self.test_dir.name, 'test_file.txt')

    def tearDown(self):
        # 清理临时目录
        self.test_dir.cleanup()

    def test_create_and_write_to_new_file(self):
        # 测试场景1：传入一个不存在的路径，应该成功创建文件并写入内容
        write_to_file(self.test_file_path, 'Hello, World!')
        # 检查文件内容是否正确
        with open(self.test_file_path, 'r') as file:
            content = file.read()
        self.assertEqual(content, 'Hello, World!')

    def test_overwrite_existing_file(self):
        # 测试场景2：传入一个已存在的文件，应该覆盖内容
        # 先写入初始内容
        with open(self.test_file_path, 'w') as file:
            file.write('Old Content')

        # 使用函数覆盖内容
        write_to_file(self.test_file_path, 'New Content')

        # 检查新内容是否正确
        with open(self.test_file_path, 'r') as file:
            content = file.read()
        self.assertEqual(content, 'New Content')

    def test_write_empty_content(self):
        # 测试场景3：对于空字符串内容，文件应被创建且内容为空
        write_to_file(self.test_file_path, '')
        # 检查文件是否为空
        with open(self.test_file_path, 'r') as file:
            content = file.read()
        self.assertEqual(content, '')

    @mock.patch('builtins.open', side_effect=PermissionError("No permission"))
    def test_exception_handling(self, mock_open):
        # 测试异常场景：模拟没有写权限的情况
        try:
            write_to_file('/no/permission/path.txt', 'Some content')
        except PermissionError:
            self.fail("write_to_file() raised PermissionError unexpectedly!")

if __name__ == '__main__':
    unittest.main()