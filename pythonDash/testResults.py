#!/usr/bin/env python3
"""
Test Results Handler - Captures test output and generates HTML reports
"""

import datetime
import os
from typing import List, Tuple


class TestResults:
    """Handles capturing test output and generating HTML reports"""

    def __init__(self, title="Test Results"):
        self.title = title
        self.start_time = datetime.datetime.now()
        self.end_time = None
        self.output_lines = []
        self.tests = []  # List of (test_name, passed, output_lines)
        self.current_test_name = None
        self.current_test_output = []

    def start_test(self, test_name):
        """Start capturing output for a new test"""
        if self.current_test_name:
            # Save previous test
            self._save_current_test(None)

        self.current_test_name = test_name
        self.current_test_output = []

    def end_test(self, test_name, passed):
        """End the current test and record its result"""
        if self.current_test_name == test_name:
            self._save_current_test(passed)

    def _save_current_test(self, passed):
        """Save the current test to the tests list"""
        if self.current_test_name:
            self.tests.append((
                self.current_test_name,
                passed,
                self.current_test_output.copy()
            ))
            self.current_test_name = None
            self.current_test_output = []

    def print(self, message=""):
        """Print to console and capture for HTML report"""
        print(message)
        self.output_lines.append(message)
        if self.current_test_name:
            self.current_test_output.append(message)

    def finalize(self):
        """Finalize the test run"""
        self.end_time = datetime.datetime.now()
        if self.current_test_name:
            self._save_current_test(None)

    def generate_html(self, output_file="test_results.html"):
        """Generate an HTML report of the test results"""
        self.finalize()

        duration = (self.end_time - self.start_time).total_seconds()
        passed_count = sum(1 for _, passed, _ in self.tests if passed)
        total_count = len(self.tests)

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{self.title}</title>
    <style>
        body {{
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            background-color: #1a1a1a;
            color: #e0e0e0;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            color: #4CAF50;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }}
        .summary {{
            background-color: #2a2a2a;
            border-left: 4px solid #4CAF50;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .summary.failed {{
            border-left-color: #f44336;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 10px;
        }}
        .summary-item {{
            background-color: #333;
            padding: 10px;
            border-radius: 4px;
        }}
        .summary-label {{
            color: #888;
            font-size: 0.9em;
        }}
        .summary-value {{
            color: #fff;
            font-size: 1.2em;
            font-weight: bold;
            margin-top: 5px;
        }}
        .test {{
            background-color: #2a2a2a;
            margin: 15px 0;
            border-radius: 4px;
            overflow: hidden;
        }}
        .test-header {{
            padding: 15px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .test-header:hover {{
            background-color: #333;
        }}
        .test.passed .test-header {{
            border-left: 4px solid #4CAF50;
        }}
        .test.failed .test-header {{
            border-left: 4px solid #f44336;
        }}
        .test.unknown .test-header {{
            border-left: 4px solid #ff9800;
        }}
        .test-name {{
            font-weight: bold;
            font-size: 1.1em;
        }}
        .test-status {{
            padding: 5px 15px;
            border-radius: 3px;
            font-weight: bold;
        }}
        .test.passed .test-status {{
            background-color: #4CAF50;
            color: white;
        }}
        .test.failed .test-status {{
            background-color: #f44336;
            color: white;
        }}
        .test.unknown .test-status {{
            background-color: #ff9800;
            color: white;
        }}
        .test-output {{
            padding: 15px;
            background-color: #1a1a1a;
            border-top: 1px solid #444;
            display: none;
            max-height: 500px;
            overflow-y: auto;
        }}
        .test.expanded .test-output {{
            display: block;
        }}
        .test-output pre {{
            margin: 0;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .success {{
            color: #4CAF50;
        }}
        .fail {{
            color: #f44336;
        }}
        .warning {{
            color: #ff9800;
        }}
        .separator {{
            color: #666;
        }}
        .timestamp {{
            color: #888;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{self.title}</h1>

        <div class="summary {'failed' if passed_count < total_count else ''}">
            <div class="summary-grid">
                <div class="summary-item">
                    <div class="summary-label">Start Time</div>
                    <div class="summary-value timestamp">{self.start_time.strftime('%Y-%m-%d %H:%M:%S')}</div>
                </div>
                <div class="summary-item">
                    <div class="summary-label">Duration</div>
                    <div class="summary-value">{duration:.2f}s</div>
                </div>
                <div class="summary-item">
                    <div class="summary-label">Tests Passed</div>
                    <div class="summary-value {'success' if passed_count == total_count else 'fail'}">
                        {passed_count} / {total_count}
                    </div>
                </div>
                <div class="summary-item">
                    <div class="summary-label">Success Rate</div>
                    <div class="summary-value {'success' if passed_count == total_count else 'fail'}">
                        {(passed_count/total_count*100) if total_count > 0 else 0:.1f}%
                    </div>
                </div>
            </div>
        </div>

        <h2>Test Details</h2>
"""

        # Add individual test results
        for test_name, passed, output in self.tests:
            status_class = "passed" if passed is True else ("failed" if passed is False else "unknown")
            status_text = "PASS" if passed is True else ("FAIL" if passed is False else "UNKNOWN")

            html += f"""
        <div class="test {status_class}">
            <div class="test-header" onclick="this.parentElement.classList.toggle('expanded')">
                <span class="test-name">{test_name}</span>
                <span class="test-status">{status_text}</span>
            </div>
            <div class="test-output">
                <pre>{self._format_output(output)}</pre>
            </div>
        </div>
"""

        html += """
    </div>
    <script>
        // Expand failed tests by default
        document.querySelectorAll('.test.failed').forEach(test => {
            test.classList.add('expanded');
        });
    </script>
</body>
</html>
"""

        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        return output_file

    def _format_output(self, lines):
        """Format output lines with HTML styling"""
        formatted = []
        for line in lines:
            # Apply color classes based on content
            if '✓' in line or 'SUCCESS' in line:
                formatted.append(f'<span class="success">{self._html_escape(line)}</span>')
            elif '✗' in line or 'FAIL' in line or 'EXCEPTION' in line:
                formatted.append(f'<span class="fail">{self._html_escape(line)}</span>')
            elif '⚠' in line or 'WARNING' in line:
                formatted.append(f'<span class="warning">{self._html_escape(line)}</span>')
            elif '=' in line and len(set(line.replace(' ', ''))) <= 2:
                formatted.append(f'<span class="separator">{self._html_escape(line)}</span>')
            else:
                formatted.append(self._html_escape(line))

        return '\n'.join(formatted)

    def _html_escape(self, text):
        """Escape HTML special characters"""
        return (str(text)
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))


# Example usage
if __name__ == "__main__":
    results = TestResults("Example Test Suite")

    results.print("Starting test suite...")
    results.print()

    results.start_test("test_example_pass")
    results.print("="*60)
    results.print("TEST: Example Passing Test")
    results.print("="*60)
    results.print("✓ SUCCESS: This test passed")
    results.end_test("test_example_pass", True)

    results.start_test("test_example_fail")
    results.print("="*60)
    results.print("TEST: Example Failing Test")
    results.print("="*60)
    results.print("✗ FAILED: This test failed")
    results.end_test("test_example_fail", False)

    results.start_test("test_example_warning")
    results.print("="*60)
    results.print("TEST: Example Warning Test")
    results.print("="*60)
    results.print("⚠ WARNING: This is a warning")
    results.end_test("test_example_warning", True)

    output_file = results.generate_html("example_results.html")
    results.print(f"\nHTML report generated: {output_file}")
