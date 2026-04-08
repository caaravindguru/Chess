# Chess Trainer Setup Guide

## Install Steps for End User
- Install Python 3.8+ — must check "Add Python to PATH" on Windows
- pip install PyQt5 python-chess requests
- Download Stockfish from stockfishchess.org/download — choose correct OS version
- On macOS: `xattr -d com.apple.quarantine /path/to/stockfish && chmod +x /path/to/stockfish`
- Run: `python main.py`
- Go to **Settings** → **Browse for Stockfish...** → select the downloaded binary

## Common Errors
- **ModuleNotFoundError PyQt5** → `pip install PyQt5`
- **ModuleNotFoundError chess** → `pip install python-chess`
- **Engine crashed** → wrong Stockfish build for CPU (download non-AVX2 version)
- **macOS Gatekeeper block** → run `xattr` command above
- **Windows Defender block** → add Stockfish folder to exclusions
- **File not executable** → `chmod +x /path/to/stockfish`
- **Pieces not showing / all black boxes** → install `fonts-symbola` on Linux
- **Analysis slow** → reduce analysis depth in Settings (12 = fast, 20 = deep)
