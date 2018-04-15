import os
import shutil
import treelib

import cursesswitch
import findcmdwrapper


class DirEntry(object):
    def __init__(self, name, path, filesystem_dirpath=None):
        self.name = name
        self.dirpath = path
        self.filesystem_dirpath = filesystem_dirpath

    def fullpath(self):
        return os.path.join(self.dirpath, self.name)

    def full_filesystem_path(self):
        return os.path.join(self.filesystem_dirpath, self.name)

    def __repr__(self):
        return self.fullpath()


class FileEntry(object):
    def __init__(self, name, parent_dir_entry):
        self.name = name
        self.dirpath = parent_dir_entry.fullpath()
        self.filesystem_dirpath = parent_dir_entry.full_filesystem_path()

    def __repr__(self):
        return self.fullpath()

    def fullpath(self):
        return os.path.join(self.dirpath, self.name)

    def full_filesystem_path(self):
        return os.path.join(self.filesystem_dirpath, self.name)


MUSIC_FILE_EXTENTIONS = ["mp3", "mp4", "wav", "ogg", "wmv", "wma"]


class DirTree(treelib.Tree):

    def __init__(self, rootpath=None, silent=False):
        super(DirTree, self).__init__()
        self._silent = silent
        self._rootpath = os.path.realpath(rootpath)
        self._root = DirEntry(path=os.path.sep,
                              name=os.path.basename(rootpath),
                              filesystem_dirpath=os.path.dirname(self._rootpath))
        self._root_node = self.create_node(identifier=self._root.dirpath,
                                           tag=self._root.name,
                                           data=self._root)

    @staticmethod
    def factory_from_filesystem(filesystem_dirpath, max_depth=None, file_extentions=None, dirs_only=False,
                                include_hidden=True, silent=False):
        filesystem_dirpath = os.path.realpath(filesystem_dirpath)
        _dirtree = DirTree(filesystem_dirpath, silent)
        _dirtree.update_from_filesystem(max_depth, file_extentions, dirs_only, include_hidden)
        _dirtree.children(_dirtree._root_node.identifier).sort()
        return _dirtree

    @staticmethod
    def factory_from_list_of_file_entries(files, filesystem_dirpath):
        filesystem_dirpath = os.path.realpath(filesystem_dirpath)
        filesystem_basename = os.path.basename(filesystem_dirpath)
        _dirtree = DirTree(filesystem_dirpath)
        for file_entry in files:
            file_first_component, inner_path = file_entry.fullpath().split(os.path.sep, 2)[1:]
            if file_first_component != filesystem_basename:
                raise ValueError("File's first path component must match that of filesystem path",
                                 file_entry, filesystem_dirpath, file_first_component, filesystem_basename)
            inner_dirpath = os.path.dirname(inner_path)
            parent_dir_node = _dirtree._get_dir_node(inner_dirpath)
            _dirtree.create_node(identifier=file_entry.fullpath(),
                                 tag=file_entry.name,
                                 data=file_entry,
                                 parent=parent_dir_node.identifier)
        return _dirtree

    def abs_path_to_inner_path(self, _path):
        rootpath_without_base = self._rootpath[:-len(os.path.basename(self._rootpath)) - 1]
        return _path[len(rootpath_without_base):]

    def update_from_filesystem(self, max_depth=None, file_extentions=None, dirs_only=False,
                               include_hidden=True):
        if not self._silent:
            cursesswitch.print_string("Scanning directory %s..." % (self._rootpath,))
        if not dirs_only:
            entries = findcmdwrapper.find_files(self._rootpath, max_depth, file_extentions, include_hidden)
            inner_paths = [self.abs_path_to_inner_path(entry) for entry in entries]
            non_existent_paths = [filepath for filepath in inner_paths if filepath not in self.nodes]
            for filepath in non_existent_paths:
                self._add_file_by_path(filepath)
        dirnames_fullpath = findcmdwrapper.find_dirs(self._rootpath, max_depth, include_hidden)
        dirnames_inner_path = [self.abs_path_to_inner_path(_dir) for _dir in dirnames_fullpath]
        for dirpath in dirnames_inner_path:
            self._get_dir_node(dirpath)

    def iter_files(self):
        for node in self.nodes.itervalues():
            if isinstance(node.data, FileEntry):
                yield node.data

    def get_unknown_entries_in_given_dirtree(self, other):
        unknown_files_dirtree = DirTree(other._rootpath)
        my_prefix = os.path.basename(self.fullpath())

        def replace_prefix(filename):
            parts = filename.split(os.path.sep)
            parts = [parts[0]] + [my_prefix] + parts[2:]
            return os.path.sep.join(parts)

        unknown_files = [file_entry for file_entry in other.iter_files() if
                         replace_prefix(file_entry.fullpath()) not in self.nodes]

        for _file in unknown_files:
            fullpath = replace_prefix(_file.fullpath())
            unknown_files_dirtree._add_file_by_path(fullpath)
        return unknown_files_dirtree

    def does_dir_contain_any_files(self):
        return any(isinstance(entry, FileEntry) for entry in self.iter_files())

    @staticmethod
    def _remove_prefix_from_path(name, _path):
        prefix = os.path.sep + name + os.path.sep
        assert _path.startswith(prefix)
        relative_path = _path[len(prefix):]
        return relative_path

    def _get_dir_node(self, dirpath):
        parts = dirpath.split(os.path.sep)
        cur_subdir = self._root_node
        for subdir_name in parts[2:]:
            cur_subdir = self._set_default_subdir(parent=cur_subdir, name=subdir_name)
        return cur_subdir

    def copy_inner_entries_from_dirtree(self, dirtree):
        files = list(dirtree.iter_files())
        for index, file_entry in enumerate(files):
            cursesswitch.print_string("Copying %s (%d out of %d)" % (file_entry, index + 1, len(files)))
            new_file_entry = self._add_file_by_path(file_entry.fullpath())
            try:
                if os.path.exists(new_file_entry.filesystem_dirpath):
                    assert os.path.isdir(new_file_entry.filesystem_dirpath)
                else:
                    try:
                        os.makedirs(new_file_entry.filesystem_dirpath)
                    except OSError as ex:
                        cursesswitch.print_string("Copy failed: %s" % (str(ex),), "red")
                        continue
                shutil.copy(file_entry.full_filesystem_path(), new_file_entry.full_filesystem_path())
            except:
                self.remove_node(new_file_entry.fullpath())
                raise

    def get_inner_path_of_entry(self, entry):
        return entry.fullpath()[len(os.path.sep + self._root.name + os.path.sep):]

    def _add_file_by_path(self, filepath):
        dirpath = os.path.dirname(filepath)
        parent_dir_node = self._get_dir_node(dirpath)
        filename = os.path.basename(filepath)
        _file = FileEntry(filename, parent_dir_entry=parent_dir_node.data)
        file_entry = self.create_node(identifier=_file.fullpath(),
                                      tag=_file.name,
                                      data=_file,
                                      parent=parent_dir_node)
        return file_entry.data

    def _set_default_subdir(self, parent, name):
        entry_path = parent.data.fullpath()
        entry_fullpath = os.path.join(entry_path, name)
        node = self.get_node(entry_fullpath)
        if node is None:
            filesystem_dirpath = os.path.join(parent.data.filesystem_dirpath, parent.data.name)
            subdir_entry = DirEntry(name, path=entry_path, filesystem_dirpath=filesystem_dirpath)
            node = self.create_node(identifier=entry_fullpath, tag=name, data=subdir_entry,
                                    parent=parent.identifier)
        return node

    def fullpath(self):
        return self._rootpath

    def __str__(self):
        return self.fullpath()

    def __repr__(self):
        return self.fullpath()

if __name__ == '__main__':
    a = DirTree.factory_from_filesystem('alpha')
    cursesswitch.print_string(a)
