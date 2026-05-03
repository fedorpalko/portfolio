import sys
import os

# Ensure the src directory is in the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from app import TradelabApp

def main():
    """
    Launch the Tradelab TUI application.
    """
    app = TradelabApp()
    app.run()

if __name__ == "__main__":
    main()
