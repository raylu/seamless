#!/usr/bin/env python3

import ctypes
import ctypes.util
import errno
import os
import selectors
import signal
import socket
import sys

libc = ctypes.CDLL(ctypes.util.find_library('c'))
sock = None
keep_going = True
worker_pid = None

def main():
	global sock, worker_pid
	if len(sys.argv) == 2:
		fd = int(sys.argv[1])
		print('inheriting', fd)
		sock = socket.socket(fileno=fd) # sock is now non-inheritable
	else:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.bind(('', 8000))
		sock.listen(4)
	print('pid', os.getpid(), 'listening on :8000')

	worker_pid = os.fork()
	if worker_pid:
		master()
	else:
		worker()

def master():
	set_proc_title('seamless master')
	signal.signal(signal.SIGHUP, hup)
	signal.signal(signal.SIGTERM, master_term)
	while True:
		try:
			os.wait()
		except ChildProcessError as e:
			if e.errno == errno.ECHILD:
				break
			else:
				raise

def worker():
	set_proc_title('seamless worker')
	signal.signal(signal.SIGTERM, worker_term)
	set_pdeathsig(signal.SIGTERM)
	if os.getppid() == 1: # re-parented to init
		sys.exit('master died before we set pdeathsig; exiting')

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
	os.kill(worker_pid, signal.SIGTERM)
	sock.set_inheritable(True)
	os.execl(sys.argv[0], sys.argv[0], str(sock.fileno()))

def master_term(signum, frame):
	os.kill(worker_pid, signal.SIGTERM)

def worker_term(signum, frame):
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
	#print('recv', req, 'send', content.rstrip('\n'))
	conn.close()

def set_proc_title(prname):
	PR_SET_NAME = 15
	prname = prname.encode('ascii')
	prbuf = ctypes.create_string_buffer(len(prname) + 1)
	prbuf.value = prname
	r = libc.prctl(PR_SET_NAME, ctypes.byref(prbuf), 0, 0, 0)
	if r != 0:
		raise Exception('prctl for PR_SET_NAME returned %r' % r)

def set_pdeathsig(sig):
	PR_SET_PDEATHSIG = 1
	r = libc.prctl(PR_SET_PDEATHSIG, sig.value, 0, 0, 0)
	if r != 0:
		raise Exception('prctl for PR_SET_PDEATHSIG returned %r' % r)

if __name__ == '__main__':
	main()
