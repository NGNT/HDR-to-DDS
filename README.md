# Teardown Skybox Converter

A modern Python GUI tool for converting HDR skybox images to DDS cubemaps for use in [Teardown](https://teardowngame.com/) and other 3D applications.  
This tool wraps the [cmft](https://github.com/dariomanesku/cmft) utility with a user-friendly interface, allowing you to easily configure conversion parameters and generate optimized skybox textures.

## Features

- Intuitive, modern Tkinter interface
- Customizable conversion parameters (filter, mip count, gloss, lighting model, etc.)
- Tooltips for all options
- Debug output and status reporting
- One-click conversion to DDS cubemap format
- Requires `cmft.exe` in the same directory

## Requirements

- Python 3.8+
- [Pillow](https://pypi.org/project/Pillow/) (`pip install pillow`)
- `cmft.exe` (Download from [cmft releases](https://github.com/dariomanesku/cmft/releases) and place in the script directory)
- Windows OS (for `cmft.exe` and GUI)

## Installation

1. Clone this repository or download the script.
2. Install dependencies:
```
pip install pillow
```
3. Ensure `cmft.exe` is present in the same folder as `teardown_skybox_gui.py` (already included).

---

## Usage

1. Run the script:
```
python teardown_skybox_gui.py
```
2. Use the GUI to select your HDR file, set the output name, and adjust conversion parameters as needed.
3. Click **Convert** to generate your DDS cubemap.

---

## Notes

- Output files are saved in the same directory as the script.
- For best results, use high-quality HDR images as input.

---

## License

This project is provided under the MIT License. See [LICENSE](LICENSE) for details.

---

*Teardown is a trademark of Tuxedo Labs. This project is not affiliated with or endorsed by Tuxedo Labs.*