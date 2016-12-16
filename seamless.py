#!/usr/bin/env python3

import socket

def main():
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	sock.bind(('', 8000))
	sock.listen(1)
	while True:
		conn, addr = sock.accept()
		with conn:
			handle_client(conn)

def handle_client(conn):
	data = conn.recv(1024)
	if not data:
		return
	req = data.split(b'\r\n')[0].decode('ascii')
	content = 'hello\n'
	header = 'HTTP/1.1 200 OK'
	headers = {
		'Content-Type': 'text/plain; charset=utf-8',
		'Content-Length': len(content),
		'Connection': 'close',
	}
	response = header + '\r\n' + '\r\n'.join(map(lambda kv: '%s: %s' % kv, headers.items())) + '\r\n' * 2 + content
	conn.sendall(response.encode('ascii'))
	print('recv', req, 'send', content.rstrip('\n'))
	conn.close()

if __name__ == '__main__':
	main()
