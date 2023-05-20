from .const import LZ4_COMPRESSION, NO_COMPRESSION, XZ_COMPRESSION, ZLIB_COMPRESSION, ZSTD_COMPRESSION


class Compressor:
    name = "none"

    def uncompress(self, src, size, outsize):
        return src


class ZlibCompressor(Compressor):
    name = "gzip"

    def __init__(self):
        import zlib
        self._lib = zlib

    def uncompress(self, src, size, outsize):
        return self._lib.decompress(src)


class XZCompressor(Compressor):
    name = "xz"

    def __init__(self):
        try:
            import lzma
        except ImportError:
            from backports import lzma
        self._lib = lzma

    def uncompress(self, src, size, outsize):
        return self._lib.decompress(src)


class LZ4Compressor(Compressor):
    name = "lz4"

    def __init__(self):
        import lz4.frame
        self._lib = lz4.frame

    def uncompress(self, src, size, outsize):
        return self._lib.decompress(src)


class ZSTDCompressor(Compressor):
    name = "zstd"

    def __init__(self):
        import zstandard
        self._lib = zstandard.ZstdDecompressor()

    def uncompress(self, src, size, outsize):
        return self._lib.decompress(src)


compressors = {
    NO_COMPRESSION: Compressor,
    ZLIB_COMPRESSION: ZlibCompressor,
    XZ_COMPRESSION: XZCompressor,
    LZ4_COMPRESSION: LZ4Compressor,
    ZSTD_COMPRESSION: ZSTDCompressor
}
