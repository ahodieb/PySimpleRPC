from threading import Thread
import time

class InputChannel(Thread):
	def __init__(self,connection,callback):
		Thread.__init__(self)
		self.connection = connection
		self.callback = callback
		
		self.alive = True

	def __del__(self):
		print 'InputChannel Killed'
		#pass

	def run(self):
		while self.alive : 
			msg = ''
			try:
				msg = self.connection.recv(1024)
				time.sleep(0.1)
				

			except Exception as e:
				pass 
				#print e
				#self.callback('disconnected')
				#self.alive = False
			self.callback(msg)
			#print 'msg recived :',msg
