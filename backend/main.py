"""
Main entry point for the Orbis Ethica backend.
"""

import os
import sys
import uvicorn

def main():
    """
    Main execution function.
    """
    # TODO: Implement argument parsing for CLI vs API mode
    # For now, default to running the API server
    
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"Starting Orbis Ethica Backend on {host}:{port}")
    uvicorn.run("backend.api.app:app", host=host, port=port, reload=True)

if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    main()
