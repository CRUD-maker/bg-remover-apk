import sys
import os

# Fix for "NoneType object has no attribute write" when running with pythonw.exe
# Libraries like tqdm or onnxruntime might try to print to stdout/stderr which are None in windowless mode.
class NullWriter:
    def write(self, text): pass
    def flush(self): pass
    def isatty(self): return False

if sys.stdout is None: sys.stdout = NullWriter()
if sys.stderr is None: sys.stderr = NullWriter()

# Add the directory containing this script to sys.path
# This is required for Embeddable Python to find local modules like 'gui' and 'core'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from gui.mainwindow import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # Optional: Set global font or style
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
