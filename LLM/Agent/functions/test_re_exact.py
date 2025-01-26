import unittest
from re_exact import json_exact, extract_code_snippet  # assuming the function is in a module named your_module

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

class TestExtractCodeSnippet(unittest.TestCase):
    def test_python_code_extraction(self):
        # Test extracting Python code
        content = '''Here's a Python function:
```python
def hello():
    print("Hello, World!")
```
End of code'''
        expected = 'def hello():\n    print("Hello, World!")'
        self.assertEqual(extract_code_snippet(content, "python"), expected)

    def test_different_language(self):
        # Test extracting code with different language
        content = '''JavaScript code:
```javascript
function hello() {
    console.log("Hello!");
}
```'''
        expected = 'function hello() {\n    console.log("Hello!");\n}'
        self.assertEqual(extract_code_snippet(content, "javascript"), expected)

    def test_no_language_specified(self):
        # Test generic code block without language
        content = '''Generic code:
```
print("Hello")
```'''
        expected = 'print("Hello")'
        self.assertEqual(extract_code_snippet(content), expected)

    def test_no_code_block(self):
        # Test content without code block
        content = "Just plain text without any code block"
        self.assertEqual(extract_code_snippet(content), content.strip())

    def test_empty_content(self):
        # Test empty content
        self.assertEqual(extract_code_snippet(""), "")

    def test_multiple_code_blocks(self):
        # Test content with multiple code blocks
        content = '''First block:
```python
def first():
    pass
```
Second block:
```python
def second():
    pass
```'''
        expected = 'def first():\n    pass'
        self.assertEqual(extract_code_snippet(content), expected)

if __name__ == "__main__":
    unittest.main()