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
__all__ = ['SquashFsImage', 'SquashedFile', 'SquashInode']

import struct
import sys
import stat

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

SQUASHFS_DIR_TYPE = 1
SQUASHFS_FILE_TYPE = 2
SQUASHFS_SYMLINK_TYPE = 3
SQUASHFS_BLKDEV_TYPE = 4
SQUASHFS_CHRDEV_TYPE = 5
SQUASHFS_FIFO_TYPE = 6
SQUASHFS_SOCKET_TYPE = 7
SQUASHFS_LDIR_TYPE = 8
SQUASHFS_LREG_TYPE = 9
SQUASHFS_LSYMLINK_TYPE = 10
SQUASHFS_LBLKDEV_TYPE = 11
SQUASHFS_LCHRDEV_TYPE = 12
SQUASHFS_LFIFO_TYPE = 13
SQUASHFS_LSOCKET_TYPE = 14


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


SQASHFS_LOOKUP_TYPE = [
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


def byt2str(data):
    if isinstance(data, bytes):
        return data.decode("latin-1")
    return data


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

pyVersionTwo = sys.version_info[0] < 3


class _Squashfs_commons(object):  # Explicit new-style class for Python 2

    def makeInteger(self, myfile, length):
        """Assemble multibyte integer."""
        return self.makeBufInteger(myfile.read(length), 0, length)

    def makeBufInteger(self, buf, start, length):
        """Assemble multibyte integer."""
        if pyVersionTwo:
            ret = 0
            pwr = 1
            for i in range(start, start + length):
                ret += (ord(buf[i]) & 0xFF) * pwr
                pwr *= 0x100
            return ret
        else:
            return int.from_bytes(buf[start : start + length], byteorder='little')

    def _read_integer(self, myfile, fmt):
        return struct.unpack(fmt, myfile.read(struct.calcsize(fmt)))[0]

    def readShort(self, myfile):
        return self._read_integer(myfile, "<H")

    def readLong(self, myfile):
        return self._read_integer(myfile, "<Q")

    def autoMakeBufInteger(self, buf, start, length):
        """Assemble multibyte integer."""
        return (self.makeBufInteger(buf, start, length), start + length)

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


class _Squashfs_super_block(_Squashfs_commons):

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


class _Squashfs_fragment_entry(_Squashfs_commons):

    FORMAT = "<QII"
    SIZE = struct.calcsize(FORMAT)
    FIELDS = ["start_block", "size", "unused"]

    def __init__(self):
        self.start_block = 0
        self.size = 0
        self.unused = 0
        self.fragment = None


class SquashInode:

    def __init__(self, owner_image):
        self.image = owner_image
        self.blocks = 0
        self.block_ptr = 0
        self.data = 0
        self.fragment = 0
        self.frag_bytes = 0
        self.gid = 0
        self.inode_number = 0
        self.mode = 0
        self.offset = 0
        self.start = 0
        self.symlink = 0
        self.time = 0
        self.type = 0
        self.uid = 0
        self.sparse = 0
        self.xattr = 0

    def getXattr(self):
        return self.xattr

    def getContent(self):
        return self.image.getFileContent(self)

    def hasAttribute(self, mask):
        return (self.mode & mask) == mask


class _Inode_header(_Squashfs_commons):

    BASE_FORMAT = "<HHHHII"
    BASE_FIELDS = ["inode_type", "mode", "uid", "guid", "mtime", "inode_number"]

    def __init__(self):
        self.inode_type = 0
        self.mode = 0
        self.uid = 0
        self.guid = 0
        self.mtime = 0
        self.inode_number = 0

        self.rdev = 0
        self.xattr = 0

        self.nlink = 0
        self.symlink_size = 0
        self.symlink = []

        self.start_block = 0
        self.fragment = 0

        self.block_list = []
        self.file_size = 0
        self.offset = 0
        self.parent_inode = 0
        self.start_block = 0
        self.file_size = 0
        self.i_count = 0
        self.offset = 0

        self.file_size = 0
        self.sparse = 0
        self.index = []

    def _set_values(self, fmt, fields, buff, offset):
        """Return the amount of bytes read from the buffer."""
        size = struct.calcsize(fmt)
        values = struct.unpack_from(fmt, buff, offset)
        for field, value in zip(fields, values):
            setattr(self, field, value)
        return size

    def base_header(self, buff, offset):
        return self._set_values(self.BASE_FORMAT, self.BASE_FIELDS, buff, offset)

    def ipc_header(self, buff, offset):
        offset += self.base_header(buff, offset)
        self._set_values('<I', ["nlink"], buff, offset)

    def lipc_header(self, buff, offset):
        offset += self.base_header(buff, offset)
        self._set_values("<II", ["nlink", "xattr"], buff, offset)

    def dev_header(self, buff, offset):
        offset += self.base_header(buff, offset)
        self._set_values("<II", ["nlink", "rdev"], buff, offset)

    def ldev_header(self, buff, offset):
        offset += self.base_header(buff, offset)
        self._set_values("<III", ["nlink", "rdev", "xattr"], buff, offset)

    def symlink_header(self, buff, offset):
        offset += self.base_header(buff, offset)
        offset += self._set_values("<II", ["nlink", "symlink_size"], buff, offset)
        self.symlink = byt2str(buff[offset : offset + self.symlink_size])

    def reg_header(self, buff, offset):
        fields = ["start_block", "fragment", "offset", "file_size"]
        offset += self.base_header(buff, offset)
        offset += self._set_values("<IIII", fields, buff, offset)
        self.block_list = buff[offset:]
        return offset

    def lreg_header(self, buff, offset):
        fields = [
            "start_block", "file_size", "sparse", "nlink", "fragment", "offset", "xattr"
        ]
        offset += self.base_header(buff, offset)
        offset += self._set_values("<QQQIIII", fields, buff, offset)
        self.block_list = buff[offset:]
        return offset

    def dir_header(self, buff, offset):
        fields = ["start_block", "nlink", "file_size", "offset", "parent_inode"]
        offset += self.base_header(buff, offset)
        self._set_values("<IIHHI", fields, buff, offset)

    def ldir_header(self, buff, offset):
        fields = [
            "nlink", "file_size", "start_block", "parent_inode",
            "i_count", "offset", "xattr"
        ]
        offset += self.base_header(buff, offset)
        offset += self._set_values("<IIIIHHI", fields, buff, offset)
        self.index = buff[offset:]


class _Dir_entry(_Squashfs_commons):

    FORMAT = "<HhHH"
    SIZE = struct.calcsize(FORMAT)
    FIELDS = ["offset", "inode_number", "type", "size"]

    def __init__(self):
        self.offset = 0
        self.inode_number = 0
        self.type = 0
        self.size = 0
        self.name = None
        self.s_file = None

    @classmethod
    def from_bytes(cls, buffer, offset=0):
        # super without arguments is not Python 2 compatible.
        inst = super(_Dir_entry, cls).from_bytes(buffer, offset)
        offset += cls.SIZE
        inst.name = byt2str(buffer[offset : offset + inst.size + 1])
        return inst


class _Dir_header(_Squashfs_commons):

    FORMAT = "<III"
    SIZE = struct.calcsize(FORMAT)
    FIELDS = ["count", "start_block", "inode_number"]

    def __init__(self):
        self.count = 0
        self.start_block = 0
        self.inode_number = 0


class _Dir:

    def __init__(self):
        self.dir_count = 0
        self.cur_entry = 0
        self.mode = 0
        self.uid = 0
        self.guid = 0
        self.mtime = 0
        self.xattr = 0
        self.dirs = []


class _Xattr_id(_Squashfs_commons):  # 16

    FORMAT = "<QII"
    SIZE = struct.calcsize(FORMAT)
    FIELDS = ["xattr", "count", "size"]

    def __init__(self):
        self.xattr = 0
        self.count = 0
        self.size = 0


class _Xattr_table(_Squashfs_commons):

    FORMAT = "<QII"
    SIZE = struct.calcsize(FORMAT)
    FIELDS = ["xattr_table_start", "xattr_ids", "unused"]

    def __init__(self):
        self.xattr_table_start = 0
        self.xattr_ids = 0
        self.unused = 0


class SquashedFile:

    def __init__(self, name, parent=None):
        self.name = name
        self.children = []
        self.inode = None
        self.parent = parent

    def getPath(self):
        if self.parent is None:
            return self.name
        else:
            return self.parent.getPath() + "/" + self.name

    def getXattr(self):
        return self.inode.getXattr()

    def findAll(self):
        ret = [self]
        for i in self.children:
            ret += i.findAll()
        return ret

    def findAllPaths(self):
        ret = [self.getPath()]
        for i in self.children:
            ret += i.findAllPaths()
        return ret

    def getContent(self):
        if self.inode is None:
            return None
        return self.inode.getContent()

    def read(self, path):
        node = self.select(path)
        if node is None:
            return None
        return node.getContent()

    def dirlist(self, path):
        node = self.select(path)
        if node is None:
            return None
        return node.children

    def select(self, path):
        if path == "/":
            path = ''
        lpath = path.split('/')
        start = self
        ofs = 0
        if not lpath[0]:
            ofs = 1
            while start.parent:
                start = start.parent
        if ofs >= len(lpath):
            return start
        for child in start.children:
            if child.name == lpath[ofs]:
                return child._lselect(lpath, ofs + 1)
        return None

    def _lselect(self, lpath, ofs):
        # print lpath,self.name,ofs
        if ofs >= len(lpath):
            return self
        for child in self.children:
            if child.name == lpath[ofs]:
                return child._lselect(lpath, ofs + 1)
        return None

    def hasAttribute(self, mask):
        if self.inode is None:
            return False
        return self.inode.hasAttribute(mask)

    def isFolder(self):
        if self.parent is None:
            return True
        return self.hasAttribute(stat.S_IFDIR)

    def isLink(self):
        return self.hasAttribute(stat.S_IFLNK)

    def close(self):
        self.inode.image.close()

    def getLength(self):
        return self.inode.data

    def getName(self):
        return self.name

    def getLink(self):
        if self.inode is None:
            return None
        return self.inode.symlink

    def getMode(self):
        ret = ['-'] * 10
        if self.inode is not None:
            if not pyVersionTwo:
                return stat.filemode(self.inode.mode)

            if stat.S_ISSOCK(self.inode.mode):
                ret[0] = 's'
            if stat.S_ISLNK(self.inode.mode):
                ret[0] = 'l'
            if stat.S_ISBLK(self.inode.mode):
                ret[0] = 'b'
            if stat.S_ISDIR(self.inode.mode):
                ret[0] = 'd'
            if stat.S_ISCHR(self.inode.mode):
                ret[0] = 'c'
            if stat.S_ISFIFO(self.inode.mode):
                ret[0] = 'p'

            if (self.inode.mode & stat.S_IRUSR) == stat.S_IRUSR:
                ret[1] = 'r'
            if (self.inode.mode & stat.S_IWUSR) == stat.S_IWUSR:
                ret[2] = 'w'
            if (self.inode.mode & stat.S_IRGRP) == stat.S_IRGRP:
                ret[4] = 'r'
            if (self.inode.mode & stat.S_IWGRP) == stat.S_IWGRP:
                ret[5] = 'w'
            if (self.inode.mode & stat.S_IROTH) == stat.S_IROTH:
                ret[7] = 'r'
            if (self.inode.mode & stat.S_IWOTH) == stat.S_IWOTH:
                ret[8] = 'w'

            if (self.inode.mode & stat.S_IXUSR) == stat.S_IXUSR:
                ret[3] = 'x'
                if (self.inode.mode & stat.S_ISUID) == stat.S_ISUID:
                    ret[3] = 's'
            if (self.inode.mode & stat.S_IXGRP) == stat.S_IXGRP:
                ret[6] = 'x'
                if (self.inode.mode & stat.S_ISGID) == stat.S_ISGID:
                    ret[6] = 's'
            if (self.inode.mode & stat.S_IXOTH) == stat.S_IXOTH:
                ret[9] = 'x'

        return ''.join(ret)


class SquashFsImage(_Squashfs_commons):

    def __init__(self, filepath=None, offset=0):
        self.comp = None
        self.sBlk = _Squashfs_super_block()
        self.fragment_buffer_size = FRAGMENT_BUFFER_DEFAULT
        self.data_buffer_size = DATA_BUFFER_DEFAULT
        self.block_size = 0
        self.block_log = 0
        self.all_buffers_size = 0
        self.fragment_table = []
        self.id_table = 0
        self.inode_table_hash = {}
        self.inode_table = b""
        self.id_table = []
        self.hash_table = {}
        self.xattrs = b""
        self.directory_table_hash = {}
        self.created_inode = []
        self.total_blocks = 0
        self.total_files = 0
        self.total_inodes = 0
        self.directory_table = b''
        self.inode_to_file = {}
        self.root = SquashedFile("")
        self.image_file = None
        self.offset = offset
        if filepath is not None:
            self.open(filepath)

    def getRoot(self):
        return self.root

    def setFile(self, fd):
        self.image_file = fd
        fd.seek(self.offset)
        self.initialize(self.image_file)

    def open(self, filepath):
        self.image_file = open(filepath, 'rb')
        self.image_file.seek(self.offset)
        self.initialize(self.image_file)

    def close(self):
        self.image_file.close()
        self.image_file = None

    def __read_super(self, fd):
        self.sBlk.read(fd)
        if self.sBlk.s_magic != SQUASHFS_MAGIC or self.sBlk.s_major != 4 or self.sBlk.s_minor != 0:
            raise IOError("The file supplied is not a squashfs 4.0 image")
        self.comp = self.getCompressor(self.sBlk.compression)

    def getCompressor(self, compression_id):
        if compression_id not in _compressors:
            raise ValueError("Unknown compression method %r" % compression_id)
        return _compressors[compression_id]()

    def initialize(self, myfile):
        self.__read_super(myfile)
        self.created_inode = [None] * self.sBlk.inodes
        self.block_size = self.sBlk.block_size
        self.block_log = self.sBlk.block_log
        self.fragment_buffer_size <<= 20 - self.block_log
        self.data_buffer_size <<= 20 - self.block_log
        self.all_buffers_size = self.fragment_buffer_size + self.data_buffer_size
        self.read_uids_guids(myfile)
        self.read_fragment_table(myfile)
        self.uncompress_inode_table(myfile, self.sBlk.inode_table_start, self.sBlk.directory_table_start)
        self.uncompress_directory_table(myfile, self.sBlk.directory_table_start, self.sBlk.fragment_table_start)
        self.read_xattrs_from_disk(myfile)
        root_block = SQUASHFS_INODE_BLK(self.sBlk.root_inode)
        root_offs = SQUASHFS_INODE_OFFSET(self.sBlk.root_inode)
        self.pre_scan("squashfs-root", root_block, root_offs, self.root)

    def read_data_block(self, myfile, start, size):
        c_byte = SQUASHFS_COMPRESSED_SIZE_BLOCK(size)
        myfile.seek(self.offset + start)
        data = myfile.read(c_byte)
        if SQUASHFS_COMPRESSED_BLOCK(size):
            return self.comp.uncompress(data)
        else:
            return data

    def getFileContent(self, inode):
        start = inode.start
        content = b""
        block_list = self.read_block_list(inode)
        for cur_blk in block_list:
            if cur_blk == SQUASHFS_INVALID_FRAG:
                continue
            c_byte = SQUASHFS_COMPRESSED_SIZE_BLOCK(cur_blk)
            if cur_blk != 0:  # non sparse file
                content += self.read_data_block(self.image_file, start, cur_blk)
                start += c_byte
        if inode.frag_bytes != 0:
            start, size = self.read_fragment(inode.fragment)
            buffer = self.read_data_block(self.image_file, start, size)
            # inode.frag_bytes was (inode.data%self.block_size)
            content += buffer[inode.offset : inode.offset + inode.frag_bytes]
        return content

    def read_block_list(self, inode):
        ret = []
        ofs = inode.block_ptr
        for _ in range(inode.blocks):
            number, ofs = self.autoMakeBufInteger(self.inode_table, ofs, 4)
            ret.append(number)
        return ret

    def read_block(self, myfile, start):
        myfile.seek(self.offset + start)
        c_byte = self.readShort(myfile)
        offset = 2
        if SQUASHFS_CHECK_DATA(self.sBlk.flags):
            offset = 3
        myfile.seek(self.offset + start + offset)
        size = SQUASHFS_COMPRESSED_SIZE(c_byte)
        block = myfile.read(size)
        if SQUASHFS_COMPRESSED(c_byte):
            block = self.comp.uncompress(block)
        return (block, start + offset + size, size)

    def uncompress_inode_table(self, myfile, start, end):
        bytes_ = 0
        while start < end:
            self.inode_table_hash[start] = bytes_
            block, start, _ = self.read_block(myfile, start)
            self.inode_table += block
            bytes_ = len(self.inode_table)

    def read_fragment_table(self, myfile):
        indexes = SQUASHFS_FRAGMENT_INDEXES(self.sBlk.fragments)
        fragment_table_index = []
        self.fragment_table = []
        if self.sBlk.fragments == 0:
            return
        myfile.seek(self.offset + self.sBlk.fragment_table_start)
        for _ in range(indexes):
            fragment_table_index.append(self.readLong(myfile))
        table = b""
        for fti in fragment_table_index:
            table += self.read_block(myfile, fti)[0]
        ofs = 0
        while ofs < len(table):
            entry = _Squashfs_fragment_entry.from_bytes(table, ofs)
            ofs += _Squashfs_fragment_entry.SIZE
            entry.fragment = self.read_data_block(myfile, entry.start_block, entry.size)
            self.fragment_table.append(entry)

    def read_fragment(self, fragment):
        entry = self.fragment_table[fragment]
        return (entry.start_block, entry.size)

    def read_inode(self, start_block, offset):
        start = self.sBlk.inode_table_start + start_block
        bytes_ = self.inode_table_hash[start]
        block_ptr = bytes_ + offset
        i = SquashInode(self)
        header = _Inode_header()
        header.base_header(self.inode_table, block_ptr)
        i.uid = self.id_table[header.uid]
        i.gid = self.id_table[header.guid]
        i.mode = SQASHFS_LOOKUP_TYPE[header.inode_type] | header.mode
        i.type = header.inode_type
        i.time = header.mtime
        i.inode_number = header.inode_number
        if header.inode_type == SQUASHFS_DIR_TYPE:
            header.dir_header(self.inode_table, block_ptr)
            i.data = header.file_size
            i.offset = header.offset
            i.start = header.start_block
            i.xattr = SQUASHFS_INVALID_XATTR
        elif header.inode_type == SQUASHFS_LDIR_TYPE:
            header.ldir_header(self.inode_table, block_ptr)
            i.data = header.file_size
            i.offset = header.offset
            i.start = header.start_block
            i.xattr = header.xattr
        elif header.inode_type == SQUASHFS_FILE_TYPE:
            i.block_ptr = header.reg_header(self.inode_table, block_ptr)
            i.data = header.file_size
            if header.fragment == SQUASHFS_INVALID_FRAG:
                i.frag_bytes = 0
            else:
                i.frag_bytes = header.file_size % self.sBlk.block_size
            i.fragment = header.fragment
            i.offset = header.offset
            if header.fragment == SQUASHFS_INVALID_FRAG:
                i.blocks = (i.data + self.sBlk.block_size - 1) >> self.sBlk.block_log
            else:
                i.blocks = i.data >> self.sBlk.block_log
            i.start = header.start_block
            i.sparse = 0
            # i.block_ptr = block_ptr + 32 #sizeof(*inode)
            i.xattr = SQUASHFS_INVALID_XATTR
        elif header.inode_type == SQUASHFS_LREG_TYPE:
            i.block_ptr = header.lreg_header(self.inode_table, block_ptr)
            i.data = header.file_size
            if header.fragment == SQUASHFS_INVALID_FRAG:
                i.frag_bytes = 0
            else:
                i.frag_bytes = header.file_size % self.sBlk.block_size
            i.fragment = header.fragment
            i.offset = header.offset
            if header.fragment == SQUASHFS_INVALID_FRAG:
                i.blocks = (header.file_size + self.sBlk.block_size - 1) >> self.sBlk.block_log
            else:
                i.blocks = header.file_size >> self.sBlk.block_log
            i.start = header.start_block
            i.sparse = header.sparse != 0
            # i.block_ptr = block_ptr + 60#sizeof(*inode)
            i.xattr = header.xattr
        elif header.inode_type in (SQUASHFS_SYMLINK_TYPE, SQUASHFS_LSYMLINK_TYPE):
            header.symlink_header(self.inode_table, block_ptr)
            i.symlink = header.symlink
            i.data = header.symlink_size
            if header.inode_type == SQUASHFS_LSYMLINK_TYPE:
                i.xattr = self.makeBufInteger(self.inode_table, block_ptr + 24 + header.symlink_size, 4)
            else:
                i.xattr = SQUASHFS_INVALID_XATTR
        elif header.inode_type in (SQUASHFS_BLKDEV_TYPE, SQUASHFS_CHRDEV_TYPE):
            header.dev_header(self.inode_table, block_ptr)
            i.data = header.rdev
            i.xattr = SQUASHFS_INVALID_XATTR
        elif header.inode_type in (SQUASHFS_LBLKDEV_TYPE, SQUASHFS_LCHRDEV_TYPE):
            header.ldev_header(self.inode_table, block_ptr)
            i.data = header.rdev
            i.xattr = header.xattr
        elif header.inode_type in (SQUASHFS_FIFO_TYPE, SQUASHFS_SOCKET_TYPE):
            i.data = 0
            i.xattr = SQUASHFS_INVALID_XATTR
        elif header.inode_type in (SQUASHFS_LFIFO_TYPE, SQUASHFS_LSOCKET_TYPE):
            header.lipc_header(self.inode_table, block_ptr)
            i.data = 0
            i.xattr = header.xattr
        else:
            raise RuntimeError("Unknown inode type %d in read_inode!\n" % header.inode_type)
        return i

    def uncompress_directory_table(self, myfile, start, end):
        while start < end:
            self.directory_table_hash[start] = len(self.directory_table)
            block, start, _ = self.read_block(myfile, start)
            self.directory_table += block

    def squashfs_opendir(self, block_start, offset, s_file):
        i = self.read_inode(block_start, offset)
        start = self.sBlk.directory_table_start + i.start
        bytes_ = self.directory_table_hash[start]
        bytes_ += i.offset
        size = i.data + bytes_ - 3
        self.inode_to_file[i.inode_number] = s_file
        s_file.inode = i
        mydir = _Dir()
        mydir.dir_count = 0
        mydir.cur_entry = 0
        mydir.mode = i.mode
        mydir.uid = i.uid
        mydir.guid = i.gid
        mydir.mtime = i.time
        mydir.xattr = i.xattr
        mydir.dirs = []
        while bytes_ < size:
            dirh = _Dir_header.from_bytes(self.directory_table, bytes_)
            dir_count = dirh.count + 1
            bytes_ += _Dir_header.SIZE
            while dir_count != 0:
                dire = _Dir_entry.from_bytes(self.directory_table, bytes_)
                dir_count -= 1
                dire.s_file = SquashedFile(dire.name, s_file)
                s_file.children.append(dire.s_file)
                dire.parent = mydir
                dire.start_block = dirh.start_block
                mydir.dirs.append(dire)
                mydir.dir_count += 1
                bytes_ += _Dir_entry.SIZE + dire.size + 1
        return (mydir, i)

    def read_uids_guids(self, myfile):
        indexes = SQUASHFS_ID_BLOCKS(self.sBlk.no_ids)
        id_index_table = []
        self.id_table = [None] * self.sBlk.no_ids
        myfile.seek(self.offset + self.sBlk.id_table_start)
        for _ in range(indexes):
            id_index_table.append(self.makeInteger(myfile, SQUASHFS_ID_BLOCK_BYTES(1)))
        for i, idx in enumerate(id_index_table):
            myfile.seek(self.offset + idx)
            block = self.read_block(myfile, idx)[0]
            offset = 0
            index = i * (SQUASHFS_METADATA_SIZE // 4)
            while offset < len(block):
                self.id_table[index], offset = self.autoMakeBufInteger(block, offset, 4)
                index += 1

    def read_xattrs_from_disk(self, myfile):
        id_table = _Xattr_table()
        if self.sBlk.xattr_id_table_start == SQUASHFS_INVALID_BLK:
            return SQUASHFS_INVALID_BLK
        myfile.seek(self.offset + self.sBlk.xattr_id_table_start)
        id_table.read(myfile)
        ids = id_table.xattr_ids
        xattr_table_start = id_table.xattr_table_start
        indexes = SQUASHFS_XATTR_BLOCKS(ids)
        index = []
        for _ in range(indexes):
            index.append(self.makeInteger(myfile, SQUASHFS_XATTR_BLOCK_BYTES(1)))
        xattr_ids = {}
        for i, idx in enumerate(index):
            block = self.read_block(myfile, idx)[0]
            cur_idx = (i * SQUASHFS_METADATA_SIZE) / 16
            ofs = 0
            while ofs < len(block):
                xattr_ids[cur_idx] = _Xattr_id.from_bytes(block, ofs)
                cur_idx += 1
                ofs += _Xattr_id.SIZE
        start = xattr_table_start
        end = index[0]
        i = 0
        while start < end:
            self.hash_table[start] = i * SQUASHFS_METADATA_SIZE
            block, start, _ = self.read_block(myfile, start)
            for i in range(len(block), SQUASHFS_METADATA_SIZE):
                block += b'\x00'
            self.xattrs += block
            i += 1
        return ids

    def pre_scan(self, parent_name, start_block, offset, parent):
        mydir, i = self.squashfs_opendir(start_block, offset, parent)
        while mydir.cur_entry < mydir.dir_count:
            dir_entry = mydir.dirs[mydir.cur_entry]
            start_block = dir_entry.start_block
            offset = dir_entry.offset
            objtype = dir_entry.type
            parent = dir_entry.s_file
            mydir.cur_entry += 1
            if objtype == SQUASHFS_DIR_TYPE:
                self.pre_scan(parent_name, start_block, offset, parent)
            else:
                if objtype in [SQUASHFS_FILE_TYPE, SQUASHFS_LREG_TYPE, SQUASHFS_SYMLINK_TYPE, SQUASHFS_LSYMLINK_TYPE]:
                    i = self.read_inode(start_block, offset)
                    if self.created_inode[i.inode_number - 1] is None:
                        self.created_inode[i.inode_number - 1] = i
                        self.total_blocks += (i.data + (self.block_size - 1)) >> self.block_log
                    self.total_files += 1
                self.total_inodes += 1
                self.inode_to_file[i.inode_number] = dir_entry.s_file
                dir_entry.s_file.inode = i
        return mydir


def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Print information about squashfs images.")
    parser.add_argument("file", help="squashfs filesystem")
    parser.add_argument("paths", nargs='+', help="directories or files to print information about")
    parser.add_argument("-V", "--version", action="version", version="%(prog)s v0.8.0")
    args = parser.parse_args()

    image = SquashFsImage(args.file)
    if len(sys.argv) > 1:
        for path in args.paths:
            sqashed_filename = path
            squashed_file = image.root.select(sqashed_filename)
            print("--------------%-50.50s --------------" % sqashed_filename)
            if squashed_file is None:
                print("NOT FOUND")
            elif squashed_file.isFolder():
                print("FOLDER " + squashed_file.getPath())
                for child in squashed_file.children:
                    if child.isFolder():
                        print("\t%s %-60s  <dir> " % (child.getMode(), child.name))
                    elif child.isLink():
                        print("\t%s %s -> %s" % (child.getMode(), child.name, child.getLink()))
                    else:
                        print("\t%s %-60s %8d" % (child.getMode(), child.name, child.inode.data))
            else:
                print(squashed_file.getContent())
    else:
        for i in image.root.findAll():
            nodetype = "FILE  "
            if i.isFolder():
                nodetype = "FOLDER"
            print(nodetype + ' ' + i.getPath() + " inode=" + i.inode.inode_number + " (" + image.read_block_list(i.inode) + " + " + i.inode.offset + ")")

        for i in image.root.findAll():
            if i.name.endswith(".ini"):
                content = i.getContent()
                print("==============%-50.50s (%8d)==============" % (i.getPath(), len(content)))
                print(content)
            elif i.name.endswith(".so"):
                content = i.getContent()
                print("++++++++++++++%-50.50s (%8d)++++++++++++++" % (i.getPath(), len(content)))
                oname = i.name + "_saved_" + str(i.inode.inode_number)
                print("written %s from %s %d" % (oname, i.name, len(content)))
                with open(oname, "wb") as of:
                    of.write(content)
        image.close()


if __name__ == "__main__":
    main()
