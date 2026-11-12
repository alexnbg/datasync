# datasync

A small Python CLI utility for comparing two folders and syncing the "root" directory into an archive directory.

It scans both directories, identifies modified, new, and deleted files, shows a summary, and asks for confirmation before applying the sync. This is useful for keeping a backup or archive mirror of a source folder without manually copying files.

## What it does

- Recursively scans the source and archive directories
- Detects:
  - modified files
  - newly added files
  - files deleted from the source but still present in the archive
- Copies changed files from the source tree into the archive tree
- Removes files from the archive that no longer exist in the source
- Prompts before making potentially destructive changes
- Can print progress information and create a log file

## Typical use

```bash
python3 datasync.py /path/to/root /path/to/archive
```

If you omit the directory arguments, the script asks for them interactively.

## Command line options

```bash
python3 datasync.py [root_dir] [archive_dir] [-l] [-p]
```

- `root_dir`: the directory you want to treat as the source of truth
- `archive_dir`: the archive or backup directory to sync to
- `-l`, `--log`: create a log file while running
- `-p`, `--print`: print sync progress and summary information

## Example

```bash
python3 datasync.py ~/Documents/project ~/Backups/project --print --log
```

The script will compare the project folder against the backup folder, list the files that differ, and ask before applying the sync.

## Safety checks

The project includes a few safeguards:

- the root and archive directories must not be the same
- it warns before deleting a large share of files from the archive
- it warns before syncing when a large portion of the source files are marked modified
- it asks for confirmation before starting the actual sync

## Notes

This tool is best for simple folder mirroring and backup synchronization. It is not a full-featured synchronization solution for complex multi-source workflows, versioned backups, or conflict resolution.

## Requirements

- Python 3
- standard library modules only (no external dependencies)
