import fspick
import cursesswitch


def main():
    picker = fspick.FilesystemPicker(".", max_depth=30)
    picked_file = picker.pick_one()


cursesswitch.wrapper(main)

