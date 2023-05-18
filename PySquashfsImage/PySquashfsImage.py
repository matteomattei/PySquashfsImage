#!/usr/bin/env python

# -*- coding: utf-8 -*-

"""
This module is released with the LGPL license.
Copyright 2011-2012

Matteo Mattei <matteo.mattei@gmail.com>
Nicola Ponzeveroni <nicola.ponzeveroni@gilbarco.com>

It is intended to be used to access files into a SQUASHFS 4.0 image file.

Based on Phillip Lougher <phillip@lougher.demon.co.uk> Unsquash tool

https://github.com/matteomattei/PySquashfsImage
http://squashfs.sourceforge.net/

"""
__all__ = ["SquashFsImage"]

import io
import stat
import struct
import sys
import warnings
from ctypes import sizeof

from .const import Type
from .file import Directory, filetype
from .structure import DirEntry, DirHeader
from .structure.inode import InodeHeader, inomap

SQUASHFS_CHECK = 2

SQUASHFS_UIDS = 256
SQUASHFS_GUIDS = 255

NO_COMPRESSION = 0
ZLIB_COMPRESSION = 1
LZMA_COMPRESSION = 2
LZO_COMPRESSION = 3
XZ_COMPRESSION = 4
LZ4_COMPRESSION = 5
ZSTD_COMPRESSION = 6

SQUASHFS_MAJOR = 4
SQUASHFS_MINOR = 0
SQUASHFS_MAGIC = 0x73717368
SQUASHFS_START = 0

SQUASHFS_METADATA_SIZE = 8192
SQUASHFS_METADATA_LOG = 13

FRAGMENT_BUFFER_DEFAULT = 256
DATA_BUFFER_DEFAULT = 256

SQUASHFS_NAME_LEN = 256
SQUASHFS_INVALID = 0xFFFFFFFFFFFF
SQUASHFS_INVALID_FRAG = 0xFFFFFFFF
SQUASHFS_INVALID_XATTR = 0xFFFFFFFF
SQUASHFS_INVALID_BLK = 0xFFFFFFFFFFFFFFFF  # -1
SQUASHFS_USED_BLK = SQUASHFS_INVALID_BLK - 1  # -2

# ****** MACROS
SQUASHFS_COMPRESSED_BIT = 1 << 15
SQUASHFS_COMPRESSED_BIT_BLOCK = 1 << 24


def SQUASHFS_COMPRESSED_SIZE(B):
    if B & ~SQUASHFS_COMPRESSED_BIT:
        return B & ~SQUASHFS_COMPRESSED_BIT
    else:
        return SQUASHFS_COMPRESSED_BIT


def SQUASHFS_BIT(flag, bit):
    return ((flag >> bit) & 1) != 0


def SQUASHFS_CHECK_DATA(flags):
    return SQUASHFS_BIT(flags, SQUASHFS_CHECK)


def SQUASHFS_COMPRESSED(B):
    return (B & SQUASHFS_COMPRESSED_BIT) == 0


def SQUASHFS_COMPRESSED_SIZE_BLOCK(B):
    return B & ~SQUASHFS_COMPRESSED_BIT_BLOCK


def SQUASHFS_COMPRESSED_BLOCK(B):
    return (B & SQUASHFS_COMPRESSED_BIT_BLOCK) == 0


def SQUASHFS_INODE_BLK(a):
    return (a >> 16) & 0xFFFFFFFF


def SQUASHFS_INODE_OFFSET(a):
    return a & 0xFFFF


def SQUASHFS_MKINODE(A, B):
    return ((A << 16) + B) & 0xFFFFFFFFFFFFFFFF


def SQUASHFS_MK_VFS_INODE(a, b):
    return ((a << 8) + (b >> 2) + 1) & 0xFFFFFFFF


def SQUASHFS_MODE(a):
    return a & 0xFFF


def SQUASHFS_FRAGMENT_BYTES(A):
    return A * 16


def SQUASHFS_FRAGMENT_INDEX(A):
    return SQUASHFS_FRAGMENT_BYTES(A) // SQUASHFS_METADATA_SIZE


def SQUASHFS_FRAGMENT_INDEX_OFFSET(A):
    return SQUASHFS_FRAGMENT_BYTES(A) % SQUASHFS_METADATA_SIZE


def SQUASHFS_FRAGMENT_INDEXES(A):
    return (SQUASHFS_FRAGMENT_BYTES(A) + SQUASHFS_METADATA_SIZE - 1) // SQUASHFS_METADATA_SIZE


def SQUASHFS_FRAGMENT_INDEX_BYTES(A):
    return SQUASHFS_FRAGMENT_INDEXES(A) * 8


def SQUASHFS_LOOKUP_BYTES(A):
    return A * 8


def SQUASHFS_LOOKUP_BLOCK(A):
    return SQUASHFS_LOOKUP_BYTES(A) // SQUASHFS_METADATA_SIZE


def SQUASHFS_LOOKUP_BLOCK_OFFSET(A):
    return SQUASHFS_LOOKUP_BYTES(A) % SQUASHFS_METADATA_SIZE


def SQUASHFS_LOOKUP_BLOCKS(A):
    return (SQUASHFS_LOOKUP_BYTES(A) + SQUASHFS_METADATA_SIZE - 1) // SQUASHFS_METADATA_SIZE


def SQUASHFS_LOOKUP_BLOCK_BYTES(A):
    return SQUASHFS_LOOKUP_BLOCKS(A) * 8


def SQUASHFS_ID_BYTES(A):
    return A * 4


def SQUASHFS_ID_BLOCK(A):
    return SQUASHFS_ID_BYTES(A) // SQUASHFS_METADATA_SIZE


def SQUASHFS_ID_BLOCK_OFFSET(A):
    return SQUASHFS_ID_BYTES(A) % SQUASHFS_METADATA_SIZE


def SQUASHFS_ID_BLOCKS(A):
    return (SQUASHFS_ID_BYTES(A) + SQUASHFS_METADATA_SIZE - 1) // SQUASHFS_METADATA_SIZE


def SQUASHFS_ID_BLOCK_BYTES(A):
    return SQUASHFS_ID_BLOCKS(A) * 8


def SQUASHFS_XATTR_BYTES(A):
    return A * 16


def SQUASHFS_XATTR_BLOCK(A):
    return SQUASHFS_XATTR_BYTES(A) // SQUASHFS_METADATA_SIZE


def SQUASHFS_XATTR_BLOCK_OFFSET(A):
    return SQUASHFS_XATTR_BYTES(A) % SQUASHFS_METADATA_SIZE


def SQUASHFS_XATTR_BLOCKS(A):
    return (SQUASHFS_XATTR_BYTES(A) + SQUASHFS_METADATA_SIZE - 1) // SQUASHFS_METADATA_SIZE


def SQUASHFS_XATTR_BLOCK_BYTES(A):
    return SQUASHFS_XATTR_BLOCKS(A) * 8


def SQUASHFS_XATTR_BLK(A):
    return (A >> 16) & 0xFFFFFFFF


def SQUASHFS_XATTR_OFFSET(A):
    return A & 0xFFFF


SQUASHFS_LOOKUP_TYPE = [
    0,
    stat.S_IFDIR,
    stat.S_IFREG,
    stat.S_IFLNK,
    stat.S_IFBLK,
    stat.S_IFCHR,
    stat.S_IFIFO,
    stat.S_IFSOCK,
    stat.S_IFDIR,
    stat.S_IFREG,
    stat.S_IFLNK,
    stat.S_IFBLK,
    stat.S_IFCHR,
    stat.S_IFIFO,
    stat.S_IFSOCK
]


class _Compressor:
    name = "none"

    def uncompress(self, src):
        return src


class _ZlibCompressor(_Compressor):
    name = "zlib"

    def __init__(self):
        import zlib
        self._lib = zlib

    def uncompress(self, src):
        return self._lib.decompress(src)


class _XZCompressor(_Compressor):
    name = "xz"

    def __init__(self):
        try:
            import lzma  # Python 3.3+
        except ImportError:
            from backports import lzma
        self._lib = lzma

    def uncompress(self, src):
        return self._lib.decompress(src)


class _LZ4Compressor(_Compressor):
    name = "lz4"

    def __init__(self):
        import lz4.frame
        self._lib = lz4.frame

    def uncompress(self, src):
        return self._lib.decompress(src)


class _ZSTDCompressor(_Compressor):
    name = "zstd"

    def __init__(self):
        import zstandard
        self._lib = zstandard.ZstdDecompressor()

    def uncompress(self, src):
        return self._lib.decompress(src)


_compressors = {
    NO_COMPRESSION: _Compressor,
    ZLIB_COMPRESSION: _ZlibCompressor,
    XZ_COMPRESSION: _XZCompressor,
    LZ4_COMPRESSION: _LZ4Compressor,
    ZSTD_COMPRESSION: _ZSTDCompressor
}


class _SquashfsCommons(object):  # Explicit new-style class for Python 2

    def read(self, myfile):
        """Set values read from a file object."""
        values = struct.unpack(self.FORMAT, myfile.read(self.SIZE))
        for field, value in zip(self.FIELDS, values):
            setattr(self, field, value)

    @classmethod
    def from_bytes(cls, buffer, offset=0):
        inst = cls()
        values = struct.unpack_from(cls.FORMAT, buffer, offset)
        for field, value in zip(cls.FIELDS, values):
            setattr(inst, field, value)
        return inst


class _SquashfsSuperBlock(_SquashfsCommons):

    FORMAT = "<IIIIIHHHHHHQQQQQQQQ"
    SIZE = struct.calcsize(FORMAT)
    FIELDS = [
        "s_magic", "inodes", "mkfs_time", "block_size", "fragments", "compression",
        "block_log", "flags", "no_ids", "s_major", "s_minor", "root_inode",
        "bytes_used", "id_table_start", "xattr_id_table_start", "inode_table_start",
        "directory_table_start", "fragment_table_start", "lookup_table_start"
    ]

    def __init__(self):
        self.s_magic = 0
        self.inodes = 0
        self.mkfs_time = 0
        self.block_size = 0
        self.fragments = 0
        self.compression = 0
        self.block_log = 0
        self.flags = 0
        self.no_ids = 0
        self.s_major = 0
        self.s_minor = 0
        self.root_inode = 0
        self.bytes_used = 0
        self.id_table_start = 0
        self.xattr_id_table_start = 0
        self.inode_table_start = 0
        self.directory_table_start = 0
        self.fragment_table_start = 0
        self.lookup_table_start = 0


class _SquashfsFragmentEntry(_SquashfsCommons):

    FORMAT = "<QII"
    SIZE = struct.calcsize(FORMAT)
    FIELDS = ["start_block", "size", "unused"]

    def __init__(self):
        self.start_block = 0
        self.size = 0
        self.unused = 0
        self.fragment = None


class _XattrId(_SquashfsCommons):  # 16

    FORMAT = "<QII"
    SIZE = struct.calcsize(FORMAT)
    FIELDS = ["xattr", "count", "size"]

    def __init__(self):
        self.xattr = 0
        self.count = 0
        self.size = 0


class _XattrTable(_SquashfsCommons):

    FORMAT = "<QII"
    SIZE = struct.calcsize(FORMAT)
    FIELDS = ["xattr_table_start", "xattr_ids", "unused"]

    def __init__(self):
        self.xattr_table_start = 0
        self.xattr_ids = 0
        self.unused = 0


class SquashFsImage(object):

    def __init__(self, filepath=None, offset=0):
        self.comp = None
        self.sBlk = _SquashfsSuperBlock()
        self.fragment_buffer_size = FRAGMENT_BUFFER_DEFAULT
        self.data_buffer_size = DATA_BUFFER_DEFAULT
        self.block_size = 0
        self.block_log = 0
        self.all_buffers_size = 0
        self.fragment_table = []
        self.inode_table_hash = {}
        self.id_table = {}
        self.hash_table = {}
        self.xattrs = b""
        self.directory_table_hash = {}
        self._root = None
        self._image_file = None
        self.offset = offset
        if filepath is not None:
            self.open(filepath)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def __iter__(self):
        return self._root.riter()

    @property
    def root(self):
        return self._root

    @classmethod
    def from_bytes(cls, bytes_, offset=0):
        self = cls(offset=offset)
        self.set_file(io.BytesIO(bytes_))
        return self

    def getRoot(self):
        """Deprecated. Use the `root` property instead."""
        warnings.warn("SquashFsImage.getRoot() is deprecated. "
                      "Use the root property instead",
                      DeprecationWarning, stacklevel=2)
        return self.root

    def set_file(self, fd):
        self._image_file = fd
        fd.seek(self.offset)
        self._initialize()

    def setFile(self, fd):
        """Deprecated. Use `SquashFsImage.set_file()` instead."""
        warnings.warn("SquashFsImage.setFile() is deprecated. "
                      "Use set_file() instead",
                      DeprecationWarning, stacklevel=2)
        self.set_file(fd)

    def open(self, filepath):
        self._image_file = open(filepath, 'rb')
        self._image_file.seek(self.offset)
        self._initialize()

    def close(self):
        self._image_file.close()
        self._image_file = None

    def _read_super(self):
        self.sBlk.read(self._image_file)
        if self.sBlk.s_magic != SQUASHFS_MAGIC or self.sBlk.s_major != 4 or self.sBlk.s_minor != 0:
            raise IOError("The file supplied is not a squashfs 4.0 image")
        self.comp = self._get_compressor(self.sBlk.compression)

    def _get_compressor(self, compression_id):
        if compression_id not in _compressors:
            raise ValueError("Unknown compression method %r" % compression_id)
        return _compressors[compression_id]()

    def _initialize(self):
        self._read_super()
        self.block_size = self.sBlk.block_size
        self.block_log = self.sBlk.block_log
        self.fragment_buffer_size <<= 20 - self.block_log
        self.data_buffer_size <<= 20 - self.block_log
        self.all_buffers_size = self.fragment_buffer_size + self.data_buffer_size
        self._read_uids_guids()
        self._read_fragment_table()
        self._read_xattrs_from_disk()
        root_block = SQUASHFS_INODE_BLK(self.sBlk.root_inode)
        root_offs = SQUASHFS_INODE_OFFSET(self.sBlk.root_inode)
        self._root = self._dir_scan(root_block, root_offs)

    def _read_data_block(self, start, size):
        c_byte = SQUASHFS_COMPRESSED_SIZE_BLOCK(size)
        self._image_file.seek(self.offset + start)
        data = self._image_file.read(c_byte)
        if SQUASHFS_COMPRESSED_BLOCK(size):
            return self.comp.uncompress(data)
        else:
            return data

    def read_file(self, inode):
        # unsquashfs.c -> write_file
        start = inode.start
        content = b''
        if inode.blocks:
            block_list = self._read_block_list(inode.block_start, inode.block_offset, inode.blocks)
            for block in block_list:
                if block == SQUASHFS_INVALID_FRAG:
                    continue
                c_byte = SQUASHFS_COMPRESSED_SIZE_BLOCK(block)
                if block != 0:  # non sparse file
                    content += self._read_data_block(start, block)
                    start += c_byte
        if inode.frag_bytes:
            start, size = self._read_fragment(inode.fragment)
            buffer = self._read_data_block(start, size)
            # inode.frag_bytes was (inode.data%self.block_size)
            content += buffer[inode.offset : inode.offset + inode.frag_bytes]
        return content

    def getFileContent(self, inode):
        """Deprecated. Use `SquashFsImage.read_file()` instead."""
        warnings.warn("SquashFsImage.getFileContent() is deprecated. "
                      "Use read_file() instead",
                      DeprecationWarning, stacklevel=2)
        return self.read_file(inode)

    def _read_block_list(self, start, offset, blocks):
        # unsquash-4.c
        size = 4  # sizeof(unsigned int)
        idata, _, _ = self._read_inode_data(start, offset, blocks * size)
        ret = []
        ofs = 0
        for _ in range(blocks):  # use struct.iter_unpack when Py3 only
            ret.append(self._make_buf_integer(idata, ofs, size))
            ofs += size
        return ret

    def _read_block(self, start):
        """Read a block starting at offset `start` relative to the start of the image.

        Return the uncompressed block and the start of the next compressed one.
        """
        self._image_file.seek(self.offset + start)
        c_byte = self._read_short()
        offset = 3 if SQUASHFS_CHECK_DATA(self.sBlk.flags) else 2
        self._image_file.seek(self.offset + start + offset)
        size = SQUASHFS_COMPRESSED_SIZE(c_byte)
        block = self._image_file.read(size)
        if SQUASHFS_COMPRESSED(c_byte):
            block = self.comp.uncompress(block)
        return block, start + offset + size

    def _read_fragment_table(self):
        indexes = SQUASHFS_FRAGMENT_INDEXES(self.sBlk.fragments)
        if self.sBlk.fragments == 0:
            return
        self._image_file.seek(self.offset + self.sBlk.fragment_table_start)
        fragment_table_index = [self._read_long() for _ in range(indexes)]
        table = b''.join(self._read_block(fti)[0] for fti in fragment_table_index)
        ofs = 0
        while ofs < len(table):
            entry = _SquashfsFragmentEntry.from_bytes(table, ofs)
            ofs += _SquashfsFragmentEntry.SIZE
            entry.fragment = self._read_data_block(entry.start_block, entry.size)
            self.fragment_table.append(entry)

    def _read_fragment(self, fragment):
        entry = self.fragment_table[fragment]
        return (entry.start_block, entry.size)

    def _read_inode(self, start_block, offset):
        # unsquash-4.c
        start = self.sBlk.inode_table_start + start_block
        idata, start, offset = self._read_inode_data(start, offset, sizeof(InodeHeader))
        header = InodeHeader.from_bytes(idata)
        cls = inomap[header.inode_type]
        idata, start, offset = self._read_inode_data(start, offset, sizeof(cls))
        ino = cls.from_bytes(idata)
        ino._header = header
        ino._uid = self.id_table[header.uid]
        ino._gid = self.id_table[header.guid]
        ino._mode = SQUASHFS_LOOKUP_TYPE[header.inode_type] | header.mode
        try:
            inode_type = Type(header.inode_type)
        except ValueError:
            raise RuntimeError("Unknown inode type %d in read_inode!\n" % header.inode_type)
        if inode_type in (Type.FILE, Type.LREG):
            ino._block_start = start
            ino._block_offset = offset
            if ino.fragment == SQUASHFS_INVALID_FRAG:
                ino._frag_bytes = 0
                ino._blocks = (ino.data + self.sBlk.block_size - 1) >> self.sBlk.block_log
            else:
                ino._frag_bytes = ino.file_size % self.sBlk.block_size
                ino._blocks = ino.data >> self.sBlk.block_log
        elif inode_type in (Type.SYMLINK, Type.LSYMLINK):
            idata, start, offset = self._read_inode_data(start, offset, ino.symlink_size)
            ino._symlink = idata
            if inode_type == Type.LSYMLINK:
                idata, start, offset = self._read_inode_data(start, offset, 4)
                ino._xattr = self._make_buf_integer(idata, 0, len(idata))
        return ino

    def _opendir(self, block_start, offset):
        # unsquash-4.c -> squashfs_opendir
        inode = self._read_inode(block_start, offset)
        directory = Directory(self, inode)
        directory.entries = []
        if inode.data == 3:
            return directory
        start = self.sBlk.directory_table_start + inode.start
        offset = inode.offset
        size = inode.data - 3
        bytes_ = 0
        while bytes_ < size:
            ddata, start, offset = self._read_directory_data(start, offset, sizeof(DirHeader))
            dirh = DirHeader.from_bytes(ddata)
            bytes_ += sizeof(DirHeader)
            for _ in range(dirh.count + 1):
                ddata, start, offset = self._read_directory_data(start, offset, sizeof(DirEntry))
                dire = DirEntry.from_bytes(ddata)
                namelen = dire.size + 1
                ddata, start, offset = self._read_directory_data(start, offset, namelen)
                dire._name = ddata
                bytes_ += sizeof(DirEntry) + namelen
                directory.entries.append({
                    "name": dire._name,
                    "start_block": dirh.start_block,
                    "offset": dire.offset,
                    "type": dire.type
                })
        return directory

    def _read_uids_guids(self):
        size = 4
        indexes = SQUASHFS_ID_BLOCKS(self.sBlk.no_ids)
        id_index_table = []
        self._image_file.seek(self.offset + self.sBlk.id_table_start)
        for _ in range(indexes):
            id_index_table.append(self._make_integer(SQUASHFS_ID_BLOCK_BYTES(1)))
        for i, idx in enumerate(id_index_table):
            block = self._read_block(idx)[0]
            offset = 0
            index = i * (SQUASHFS_METADATA_SIZE // 4)
            while offset < len(block):
                self.id_table[index] = self._make_buf_integer(block, offset, size)
                offset += size
                index += 1

    def _read_xattrs_from_disk(self):
        id_table = _XattrTable()
        if self.sBlk.xattr_id_table_start == SQUASHFS_INVALID_BLK:
            return SQUASHFS_INVALID_BLK
        self._image_file.seek(self.offset + self.sBlk.xattr_id_table_start)
        id_table.read(self._image_file)
        ids = id_table.xattr_ids
        xattr_table_start = id_table.xattr_table_start
        indexes = SQUASHFS_XATTR_BLOCKS(ids)
        index = []
        for _ in range(indexes):
            index.append(self._make_integer(SQUASHFS_XATTR_BLOCK_BYTES(1)))
        xattr_ids = {}
        for i, idx in enumerate(index):
            block = self._read_block(idx)[0]
            cur_idx = (i * SQUASHFS_METADATA_SIZE) / 16
            ofs = 0
            while ofs < len(block):
                xattr_ids[cur_idx] = _XattrId.from_bytes(block, ofs)
                cur_idx += 1
                ofs += _XattrId.SIZE
        start = xattr_table_start
        i = 0
        while start < index[0]:
            self.hash_table[start] = i * SQUASHFS_METADATA_SIZE
            block, start = self._read_block(start)
            for i in range(len(block), SQUASHFS_METADATA_SIZE):
                block += b'\x00'
            self.xattrs += block
            i += 1
        return ids

    def _dir_scan(self, start_block, offset):
        directory = self._opendir(start_block, offset)
        for entry in directory.entries:  # No need for squashfs_readdir()
            start_block = entry["start_block"]
            offset = entry["offset"]
            if entry["type"] == Type.DIR:
                subdir = self._dir_scan(start_block, offset)
                subdir._parent = directory
                subdir._name = entry["name"]
                directory.children[subdir.name] = subdir
            else:
                inode = self._read_inode(start_block, offset)
                cls = filetype[entry["type"]]
                file = cls(self, inode, entry["name"], directory)
                directory.children[file.name] = file
        del directory.entries
        return directory

    def _make_integer(self, length):
        """Assemble multibyte integer."""
        return self._make_buf_integer(self._image_file.read(length), 0, length)

    def _make_buf_integer(self, buf, start, length):
        """Assemble multibyte integer."""
        if sys.version_info < (3, 2):
            ret = 0
            pwr = 1
            for i in range(start, start + length):
                ret += (ord(buf[i]) & 0xFF) * pwr
                pwr *= 0x100
            return ret
        else:
            return int.from_bytes(buf[start : start + length], byteorder='little')

    def _read_integer(self, fmt):
        return struct.unpack(fmt, self._image_file.read(struct.calcsize(fmt)))[0]

    def _read_short(self):
        return self._read_integer("<H")

    def _read_long(self):
        return self._read_integer("<Q")

    def _get_metadata(self, hash_table, start):
        try:
            return hash_table[start]
        except KeyError:
            hash_table[start] = dict(zip(("buffer", "next_index"), self._read_block(start)))
            return hash_table[start]

    def _read_metadata(self, hash_table, block, offset, length):
        data = b''
        while True:
            entry = self._get_metadata(hash_table, block)
            copy = len(entry["buffer"]) - offset
            if copy < length:
                data += entry["buffer"][offset:]
                length -= copy
                block = entry["next_index"]
                offset = 0
            elif copy == length:
                data += entry["buffer"][offset : offset + length]
                return data, entry["next_index"], 0
            else:
                data += entry["buffer"][offset : offset + length]
                return data, block, offset + length

    def _read_inode_data(self, block, offset, length):
        return self._read_metadata(self.inode_table_hash, block, offset, length)

    def _read_directory_data(self, block, offset, length):
        return self._read_metadata(self.directory_table_hash, block, offset, length)

    def find(self, filename):
        return self._root.find(filename)

    def select(self, path):
        return self._root.select(path)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Print information about squashfs images.")
    parser.add_argument("file", help="squashfs filesystem")
    parser.add_argument("paths", nargs='+', help="directories or files to print information about")
    parser.add_argument("-V", "--version", action="version", version="%(prog)s v0.8.0")
    args = parser.parse_args()

    image = SquashFsImage(args.file)
    if len(sys.argv) > 1:
        for path in args.paths:
            print("--------------%-50.50s --------------" % path)
            squashed_file = image.root.select(path)
            if squashed_file is None:
                print("NOT FOUND")
            elif squashed_file.is_dir:
                print("FOLDER " + squashed_file.path)
                for child in squashed_file.iterdir():
                    if child.is_dir:
                        print("\t%s %-60s  <dir> " % (child.filemode, child.name))
                    elif child.is_symlink:
                        print("\t%s %s -> %s" % (child.filemode, child.name, child.readlink()))
                    else:
                        print("\t%s %-60s %8d" % (child.filemode, child.name, child.size))
            else:
                print(squashed_file.read_bytes())
    else:
        for i in image.root.find_all():
            nodetype = "FILE  "
            if i.is_dir:
                nodetype = "FOLDER"
            # print(nodetype + ' ' + i.path + " inode=" + i.inode.inode_number + " (" + image._read_block_list(i.inode) + " + " + i.inode.offset + ")")

        for i in image.root.find_all():
            if i.name.endswith(".ini"):
                content = i.read_bytes()
                print("==============%-50.50s (%8d)==============" % (i.path, len(content)))
                print(content)
            elif i.name.endswith(".so"):
                content = i.read_bytes()
                print("++++++++++++++%-50.50s (%8d)++++++++++++++" % (i.path, len(content)))
                oname = i.name + "_saved_" + str(i.inode.inode_number)
                print("written %s from %s %d" % (oname, i.name, len(content)))
                with open(oname, "wb") as of:
                    of.write(content)
        image.close()


if __name__ == "__main__":
    main()
