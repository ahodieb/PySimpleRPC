import socket as s
import json ,uuid


def request(mod_name,func_name,prams=[]):

	app_sock = s.socket(s.AF_INET,s.SOCK_STREAM)
	app_sock.connect(('127.0.0.1',8765))
	RPC_ID = str(uuid.uuid4())

	serialized_data = json.dumps({'RPC_ID':RPC_ID,'mod_name':mod_name,'func_name':func_name,'prams':prams})


	app_sock.send(json.dumps({'cmd':'RPC_REQUEST','data':serialized_data}))
	result = app_sock.recv(2048)
	d = json.loads(result)
	app_sock.close()


	if 'RPC_EXCEPTION' in d:
		raise Exception(d['RPC_EXCEPTION'])

	
	return d['RPC_RESULT']
