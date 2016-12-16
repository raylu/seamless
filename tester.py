#!/usr/bin/env python3

import signal
import socket
import subprocess
import threading
import time

keep_going = True

def main():
	global keep_going
	server = subprocess.Popen(['./seamless.py'])
	time.sleep(0.1)
	threads = []
	for _ in range(4):
		t = threading.Thread(target=checker)
		t.start()
		threads.append(t)
	print('waiting 1 second')
	time.sleep(1)
	print('sending HUP')
	server.send_signal(signal.SIGHUP)
	time.sleep(1)
	print('tester cleaning up')
	keep_going = False
	for t in threads:
		t.join()
	server.terminate()
	time.sleep(1)

def checker():
	while keep_going:
		with socket.create_connection(('localhost', 8000), 1) as sock:
			time.sleep(0.1)
			sock.sendall(b'GET / HTTP/1.1\r\nHost: localhost:8000\r\n\r\n')
			data = sock.recv(1024)
			assert data, 'got %r' % data
			body = data.split(b'\r\n\r\n', 2)[1]
			assert body == b'hello\n'

if __name__ == '__main__':
	main()
