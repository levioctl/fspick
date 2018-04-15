import os

import dirtree
import argparse
import treepicker
import cursesswitch


class FilesystemPicker(object):
    def __init__(self, rootpath, max_depth):
        self._filesystem_tree = dirtree.DirTree.factory_from_filesystem(rootpath, max_depth)
        self._tree_picker = treepicker.TreePicker(self._filesystem_tree, min_nr_options=1, max_nr_options=1)

    def pick_one(self):
        return self._tree_picker.pick_one()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dir", default=".")
    parser.add_argument("-x", "--execute", default=None)
    parser.add_argument("-m", "--max-depth", default=20)
    return parser.parse_args()


picked_file = None


def pick_wrapper(picker):
    global picked_file
    picked_file = picker.pick_one()


def print_picked_file():
    args = parse_args()
    picker = FilesystemPicker(args.dir, args.max_depth)
    global picked_file
    picked_file = picker.pick_one()
    if picked_file is not None:
        if args.execute is not None:
            command = [os.path.basename(args.execute), picked_file.full_filesystem_path()]
            os.execve(args.execute, command, {})
        else:
            cursesswitch.print_line(picked_file.full_filesystem_path())


def main():
    if os.getenv('MODE') == 'direct':
        print_picked_file()
    else:
        cursesswitch.wrapper(print_picked_file)


if __name__ == "__main__":
    main()
