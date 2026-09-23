"""Create a simple single-object illustration for a local smoke test."""

import sys
from pathlib import Path

from PIL import Image, ImageDraw


def main(output: Path) -> None:
    image = Image.new("RGB", (512, 512), "#f6f1e7")
    draw = ImageDraw.Draw(image)
    draw.ellipse((121, 376, 391, 414), fill="#dcd5ca")
    draw.rounded_rectangle((147, 158, 360, 380), radius=38, fill="#d94f43", outline="#782b35", width=9)
    draw.ellipse((166, 146, 341, 188), fill="#fff0d9", outline="#782b35", width=8)
    draw.arc((325, 204, 425, 323), 275, 85, fill="#782b35", width=20)
    draw.arc((337, 215, 411, 307), 275, 85, fill="#d94f43", width=17)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
