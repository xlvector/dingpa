import zlib, base64

def compress(buf):
	if buf == '':
		return buf
	return zlib.compress(buf)

def decompress(buf):
	if buf == '':
		return buf
	return zlib.decompress(buf)

if __name__ == '__main__':
	a = compress("Hello World")
	print a
	print decompress(a)