import os
import unittest
import tempfile
from unittest import mock
from filesystem_operations import write_to_file, read_file_segment

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

class TestReadFileSegment(unittest.TestCase):

    def setUp(self):
        # 创建一个临时文件用于测试
        self.file_name = 'test_file.txt'
        with open(self.file_name, 'w') as f:
            f.writelines([f"Line {i+1}\n" for i in range(10)])  # 写入10行

    def tearDown(self):
        # 测试结束后删除临时文件
        if os.path.exists(self.file_name):
            os.remove(self.file_name)

    def test_normal_read(self):
        # 正常读取文件，检查返回格式和内容
        result = read_file_segment(self.file_name, (1, 5))
        expected = (
            "Lines before segment: 0\n"
            "Lines in segment:\n"
            "1: Line 1\n"
            "2: Line 2\n"
            "3: Line 3\n"
            "4: Line 4\n"
            "5: Line 5\n"
            "Lines after segment: 5\n"
        )
        self.assertEqual(result, expected)

    def test_read_beyond_file_length(self):
        # 读取范围超过文件长度
        result = read_file_segment(self.file_name, (8, 15))
        expected = (
            "Lines before segment: 7\n"
            "Lines in segment:\n"
            "8: Line 8\n"
            "9: Line 9\n"
            "10: Line 10\n"
            "Lines after segment: 0\n"
        )
        self.assertEqual(result, expected)

    def test_partially_in_range(self):
        # 文件只有部分行在读取范围内
        result = read_file_segment(self.file_name, (9, 12))
        expected = (
            "Lines before segment: 8\n"
            "Lines in segment:\n"
            "9: Line 9\n"
            "10: Line 10\n"
            "Lines after segment: 0\n"
        )
        self.assertEqual(result, expected)

    def test_file_not_exists(self):
        # 尝试读取不存在的文件，检查异常处理
        result = read_file_segment('non_existent_file.txt')
        expected = "Error: The file 'non_existent_file.txt' does not exist."
        self.assertEqual(result, expected)

    def test_include_line_numbers(self):
        # 检查是否按照参数要求返回行号
        result = read_file_segment(self.file_name, (3, 5), include_line_numbers=False)
        expected = (
            "Lines before segment: 2\n"
            "Lines in segment:\n"
            "Line 3\n"
            "Line 4\n"
            "Line 5\n"
            "Lines after segment: 5\n"
        )
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()