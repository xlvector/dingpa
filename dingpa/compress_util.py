import zlib

def compress(buf):
	return zlib.compress(buf)

def decompress(buf):
	return zlib.decompress(buf)

if __name__ == '__main__':
	a = compress("Hello World")
	print a
	print decompress(a)