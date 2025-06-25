#!/usr/bin/env python3
"""
UART Command Sender for CH341 Chip (Modular Version)
Main entry point that uses separated backend and GUI modules
"""

import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from uart_gui import main

if __name__ == "__main__":
    main()