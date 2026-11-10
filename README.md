# UUSEC Rotate Angle

Image matching and angle estimation for UUSEC's rotating puzzle. The script compares a puzzle image with reference images and searches for the most likely rotation.

## How it works

- Reference images are prepared at 360 angles.
- A circular mask keeps only the useful part of each image.
- A coarse search runs every three degrees.
- A second search checks the nearby angles one degree at a time.
- Correlation scores decide the closest image and angle.

Place reference PNG files in the `images/` directory next to the script.

## Setup

```bash
pip install numpy opencv-python pillow playwright
python -m playwright install chromium
```

Set `TARGET` in `rotate_angle.py`, then run:

```bash
python rotate_angle.py
```

For security research and authorized testing only.
