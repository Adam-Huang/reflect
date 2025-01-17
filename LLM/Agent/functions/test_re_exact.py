import unittest
from re_exact import json_exact  # assuming the function is in a module named your_module

class TestJsonExactFunction(unittest.TestCase):

    def test_valid_json_extraction(self):
        # 测试1：格式正确的字符串
        text = "Some text before ```json \n{\"key\": \"value\"}``` some text after"
        expected_output = {"key": "value"}
        self.assertEqual(json_exact(text), expected_output)

    def test_invalid_json_format(self):
        # 测试2：格式不正确的字符串
        text = "Some text before ```json \n{key: value}``` some text after"
        expected_output = {}
        self.assertEqual(json_exact(text), expected_output)

    def test_no_json_part(self):
        # 测试3：不包含JSON的字符串
        text = "This text does not contain a JSON block."
        expected_output = {}
        self.assertEqual(json_exact(text), expected_output)

    def test_multiple_json_blocks(self):
        # 测试4：多个JSON块
        text = (
            "First block ```json \n{\"first\": \"json\"}``` "
            "Second block ```json \n{\"second\": \"json\"}```"
        )
        expected_output = {"first": "json"}
        self.assertEqual(json_exact(text), expected_output)

    def test_empty_string(self):
        # 测试5：空字符串
        text = ""
        expected_output = {}
        self.assertEqual(json_exact(text), expected_output)

if __name__ == "__main__":
    unittest.main()