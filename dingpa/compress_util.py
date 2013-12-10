import zlib, base64

def compress(buf):
	return base64.b64encode(zlib.compress(buf))

def decompress(buf):
	return base64.b64decode(zlib.decompress(buf))

if __name__ == '__main__':
	a = compress("Hello World")
	print a
	print decompress(a)