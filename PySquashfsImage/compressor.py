from .const import LZ4_COMPRESSION, NO_COMPRESSION, XZ_COMPRESSION, ZLIB_COMPRESSION, ZSTD_COMPRESSION


class _Compressor:
    name = "none"

    def uncompress(self, src):
        return src
    def __getstate__(self):
        return self.name


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
            import lzma
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


compressors = {
    NO_COMPRESSION: _Compressor,
    ZLIB_COMPRESSION: _ZlibCompressor,
    XZ_COMPRESSION: _XZCompressor,
    LZ4_COMPRESSION: _LZ4Compressor,
    ZSTD_COMPRESSION: _ZSTDCompressor
}
