# This program (both files) took me two full days to complete (1 day for
#	everything including sockets except multithreading, another day for
#	implementing fixes to multithreading). Dec 26 2023 - Dec 27 2023.

# Program to demonstrate a bank account that stores and modifies whole-dollar
#	amounts of money (no floats) and works across multiple connections (i.e.,
#	multiple clients), as long as the server stays up and running.
#	Multiple clients will all share the same bank account.
#	By clients, I do not mean customers, I mean server-client clients.
#		One customer could be three different clients (an iPad, laptop, phone).

### EXECUTION
# Windows:
# Run server.py by opening command prompt (not python interpreter!)
#	(Windows key-> Type in "cmd" then press Enter key->
#	Type "cd directoryWhere_server.py_is", then Enter key->
#	Type "python server.py" then Enter key)
#	E.g., cd C:\Users\Jeff\Homeworks\Hw6
#	python server.py

# Run client.py by opening another command prompt (not python interpreter!)
#	(Windows key-> Type in "cmd" then press Enter key->
#	Type "cd directoryWhere_client.py_is", then Enter key->
#	Type "python client.py" then Enter key)
#	E.g., cd C:\Users\Jeff\Homeworks\Hw6
#	python client.py

# Linux:
# All that changes is using tmux (terminal multiplexer) instead of multiple
#	command prompts (same result), changing to Unix-style directories
#	(forward slashes), and using "python3" instead of "python" to run both
#	server.py and client.py
# https://www.howtogeek.com/671422/how-to-use-tmux-on-linux-and-why-its-better-than-screen/

# To exit any client or server, press Ctrl+C ON THE CLIENT PROCESSES FIRST, then on the server.
# The server will only shutdown once all client connections have been shutdown AND the server has
#	been actively killed (Ctrl+C). The server doesn't shutdown by itself (which is by design).
# If that doesn't work, press the X on the window or use Task Manager to kill (End Task) the process.

# Linux: Shutdown an inaccessible process
#	(e.g., terminal is gone, maybe because of computer shutdown/restart):
# If server is still running but you don't have access to that command prompt/terminal
#	anymore, then `ps -u yourUsername` or `ps -u yourUsername | grep python3`.
#	Look for the process(es) (i.e., row(s)) that has `python3`.
#	This (or these) is PROBABLY the process you want to kill, if you know you
#	shouldn't have any other python processes running.
#	In that row, memorize the PID (Process IDentifier) #.
#	Now end that process by `kill PID#thatYouJustMemorized`, repeating for other
#	python3 processes as needed.
# E.g.,
#	ps -u jeff | grep python3
#	kill 26907
# https://www.howtogeek.com/413213/how-to-kill-processes-from-the-linux-terminal/


### BUG-FIXING FOR PPL WHO MODIFY THIS CODE
# If you get either of the following errors in the client.py file:
#	clientSock.connect((HOST, PORT))
#	socket.gaierror: [Errno 11001] getaddrinfo failed
# or
#	clientSock.connect((HOST, PORT))
#	ConnectionRefusedError: [WinError 10061] No connection could be made because
#		the target machine actively refused it
# , then make sure you're running server.py before running client.py .
# If you've ensured that, then wait at least .5 to 5 minutes for the port to be
#	freed by the Operating System for general use again.

# If you get missing/delayed (delayed=only pops up after telling client to send
#	a new command to the server, creating a backlog of commands that the client
#	receives msgs about one at a time) messages on a client (when using more than
#	one client) after server sends a message, regardless of whether the command
#	is valid or invalid:
#	With only one client, everything works correctly.
#	The client gets stuck on client_socket.recv() because the server sends the
#		message to the other client instead of the client that made the request.
#	Fix: lock()ing the threads when distributing messages. I'm using a shared
#		Account, per the instructions that require bank balance to be maintained
#		between connections. I think that sending the message to the wrong
#		client is due to the shared account getting its client updated by
#		differing threads, but I only want the balance to be shared, not the
#		client; to accomplish this, I just update the account's socket a lot.