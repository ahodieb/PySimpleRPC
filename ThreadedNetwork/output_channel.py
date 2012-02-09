from threading import Thread
import time

class OutputChannel(Thread):
	def __init__(self,connection):
		Thread.__init__(self)
		self.connection = connection
		
		self.data_queue = []
		self.alive = True

	def __del__(self):
		print 'InputChannel Killed'
		#pass

	def send(self,data):
		self.data_queue.append(data)


	def run(self):
		while self.alive : 
			if len(self.data_queue) > 0 :
				try:
					self.connection.send(self.data_queue.pop(0))
					time.sleep(0.5)	
				except Exception as e:
					print e
					self.alive = False
			

