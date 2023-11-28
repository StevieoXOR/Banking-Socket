# For instructions on running/execution, bugfixing, and purpose,
#	see readme.txt

import socket
import threading	# For handling multiple connections (multiple sockets)
import sys			# For MAX_INT


#####
class Account:
	# Constructor
	def __init__(self, clientSocket):
		self.balance = int(100)	# Initial balance
		self.clientSock = clientSocket
		self.BAD_DATATYPE = sys.maxsize	# maximum value for an int in python3


	def msgClient(self, msg):
		print("\nmsgClient(msg) reached")
		print("msg:\n",msg)
		self.clientSock.sendall( str.encode(msg))	# String to bytes, then transmit
		print("Successfully sent msg to Client")

	def getClientPrompt(self):
		m = ("\tType commands in the format 'deposit 100' to deposit $100.00 into your account.\n"
			"\tType commands in the format 'withdraw 100' to withdraw $100.00 from your account.\n"
			"\tOverdrafts (negative balances) are not allowed.\n"
			"\tType 'balance' to check your account's balance.\n"
			"\tFloating point #s (numbers that have values after the decimal point) are not allowed, including 'withdraw 97.' .\n"
			"\tDO NOT type '$' anywhere.\n"
			"\tPress CTRL and then C together (Ctrl+C) to exit this app.\n")
		return m

	def msgClientAboutFailure(self, failure_description):
		new_string = failure_description + self.getClientPrompt() + "Your balance has not been modified.\n"
		self.msgClient(new_string)


	def checkDataType(self, amount):
		try:
			amount_num = int(amount)
			if amount_num == self.BAD_DATATYPE:
				self.msgClientAboutFailure("You entered a privileged number, which is not allowed. Try again.\n")
				return self.BAD_DATATYPE	# Use this to check in other functions to stop execution in those other functions
		except:
			self.msgClientAboutFailure("You entered a non-integer number. Floats are not allowed. Try again.\n")
			return self.BAD_DATATYPE	# Use this to check in other functions to stop execution in those other functions
		return amount_num


	def deposit(self, amountToDeposit):
		amount_num = self.checkDataType(amountToDeposit)
		if amount_num == self.BAD_DATATYPE:
			# Don't print an error message because that would mean two messages get
			#	sent instead of one, screwing up the 1-to-1 msg send-to-receive
			#	ratio and forcing messages to get queued (delayed)
			return
		if amount_num < 0:
			self.msgClientAboutFailure("Cannot deposit a negative amount of money. Try again.\n")
			return
		
		self.balance += amount_num
		self.msgClient(f"Successfully deposited ${amount_num}.\n")

	def withdraw(self, amountToWithdraw):
		amount_num = self.checkDataType(amountToWithdraw)
		if amount_num == self.BAD_DATATYPE:
			# Don't print an error message because that would mean two messages get
			#	sent instead of one, screwing up the 1-to-1 msg send-to-receive
			#	ratio and forcing messages to get queued (delayed)
			return
		if amount_num < 0:
			self.msgClientAboutFailure("Cannot withdraw a negative amount of money. Try again.\n")
			return
		
		if self.balance - amount_num < 0:
			self.msgClientAboutFailure("Cannot overdraw (overdraft). Insufficient funds. Try again.\n")
			return
		
		self.balance -= amount_num
		self.msgClient(f"Successfully withdrew ${amount_num}.\n")

	# Expects `raw_recvd_msg` to be a regular string (not byte encoded)
	def processReturnedData(self, raw_recvd_msg):
		# Split string into tokens (words), separating each token by a ' ' character
		words = raw_recvd_msg.split(' ')
		print("raw_recvd_msg from Client:",raw_recvd_msg)
		print("words in msg from Client:",words)
		command = words[0]
		amount = "0"
		if len(words) > 2:
			self.msgClientAboutFailure("ERROR: More than two arguments given.\n"
				"Unknown command. Expected either one or two arguments\n"
				"- argument1={'balance','deposit','withdraw'}\n"
				"- argument2={None,someAmountOfMoneyLike97}, the two arguments separated by a space character.\n"
				"Try again.\n")
			return
		elif len(words) == 2:
			amount = words[1]
		
		if   (command == "balance"  and  len(words) == 1):
			self.msgClient(f"Balance: ${self.balance}\n\n")
		elif (command == "deposit"  and  len(words) == 2):
			self.deposit(amount)
		elif (command == "withdraw" and  len(words) == 2):
			self.withdraw(amount)
		else:
			self.msgClientAboutFailure("ERROR: Unknown command. Expected either one or two arguments\n"
				"- argument1={'balance','deposit','withdraw'}\n"
				"- argument2={None,someAmountOfMoneyLike97}, the two arguments separated by a space character.\n"
				"Try again.\n")
			return
#####


# Creating addresses with ports
server_AddressPort = ("", 9090)			# (HOST,PORT)  all interfaces, Arbitrary non-privileged port 9090
# client_AddressPort = ("localhost", 9091)
msgBufferSize = 4096
numMaxUnacceptedConnectionsInQueue = 2
active_threads = []


def handle_client(connSock, addressOfConn):
	print('Connected by', addressOfConn)
	acc = Account(clientSocket=connSock)
	acc.msgClient( acc.getClientPrompt() )

	# Extremely important note: the loop below expects EXACTLY one message to be sent
	#	every loop iteration. Not 0, not 2 or 3 or 4 or ...
	while True:
		msgRecvdAsBytes = connSock.recv(msgBufferSize)
		if len(msgRecvdAsBytes) == 0: break

		msgRecvdAsStr = msgRecvdAsBytes.decode('utf-8')	# Bytes to string
		print("Message from client:", msgRecvdAsStr,"\n")
		acc.processReturnedData(msgRecvdAsStr)
	connSock.close()


# Server socket order: .socket(IPv4/6, TCP/UDP), .bind((addressesToListenFrom,sharedPort)),
#	.listen(max#unacceptedConnections), .accept()
# Client socket order: .socket(IPv4/6, TCP/UDP), .connect((serverAddress,sharedPort))
# AF = AddressFamily, INET=Internet, AF_INET = IPv4, AF_INET6 = IPv6, SOCK_STREAM = TCP

# Create server socket (specifically for listening to new clients, not all the Account processing gruntwork)
server_listeningSock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
if socket.has_ipv6:
	# Overwrite socket, making it use IPv6 if supported
	server_listeningSock = socket.socket(family=socket.AF_INET6, type=socket.SOCK_STREAM)

server_listeningSock.bind(server_AddressPort)
server_listeningSock.listen(numMaxUnacceptedConnectionsInQueue)

try:
	while True:
		# Accept a new connection
		connSock, addressOfConn = server_listeningSock.accept()

		# Create a new thread to handle the connection, add it to list of active threads, then run that thread
		# target = Function to make thread run, args = arguments for the function that thread will run
		client_handler = threading.Thread(target=handle_client, args=(connSock, addressOfConn))
		active_threads.append(client_handler)
		client_handler.start()	# thread.start()
except KeyboardInterrupt:
	print("Ctrl+C has been pressed on the server's end.")

	# Wait for all threads to finish before exiting
	for thread in active_threads:
		thread.join()
	print("All clients have finished executing. Server is shutting down.")
	

	server_listeningSock.close()