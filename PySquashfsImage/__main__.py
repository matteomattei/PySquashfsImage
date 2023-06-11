#!/usr/bin/env python

import argparse
import os
import posixpath
import sys
from datetime import datetime

from . import SquashFsImage
from .extract import extract_dir, extract_file
from .file import BlockDevice, CharacterDevice

ROOT = posixpath.sep


def extract(args):
    with SquashFsImage.from_file(args.file, args.offset) as image:
        file = image.select(args.path)
        if file is None:
            raise Exception("{} not found".format(args.path))
        parent = args.dest or ''
        basename = os.path.basename(file.path) or "squashfs-root"
        dest = os.path.join(parent, basename)
        dirname = os.path.dirname(dest)
        if dirname and not os.path.isdir(dirname):
            os.makedirs(dirname)
        if file.is_dir:
            extract_dir(file, dest, args.force, quiet=args.quiet)
        else:
            extract_file(file, dest, args.force, quiet=args.quiet)


def print_file(file):
    width = 25 - len(str(file.uid)) - len(str(file.gid))
    if isinstance(file, (BlockDevice, CharacterDevice)):
        width = max(0, width - 7)
        data = "{:{width}}{:3d},{:3d}".format(' ', file.major, file.minor, width=width)
    else:
        width = max(0, width)
        data = "{:{width}}".format(file.inode.data, width=width)
    print("{} {}/{} {} {} {}".format(
        file.filemode,
        file.uid,
        file.gid,
        data,
        datetime.fromtimestamp(file.inode.time),  # TODO: Add UTC when Python 3 only
        file.path
    ) + (" -> {}".format(file.readlink()) if file.is_symlink else ''))


def list_(args):
    types = args.type
    if types is not None:
        types = set(''.join(types).replace('f', '-'))
    count = 0
    with SquashFsImage.from_file(args.file, args.offset) as image:
        file = image.select(args.path)
        if file is None:
            raise Exception("{} not found".format(args.path))
        if not file.is_dir:
            print_file(file)
            return
        recursive = not args.recursive if args.path == ROOT else args.recursive
        directory = file.riter() if recursive else file
        if types is None:
            for file in directory:
                print_file(file)
                count += 1
        else:
            for file in directory:
                if file.filemode[0] in types:
                    print_file(file)
                    count += 1
    print("{} file(s) found".format(count))


def main():
    parser = argparse.ArgumentParser(description="Print information about squashfs images.")
    parser.add_argument("-V", "--version", action="version", version="%(prog)s v0.8.0")
    subparsers = parser.add_subparsers()  # TODO: required=True Python 3

    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("file", help="squashfs filesystem")
    parent.add_argument("-o", "--offset", type=int, default=0, help="absolute position of file system's start. Default: %(default)s")

    helplist = "List the contents of the file system"
    parser_l = subparsers.add_parser("list", parents=[parent], help=helplist.lower(), description=helplist)
    parser_l.add_argument("-p", "--path", default=ROOT, help="absolute path of directory or file to list. Default: %(default)r")
    parser_l.add_argument("-r", "--recursive", action="store_true", help="whether to list recursively. For the root directory the value is inverted. Default: %(default)s")
    parser_l.add_argument("-t", "--type", nargs='+', metavar="TYPE", choices=list("fdlpsbc"), help="when listing a directory, filter by file type with %(choices)s")
    parser_l.set_defaults(func=list_)

    helpextr = "Extract files from the file system"
    parser_e = subparsers.add_parser("extract", parents=[parent], help=helpextr.lower(), description=helpextr)
    parser_e.add_argument("-d", "--dest", help="directory that will contain the extracted file(s). If it doesn't exist it will be created. Default: current directory")
    parser_e.add_argument("-p", "--path", default=ROOT, help="absolute path of directory or file to extract. Default: %(default)r")
    parser_e.add_argument("-f", "--force", action="store_true", help="overwrite files that already exist. Default: %(default)s")
    parser_e.add_argument("-q", "--quiet", action="store_true", help="don't print extraction status. Default: %(default)s")
    parser_e.set_defaults(func=extract)

    args = parser.parse_args()
    if "file" not in args:
        parser.error("the following arguments are required: subcommand")
    if not os.path.isfile(args.file):
        sys.exit("error: file does not exist")
    if not posixpath.isabs(args.path):
        sys.exit("error: path is not absolute")
    if "offset" in args and args.offset is not None and args.offset < 0:
        sys.exit("error: offset cannot be negative")

    try:
        args.func(args)
    except Exception as e:
        sys.exit("error: {}".format(e))


if __name__ == "__main__":
    main()
