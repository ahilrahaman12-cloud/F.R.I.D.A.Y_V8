"""Tests for workspace-constrained file tools."""

import unittest
from pathlib import Path
from unittest.mock import patch

from core import tools


class WorkspaceToolsTests(unittest.TestCase):
    def test_write_and_list_workspace_file(self):
        test_workspace = Path(__file__).resolve().parents[1] / "workspace"
        with patch.object(tools, "WORKSPACE_DIR", test_workspace):
            result = tools.write_workspace_file("test-output/today.txt", "Hello")
            listing = tools.list_workspace_files("test-output")
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(listing["items"], ["today.txt"])

    def test_parent_directory_escape_is_rejected(self):
        result = tools.write_workspace_file("../outside.txt", "No")
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
