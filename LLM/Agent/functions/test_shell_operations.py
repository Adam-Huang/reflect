import unittest
from shell_operations import execute_shell_command  # 替换 my_module 为实际模块名

class TestExecuteShellCommand(unittest.TestCase):

    def test_echo_command(self):
        # Test a simple command that should succeed
        command = 'echo "Hello, World!"'
        expected_output = {'output': 'Hello, World!\n', 'error': ''}
        result = execute_shell_command(command)
        self.assertEqual(result, expected_output, f'Expected {expected_output}, but got {result}')

    def test_nonexistent_command(self):
        # Test a command that does not exist
        command = 'nonexistentcommand'
        result = execute_shell_command(command)
        self.assertEqual(result['output'], '', 'Output should be empty for a nonexistent command')
        self.assertTrue(result['error'], 'Error message should not be empty for a nonexistent command')

    def test_no_permission_command(self):
        # Test a command that likely requires higher privileges
        command = 'chmod 000 /root'
        result = execute_shell_command(command)
        self.assertEqual(result['output'], '', 'Output should be empty for a command with no permission')
        self.assertTrue(result['error'], 'Error message should not be empty for a command with no permission')

    def test_empty_command(self):
        # Test an empty command string
        command = ''
        expected_output = {'output': '', 'error': 'Invalid command: Command string is empty or whitespace'}
        result = execute_shell_command(command)
        self.assertEqual(result, expected_output, f'Expected {expected_output}, but got {result}')

    def test_whitespace_command(self):
        # Test a command that is just whitespace
        command = '   '
        expected_output = {'output': '', 'error': 'Invalid command: Command string is empty or whitespace'}
        result = execute_shell_command(command)
        self.assertEqual(result, expected_output, f'Expected {expected_output}, but got {result}')

# This allows the tests to be run if this file is executed directly
if __name__ == '__main__':
    unittest.main()