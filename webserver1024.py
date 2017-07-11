#Sam Christensen
#webserver1024.py

import sys
import socket
import struct
import select
import os

class webserver:
	running = 1
	myIP = "0.0.0.0"
	myPort = "0000"
	postTargetDirectory = ""

	#Constructor for webserver.
	def __init__(self, InputIP, InputPort):
		self.myIP = InputIP
		self.myPort = InputPort
		self.getServerInfo()

	#Displays Server IP and Port information.
	def getServerInfo(self):
		print("-----------")
		print("My IP: " + self.myIP)
		print("My Port: " + self.myPort)
		print("-----------")

	#Starts Server
	def run(self):
		print("Running...")
		Address = (self.myIP, int(self.myPort))

		print("Creating Socket...")
		sTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sTCP.bind(Address)
		sTCP.listen(5)

		# Sockets from which we expect to read and write
		inputs = [sTCP]
		outputs = [ ]
		completeFlag = -1

		hold = ""

		print("Listening...")
		while inputs:
			readable, writable, exceptional = select.select(inputs, outputs, inputs)
			for s in readable:
				if s is sTCP:
					(clientsocket, address) = sTCP.accept()
					clientsocket.setblocking(0)
					inputs.append(clientsocket)
				else:
					data = s.recv(1024)
					if data:						
						complete = self.isCompleteRequest(data)
						if complete == 1: 

							#Request Area Start.
							array = self.decodeRequest(data)
							code = self.processHeader(array)
							#Request Area End.

							if(code == 200):
								response = self.encodeResponse(array)
								clientsocket.send(response)
								inputs.remove(s)
								s.close()
							else:
								print("Finished with a request!")
								print("Continuing to Listen!")
						else:
							break
												
	#Breaks HTTP request into text.
	def decodeRequest(self, data):
		decodedBin = data.decode('utf-8')
		array = decodedBin.split('\r\n')
		#Uncomment to see all requests that hit the server.
		print("-----------")
		for n in range(0, len(array)):
			print(str(n) + ". " + str(array[n]))
		print("-----------")
		return(array)

	#Checks recieved data for \r\n\r\n
	def isCompleteRequest(self, data):
		decodedBin = data.decode('utf-8')
		if "\r\n\r\n" in decodedBin:
			#print("Complete Request!")
			return(1)
		else:
			#print("Incomplete Request!")
			return(0)
			
	#Decides how to respond to HTTP request. 200 = Success, 404 = File Not Found, 400 Bad Request
	def processHeader(self, array):
		URLString = "NULL"
		#Splits the header line at index 0 on spaces. (GET /index.html HTTP/1.1)
		headerArray = array[0].split(' ')

		#GET
		if headerArray[0] == "GET" and headerArray[2] == "HTTP/1.1":
			URLString = "static" + headerArray[1]

			if(os.path.exists(URLString)):
				return(200)
			else:
				print("ERROR: file not found!")		
				return(404)	

		#POST, would get this as a response from the form html.
		elif headerArray[0] == "POST" and headerArray[2] == "HTTP/1.1":
			contentFlag = 0
			#Checks Content Type
			for i in range(0, len(array)):
				if "Content-Type: application/x-www-form-urlencoded" in array[i]:
					contentFlag = 1				
			if contentFlag == 1:	
				return(200)
			else:
				print("ERROR: bad request!")	
				print("This server requires POST requests to have a certain Content-Type (application/x-www-form-urlencoded)")
				return(400)
		else:
			print("ERROR: bad request!")		
			print("This server only handles HTTP/1.1 GET and POST requests!")
			return(400)

	#Responds to HTTP request, only use if 200 recieved from processHeader.
	def encodeResponse(self, array):
		headerArray = array[0].split(' ')
		#GET
		if headerArray[0] == "GET" and headerArray[2] == "HTTP/1.1":
			response = ""
			response = response + "HTTP/1.1 200 OK\r\n"
			response = response + "Content-Type: text/html\r\n"
			response = response + "\n"
			addressArray = array[0].split(" ")
			address = addressArray[1]
			address = "static" + address
			with open(address, 'r') as inFile:
				 data = inFile.read()
			response = response + data
			response = response.encode('utf-8')
			return(response)

		#POST
		elif headerArray[0] == "POST" and headerArray[2] == "HTTP/1.1":
			count = 0 #This will be used to identify the start of the body.

			#grabs directory
			targetDirectory = headerArray[1]
			targetDirectory = targetDirectory.strip("action=")
			
			for i in range(0, len(array)):
				#Looks for content Length
				if "Content-Length" in array[i]:
					contentLengthLine = array[i];
				#Looks for empty line (because below is body line)
				if "" is array[i]:
					#save count value
					bodyLineNumber = count + 1
				#increment count
				count = count + 1
			#This is where the content of our forms is saved.
			bodyLine = array[bodyLineNumber]
			#Creates array
			bodyLineArray = bodyLine.split("&")
			#Will catch variable names 
			catchArray = [] 
			catchArrayVarNames = []
			for i in range(0, len(bodyLineArray)):
				hold = bodyLineArray[i].split("=")
				if hold[1] is "":
					hold[1] = "??UNKNOWN??"
				hold[1] = hold[1].replace("+", " ")
				hold[1] = hold[1].strip(" ")
				catchArray.append(hold[1])
				catchArrayVarNames.append(hold[0])

			#Adds mustaches.
			for i in range(0, len(catchArrayVarNames)):
				catchArrayVarNames[i] = "{{" + catchArrayVarNames[i] + "}}"

			#Starting HTTP response construction
			#Header
			response = ""
			response = response + "HTTP/1.1 200 OK\r\n"
			response = response + "Content-Type: text/html\r\n"
			response = response + "\n"

			targetDirectory = "static" + targetDirectory
			#print("Target Directory: " + targetDirectory)
			f = open(targetDirectory, "r")
			template = f.read()

			#Body
			#Replaces variables in template with variable names.
			for i in range(0, len(bodyLineArray)):
				template = template.replace(catchArrayVarNames[i], catchArray[i])

			#Returns the modified template.
			response = response + template
			response = response.encode('utf-8')
			return(response)

#Main
if __name__ == '__main__':
	print("Main Start")

	if(len(sys.argv) == 3):
		WS = webserver(sys.argv[1], sys.argv[2])
		WS.run()

	else:
		print("Incorrect Amount of Arguments! (IP, PORT)")
		exit(1)




	
