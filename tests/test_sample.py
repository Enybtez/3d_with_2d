import subprocess
import sys

from PIL import Image


def test_sample_script_creates_valid_png(tmp_path):
    output = tmp_path / "cup.png"
    subprocess.run([sys.executable, "examples/make_sample.py", str(output)], check=True)
    with Image.open(output) as image:
        assert image.format == "PNG"
        assert image.size == (512, 512)
