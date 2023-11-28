# For instructions on running/execution, bugfixing, and purpose,
#	see readme.txt

import socket		# For connecting client(s) to server
import threading	# For handling multiple connections (multiple sockets)
import sys			# For MAX_INT


#####
class Account:
	# Constructor
	def __init__(self):
		self.balance = int(100)	# Initial balance. This will be shared among all sockets.
		self.clientSock = None	# This will get modified a lot if there is more than one connection.
		self.addrOfSock = None	# This will get modified a lot if there is more than one connection.
		self.BAD_DATATYPE = sys.maxsize	# maximum value for an int in python3
	
	# This will be used for changing sockets when a thread decides to do something
	def updateSockets(self, clientSocketAndItsAddress):
		self.clientSock = clientSocketAndItsAddress[0]
		self.addrOfSock = clientSocketAndItsAddress[1]


	def msgClient(self, msg):
		print(f"\nClient: {self.addrOfSock}")
		print("\nmsgClient(msg) reached")
		print(f"msg:\n{msg}")
		try:
			if self.clientSock:	# If there's a socket to send data to
				self.clientSock.sendall(str.encode(msg))  # String to bytes, then transmit
				print(f"Successfully sent msg to client {self.addrOfSock}\n\n")
			else:
				print("No Client to send data to. Did you forget to re/set the account's sockets?")
		except Exception as e:
			print(f"Error sending message to client {self.addrOfSock}: {e}")

	def getClientPrompt(self):
		m = ("\tType commands in the format 'deposit 100' to deposit $100.00 into your account.\n"
			"\tType commands in the format 'withdraw 100' to withdraw $100.00 from your account.\n"
			"\tOverdrafts (negative balances) are not allowed.\n"
			"\tType 'balance' to check your account's balance.\n"
			"\tFloating point #s (numbers that have values after the decimal point) are not allowed, including 'withdraw 97.'\n"
			"\tDO NOT type '$' anywhere.\n"
			"\tDisallowed: 'withdraw 97.00', 'withdraw 97.', 'withdraw 97.50', 'withdraw 97 dollars',\n"
			"\t  'withdraw $97', and the equivalents for 'deposit'\n"
			"\tPress CTRL and then C together (Ctrl+C) to exit this app.\n")
		return m

	def msgClientAboutFailure(self, failure_description):
		new_string = failure_description + self.getClientPrompt() + "Your balance has not been modified.\n\n"
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
		print(f"raw_recvd_msg from client {self.addrOfSock}: {raw_recvd_msg}")
		print(f"words in msg from client {self.addrOfSock}: {words}")
		command = words[0]
		amount = "0"
		if len(words) > 2:
			self.msgClientAboutFailure("ERROR: More than two arguments given.\n"
				"Unknown command '"+raw_recvd_msg+"'.\n"
				"Expected either one or two arguments\n"
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
			self.msgClientAboutFailure("ERROR: Unknown command '"+raw_recvd_msg+"'.\n"
				"Expected either one or two arguments\n"
				"- argument1={'balance','deposit','withdraw'}\n"
				"- argument2={None,someAmountOfMoneyLike97}, the two arguments separated by a space character.\n"
				"Try again.\n")
			return
#####


IPAddrOfHostsToDistributeTo = ""	# All interfaces
portOfHostsToDistributeTo = 9090	# Arbitrary non-privileged port 9090
hostsToDistributeTo = (IPAddrOfHostsToDistributeTo, portOfHostsToDistributeTo)

msgBufferSize = 4096
numMaxUnacceptedConnectionsInQueue = 2
l = threading.Lock()	# Mutex Lock so threads don't **accidentally** overwrite each other's data
active_threads = []

acc = Account()	# Account(clientSock=None, addrOfSock=None)

# Ensures that messages are sent to the correct socket when using multiple,
#	removing the possibility of other threads **accidentally** tampering
#	with the shared account.
def msgClient_threadSafe(acct:Account, connSock,addressOfConn):
	# l = Thread lock variable that was set up outside this function,
	#	but before this function is called.
	l.acquire()

	# Temp variable to preserve state so that messages are sent to the correct
	#	socket when using multiple threads.
	# Create tuple of Account's socket (which could be (None,None), or could be
	#	an existing Client and its IP Address).
	oldSockAndItsAddr = (acct.clientSock, acct.addrOfSock)

	# Update the shared Account's socket to where messages should/will be sent,
	#	along with socket address info for printing.
	acct.updateSockets( clientSocketAndItsAddress = (connSock,addressOfConn) )

	acct.msgClient( acct.getClientPrompt() )	# All of the surrounding lines are for this one line

	# Restore the original socket so that other threads can have what they expected
	acct.updateSockets( clientSocketAndItsAddress = oldSockAndItsAddr )

	# Release thread lock, allowing other threads to access the passed-in Account
	#	(other threads will wait at l.acquire(), waiting for some thread to call
	#	l.release(), letting a different thread (one of the "other threads") acquire the lock)
	l.release()

def processReturnedData_threadSafe(acct:Account, connSock,addressOfConn, msgRecvdAsStr):
	# Almost identical to other thread-safe function above, except this function uses
	#	processReturnedData() instead of msgClient()
	l.acquire()
	oldSockAndItsAddr = (acct.clientSock, acct.addrOfSock)
	acct.updateSockets( (connSock,addressOfConn) )
	acct.processReturnedData(msgRecvdAsStr)	# All of the surrounding lines are for this one line
	acct.updateSockets( oldSockAndItsAddr )
	l.release()


def handle_client(connSock, addressOfConn):
	print('Successfully connected to client', addressOfConn)

	# Preserve state inside function so that messages are sent to the correct
	#	socket (and by extension the correct client) when using multiple threads
	msgClient_threadSafe(acc, connSock,addressOfConn)

	# Extremely important note: the loop below expects EXACTLY one message to be sent
	#	every loop iteration. Not 0, not 2 or 3 or 4 or ... msgs
	while True:
		msgRecvdAsBytes = connSock.recv(msgBufferSize)
		if len(msgRecvdAsBytes) == 0: break

		msgRecvdAsStr = msgRecvdAsBytes.decode('utf-8')	# Bytes to string
		print(f"Message from client {addressOfConn}: {msgRecvdAsStr}\n")

		# Preserve state inside function so that messages are sent to the correct
		#	socket when using multiple threads and balance doesn't have race cond'ns
		processReturnedData_threadSafe(acc, connSock,addressOfConn, msgRecvdAsStr)
	
	# After thread finishes execution (i.e., client ends session/execution),
	#	close the client<->server socket so that (IPAddress,Port) can be used
	#	by a different process in the future, like the next time this program is run.
	print(f"Closing connection {addressOfConn}\n\n")
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

server_listeningSock.bind(hostsToDistributeTo)
server_listeningSock.listen(numMaxUnacceptedConnectionsInQueue)

try:
	while True:
		# Let the server socket accept a new connection, return the new
		#	connection as connSock and conxn's address as addressOfConn
		connSock, addressOfConn = server_listeningSock.accept()

		# Create a new thread to handle the connection, add it to list of
		#	active threads, then run that thread.
		# target = Function that the thread will run.
		# args = Arguments for the function that the thread will run.
		client_handler = threading.Thread(
			target=handle_client, args=(connSock, addressOfConn[0:2])
		)
		active_threads.append(client_handler)

		# thread.start() Begin execution of the thread's assigned function
		client_handler.start()
except KeyboardInterrupt:
	print("\nCtrl+C has been pressed on the server's end. Server is still running.")

	# Wait for all threads to finish execution before exiting
	for thread in active_threads:
		thread.join()
	print("All clients have finished executing.")

	print("Server is shutting down.")
	server_listeningSock.close()