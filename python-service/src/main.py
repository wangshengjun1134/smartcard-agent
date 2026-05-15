#!/usr/bin/env python3
"""
Smartcard Knowledge Base Service - Tauri Sidecar Entry Point.

This module provides the entry point for the Python service that runs as a
Tauri sidecar process. It communicates with the main Tauri application via
stdio or HTTP.
"""

import json
import sys
from typing import Any


def process_request(request: dict[str, Any]) -> dict[str, Any]:
    """Process a request from the Tauri application.

    Args:
        request: The request payload from Tauri.

    Returns:
        The response payload to send back to Tauri.
    """
    command = request.get("command", "")

    if command == "ping":
        return {"status": "ok", "message": "pong"}
    elif command == "version":
        return {"status": "ok", "version": "0.1.0"}
    elif command == "query":
        # Placeholder for knowledge base query
        query = request.get("query", "")
        return {"status": "ok", "result": f"Query result for: {query}"}
    else:
        return {"status": "error", "message": f"Unknown command: {command}"}


def main() -> None:
    """Main entry point for the sidecar service.

    Reads JSON requests from stdin and writes JSON responses to stdout.
    """
    # Simple stdio communication loop
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            response = process_request(request)
            print(json.dumps(response), flush=True)
        except json.JSONDecodeError as e:
            error_response = {"status": "error", "message": f"Invalid JSON: {e}"}
            print(json.dumps(error_response), flush=True)


if __name__ == "__main__":
    main()