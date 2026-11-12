#!/usr/bin/python3

import os
import pathlib
import shutil
import argparse
import time
from datetime import datetime
from typing import List, Dict, Callable
from pprint import pprint

import logging

# TODO if the paths are wrong
# if 0 files in root and/or 0 files in archive

# TODO add variable for printning information or not, also for print all infor or minimal info

# TODO add variable for making a log file

# TODO make the arg for log file to be the path to the log file - if posible like that:
# -l             = log with default file name
# -l path/name   = log with specified file name and path

# TODO log system

# TODO check if paths are real paths


# TODO PathSync - add folder tree sync
# now if there are deleted folders, they will remain in the archive
# also if there are new empty folders, they will not be created in the archive

# TODO PathSync - remove os and shutil and use only pathlib


ARCHIVE_FILES_FOR_DELETION_PERCENT_CHECK: int = 50
ROOT_FILES_MODIFIED_PERCENT_CHECK: int = 50


def printlog(fn):
    def wrapper(*args, **kwargs):
        print_log = kwargs['print_log']
        root_dir = kwargs['root_path']
        file_name = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{pathlib.Path(root_dir).name}.txt"

        def printlog(message: str = '', minimal: bool = False, pp: bool = False) -> None:
            with open(file_name, 'a') as f:
                if (minimal and pp) or (print_log and pp):
                    pprint(message)
                    f.writelines([str(message), '\n'])
                elif minimal or print_log:
                    print(message)
                    f.writelines([str(message), '\n'])
                else:
                    f.writelines([str(message), '\n'])

        fn(*args, **kwargs, printlog=printlog)
    return wrapper


@printlog
def program(root_path: str = None,
            archive_path: str = None,
            save_log: bool = False,
            print_log: bool = False,
            printlog: Callable = None,
            ) -> None:
    rows = '='*50
    printlog(rows)

    # Check if paths are specified
    if root_path is None and archive_path is None:
        root_path = input("Enter root path: ")
        archive_path = input("Enter archive path: ")
    elif (root_path is None and archive_path is not None) or (root_path is not None and archive_path is None):
        raise ValueError("Root and archive paths must be both specified!")

    # Read the data
    printlog()
    printlog('Start reading files...')
    start_time_ext = time.time()

    path_sync = PathSync(root_path, archive_path)
    path_sync.get_data()

    time_ext = int(time.time() - start_time_ext)

    # Print number of files in root and archive directories
    root_files_num = len(path_sync.root_files['files'])
    archive_files_num = len(path_sync.archive_files['files'])
    printlog()
    if time_ext > 1:
        printlog(f'Reading files completed in {time_ext} seconds')
    printlog(r'Files in {path}: {num}'.format(path=root_path, num=root_files_num))
    printlog(r'Files in {path}: {num}'.format(path=archive_path, num=archive_files_num))
    printlog()

    # Check if there are files in root and archive directories
    if root_files_num == 0 and archive_files_num == 0:
        printlog('No files in root and archive directories', True)
        printlog(rows)
        return
    elif root_files_num == 0:
        printlog('No files in root directory', True)
        printlog(rows)
        return
    elif archive_files_num == 0:
        printlog('The archive directory is empty', True)
        if not _input_continue('Continue? (y): '):
            printlog(rows)
            return

    # Compare files
    modified_files = [file.__str__() for file in path_sync.modified_files]
    new_files = [file.__str__() for file in path_sync.new_files]
    deleted_files = [file.__str__() for file in path_sync.deleted_files]
    num_all = len(modified_files) + len(new_files) + len(deleted_files)

    if modified_files:
        printlog('Modified files: {num}'.format(num=len(modified_files)))
        printlog(modified_files, False, True)
    if new_files:
        printlog('New files: {num}'.format(num=len(new_files)))
        printlog(new_files, False, True)
    if deleted_files:
        printlog('Deleted files: {num}'.format(num=len(deleted_files)))
        printlog(deleted_files, False, True)

    # Check compared files
    if len(deleted_files) == archive_files_num:
        printlog('All files in archive directory will be deleted!', True)
        if not _input_continue('Continue? (y): '):
            printlog('Sync aborted', True)
            printlog(rows)
            return
    elif len(deleted_files)/archive_files_num > ARCHIVE_FILES_FOR_DELETION_PERCENT_CHECK:
        printlog('More than {percent}% of files in archive directory will be deleted!'.format(
            percent=ARCHIVE_FILES_FOR_DELETION_PERCENT_CHECK), True)
        if not _input_continue('Continue? (y): '):
            printlog('Sync aborted', True)
            printlog(rows)
            return
    if len(modified_files)/root_files_num > ROOT_FILES_MODIFIED_PERCENT_CHECK:
        printlog('More than {percent}% of files in root directory are modified!'.format(
            percent=ROOT_FILES_MODIFIED_PERCENT_CHECK), True)
        if not _input_continue('Continue? (y): '):
            printlog('Sync aborted', True)
            printlog(rows)
            return

    # Sync data
    if not (modified_files or new_files or deleted_files):
        printlog('No changes detected', True)
    else:
        printlog()
        if _input_continue(f"Start sync {num_all} files? (y): "):
            printlog()
            printlog('Starting sync...')

            start_time_sync = time.time()
            path_sync.sync_data()
            time_sync = int(time.time() - start_time_sync)

            printlog()
            if time_sync > 1:
                printlog(f'Data sync completed in {time} seconds!'.format(time=time_sync))
            else:
                printlog(f'{num_all} files sync completed successfully!', True)
        else:
            printlog()
            printlog('Sync aborted', True)
    printlog(rows)


def _input_continue(message: str, agree_continue: List[str] = ['y', '']) -> bool:
    user_input = input(message)
    return any([user_input.lower() == agree for agree in agree_continue])


def _input_till_correct(message: str, default: str = None) -> str:
    while True:
        user_input = input(message)
        if user_input == '':
            if default is not None:
                return default
        else:
            return user_input


class PathSync:
    def __init__(self,
                 root_path: str,
                 archive_path: str,
                 ) -> None:
        self.root_path = root_path
        self.archive_path = archive_path
        if root_path == archive_path:
            raise ValueError("Root and archive paths must be different")
        self.root_files = None
        self.archive_files = None
        self.modified_files = None
        self.new_files = None

    def sync_data(self) -> None:
        if self.root_files is None or self.archive_files is None:
            self.get_data()

        # Replace modified files
        for file in self.modified_files:
            mod_file_root_path = file.__str__()
            mod_file_archive_path_dir = os.path.dirname(self._new_path(file, self.root_path, self.archive_path))
            if not os.path.exists(mod_file_archive_path_dir):
                os.makedirs(mod_file_archive_path_dir)
            shutil.copy2(mod_file_root_path, mod_file_archive_path_dir)

        # Copy new files
        for file in self.new_files:
            new_file_root_path = file.__str__()
            new_file_archive_path_dir = os.path.dirname(self._new_path(file, self.root_path, self.archive_path))
            if not os.path.exists(new_file_archive_path_dir):
                os.makedirs(new_file_archive_path_dir)
            shutil.copy2(new_file_root_path, new_file_archive_path_dir)

        # Remove deleted files
        for file in self.deleted_files:
            del_file_archive_path = file.__str__()
            os.remove(del_file_archive_path)
            # pathlib.Path(del_file_archive_path).unlink()

    def get_data(self) -> None:
        self.root_files = self._get_files(self.root_path)
        self.archive_files = self._get_files(self.archive_path)
        self.modified_files = self._get_modified_files()
        self.new_files = self._get_new_files()
        self.deleted_files = self._get_deleted_files()

    def _get_files(self, path: str) -> Dict[str, List[pathlib.Path]]:
        path = r'{}'.format(path)
        return {'path': pathlib.Path(path),
                'files': [pathlib.Path(f) for f in pathlib.Path(path).glob('**/*') if f.is_file()]}

    def _get_modified_files(self) -> List[pathlib.Path]:
        result = []
        for file_root in self.root_files['files']:
            file_root_relative_path = self._relative_path(file_root, self.root_files['path'])
            for file_arch in self.archive_files['files']:
                file_arch_relative_path = self._relative_path(file_arch, self.archive_files['path'])
                if file_root_relative_path == file_arch_relative_path \
                        and (file_root.stat().st_size != file_arch.stat().st_size or file_root.stat().st_mtime != file_arch.stat().st_mtime):
                    result.append(file_root)
        return result

    def _get_new_files(self) -> List[pathlib.Path]:
        archive_files_relative_paths = [self._relative_path(
            file, self.archive_files['path']) for file in self.archive_files['files']]
        result = []
        for file_root in self.root_files['files']:
            file_root_relative_path = self._relative_path(file_root, self.root_files['path'])
            if file_root_relative_path not in archive_files_relative_paths:
                result.append(file_root)
        return result

    def _get_deleted_files(self) -> List[pathlib.Path]:
        root_files_relative_paths = [self._relative_path(file, self.root_files['path'])
                                     for file in self.root_files['files']]
        result = []
        for file_arch in self.archive_files['files']:
            file_arch_relative_path = self._relative_path(file_arch, self.archive_files['path'])
            if file_arch_relative_path not in root_files_relative_paths:
                result.append(file_arch)
        return result

    def _relative_path(self, file: pathlib.Path, base: pathlib.Path) -> str:
        return file.__str__().replace(base.__str__(), '')

    def _new_path(self, file: pathlib.Path, base: pathlib.Path, new_base: pathlib.Path) -> str:
        return file.__str__().replace(base.__str__(), new_base.__str__())


def main(command_line=None):
    parser = argparse.ArgumentParser(description='Sync data between two directories')
    parser.add_argument('root_dir', metavar='root', type=str, nargs='?', default=None,
                        help='root directory with new data')
    parser.add_argument('archive_dir', metavar='archive', type=str, nargs='?', default=None,
                        help='destination directory with archive data')
    parser.add_argument('-l', '--log', action='store_true',
                        help='create log file')
    parser.add_argument('-p', '--print', action='store_true',
                        help='print information while running')

    args = parser.parse_args(command_line)

    root_path = args.root_dir
    archive_path = args.archive_dir
    if args.root_dir is None and args.archive_dir is None:
        root_path = _input_till_correct("Enter root directory path: ")
        archive_path = _input_till_correct("Enter archive directory path: ")
    elif args.root_dir is not None and args.archive_dir is None:
        root_path = _input_till_correct(f"Enter root directory path ({root_path}): ", root_path)
        archive_path = _input_till_correct("Enter archive directory path: ")

    # Run main program
    program(root_path=root_path,
            archive_path=archive_path,
            save_log=args.log,
            print_log=args.print)


if __name__ == '__main__':
    main()
