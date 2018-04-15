# fspick
A Shell-based interactive search picker of files and/or directories.

## Demo
[![asciicast](https://asciinema.org/a/176283.png)](https://asciinema.org/a/176283)

## Usage
```python
import fspick
import cursesswitch


def main():
    picker = fspick.FilesystemPicker(".", max_depth=30)
    picked_file = picker.pick_one()


cursesswitch.wrapper(main)
```
