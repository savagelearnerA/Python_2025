import sys
from pathlib import Path


sys.path.append(str(Path(__file__).parent))


from batch_image_processor import ImageProcessorGUI

if __name__ == "__main__":
    app = ImageProcessorGUI()
    app.mainloop()