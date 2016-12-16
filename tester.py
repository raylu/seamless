#!/usr/bin/env python3

import signal
import subprocess
import sys
import threading
import time
import urllib.request

def main():
	server = subprocess.Popen(['./seamless.py'])
	time.sleep(0.1)
	for _ in range(4):
		t = threading.Thread(target=checker)
		t.start()
	print('waiting 1 second')
	time.sleep(1)
	print('sending HUP')
	server.send_signal(signal.SIGHUP)
	time.sleep(1)
	print('done!')
	server.terminate()
	sys.exit()

def checker():
	while True:
		req = urllib.request.urlopen('http://localhost:8000')
		assert req.read() == b'hello\n'

if __name__ == '__main__':
	main()
