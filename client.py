# For instructions on running/execution, bugfixing, and purpose,
#	see readme.txt

import socket

# The remote (server) host (don't use 127.0.0.1, which is specific to IPv4. Using 'localhost' works with both IPv4 and IPv6)
# HOST = 'localhost'	# Easy way that doesn't ever need to be changed based on IPv4 vs IPv6
PORT = 9090				# The same port as used by the server

msgBufferSize = 4096

# Server socket order: .socket(IPv4/6, TCP/UDP), .bind((addressesToListenFrom,sharedPort)),
#	.listen(max#unacceptedConnections), .accept()
# Client socket order: .socket(IPv4/6, TCP/UDP), .connect((serverAddress,sharedPort))
# AF = AddressFamily, INET=Internet, AF_INET = IPv4, AF_INET6 = IPv6, SOCK_STREAM = TCP
clientSock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
HOST = '127.0.0.1'	# IPv4 localhost address
if socket.has_ipv6:
	# Overwrite socket, making it use IPv6 if supported
	clientSock = socket.socket(family=socket.AF_INET6, type=socket.SOCK_STREAM)
	HOST = '::1'	# IPv6 localhost address

clientSock.connect((HOST, PORT))
print('Connected to server')

# Initial message from server
msgRecvdAsBytes = clientSock.recv(msgBufferSize)
print("Message from server:\n" + msgRecvdAsBytes.decode('utf-8'))

# Extremely important note: the loop below expects EXACTLY one message to be sent
#	every loop iteration. Not 0, not 2 or 3 or 4 or ...
while True:
	userPrompt = "(Note for hackers: pressing Enter before typing anything else freezes the client program but not the server)\n>>>>> "
	msgToSendAsBytes = input(userPrompt)
	clientSock.sendall( str.encode(msgToSendAsBytes) )
	
	msgRecvdAsBytes = clientSock.recv(msgBufferSize)
	if len(msgRecvdAsBytes) == 0: break
	# str.decode(original_encoding_type): Bytes to string
	print("Message from server:\n" + msgRecvdAsBytes.decode('utf-8'))

clientSock.close()