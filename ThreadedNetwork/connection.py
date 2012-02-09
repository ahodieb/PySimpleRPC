import input_channel  as ic
import output_channel as oc
import socket

class Connection ():

	def callback(self,Msg):
		#print 'conn,callback',Msg
		if not Msg == '':
			if self.call : self.call(Msg)
		else:
			if self.call :
				if not self.disconnected:
					self.disconnected = True
					self.call('{"cmd": "disconnected", "data": ""}')

	def __init__(self,connection = None,callback=None):
		if not connection:self.connection     = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		else : self.connection = connection
		self.input_channel  = ic.InputChannel(self.connection,self.callback)
		self.output_channel = oc.OutputChannel(self.connection)

		self.call = callback
		self.disconnected = False

	def send(self,data):
		self.output_channel.send(data)
	
	def close(self):
		self.input_channel.alive = False
		self.output_channel.alive = False
		self.alive = False		
		self.disconnected=True
		#self.input_channel.join()
		#self.output_channel.join()
		self.connection.close()

	def start_channel_threads(self):
	    self.input_channel.start()
	    self.output_channel.start()


	def connect(self,add,port):
		self.connection.connect((add,port))
		self.start_channel_threads()





