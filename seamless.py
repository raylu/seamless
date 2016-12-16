#!/usr/bin/env python3

import os
import selectors
import signal
import socket
import sys

sock = None
keep_going = True

def main():
	global sock, keep_going
	if len(sys.argv) == 2:
		fd = int(sys.argv[1])
		print('inheriting', fd)
		sock = socket.socket(fileno=fd) # sock is now non-inheritable
	else:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.bind(('', 8000))
		sock.listen(1)

	signal.signal(signal.SIGHUP, hup)
	signal.signal(signal.SIGTERM, term)
	print('pid', os.getpid(), 'listening on :8000')

	sel = selectors.DefaultSelector()
	sel.register(sock, selectors.EVENT_READ)
	while keep_going:
		events = sel.select(1)
		if events:
			conn, addr = sock.accept()
			with conn:
				handle_client(conn)
	print('cleaning up')
	sock.close()

def hup(signum, frame):
	sock.set_inheritable(True)
	os.execl(sys.argv[0], sys.argv[0], str(sock.fileno()))

def term(signum, frame):
	global keep_going
	keep_going = False

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
