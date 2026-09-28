"""
test_tools.py

Manual test script for mcp_server.py's tool functions, called directly
(bypassing the MCP transport) so you can see diagnose_log and
summarize_failure output with your live GOOGLE_API_KEY without needing
a full MCP client connected yet.

Usage:
    python3 test_tools.py corpus/keyerror_novel_01.log
"""

import sys
import mcp_server as s

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 test_tools.py <path_to_log_file>")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8", errors="replace") as f:
        log_text = f.read()

    print("=" * 70)
    print("get_rare_events")
    print("=" * 70)
    print(s.get_rare_events(log_text))

    print("\n" + "=" * 70)
    print("diagnose_log")
    print("=" * 70)
    print(s.diagnose_log(log_text))

    print("\n" + "=" * 70)
    print("summarize_failure")
    print("=" * 70)
    print(s.summarize_failure(log_text))
