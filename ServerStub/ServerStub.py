#!/usr/bin/env python

import socket,os,sys,time,json,uuid
from optparse import OptionParser

ThreadedNetworkFolder = os.path.dirname(os.path.abspath('../ThreadedNetwork'))
if ThreadedNetworkFolder not in sys.path:
    sys.path.insert(0,ThreadedNetworkFolder)

CommonStubFolder = os.path.dirname(os.path.abspath('../Common'))
if CommonStubFolder not in sys.path:
    sys.path.insert(0,CommonStubFolder)

from ThreadedNetwork import connection as ThCon
from Common     import CommonStub as cStub
StubThread = cStub.StubThread
    
class ServerStub(cStub.CommonStub):
    def __init__(self,conf):
        
        self.config = conf
        self.listen_socket = None
        self.alive = True
        self.unamed_connected_stubs = []
        self.connected_stubs = dict()
        self.RPC_MODULES = dict() 
        self.RPC_CALLS   = dict()        
        self.file_handlers = dict()        

    def start_listening(self):
        super(ServerStub,self).start_listening()
        self.listen_socket.bind((self.config['ip'],self.config['port']))

    def send(self,client_name,data):
        self.connected_stubs[client_name].send(data)

    def send_to_all(self,data,without=None):
        print without
        dont_send_to = []

        if without: 
            dont_send_to.extend(without)

        for con_stub in self.connected_stubs:
            if con_stub not in dont_send_to:

                self.connected_stubs[con_stub].send(data)
                
    def process(self,input_line,caller=None):
        i = json.loads(input_line)
        cmd  = i['cmd']
        data = i['data']

        if cmd == 'NAME':
            caller.name = data
            
            if data in self.connected_stubs : 
                caller.send(json.dumps({'cmd':'NAME_ERROR','data':''}))
                caller.name = ''

            else:
                self.unamed_connected_stubs.remove(caller)
                self.connected_stubs[data] = caller
                print data ,'connected'
        
        if cmd == 'MSG':
            print caller.name + ':',data

        elif cmd == 'CHECK_FILE':
            check_ok = self.proccess_check_file(data,caller.folder)
            if check_ok : caller.send(json.dumps({'cmd':'CHECK_FILE_OK','data':{'file_name':data['file_name'],'file_type':data['file_type']}}))
            else        : caller.send(json.dumps({'cmd':'CHECK_FILE_NOK','data':{'file_name':data['file_name'],'file_type':data['file_type']}}))
                
        elif cmd == 'FILE':
            filename = data['file_name']

            print 'reciving ' ,filename
            if '.parsed' in filename:
                filename = filename[:filename.find('.parsed')]

            if not filename in self.file_handlers:
                self.file_handlers[filename] = open(os.path.join(caller.folder,filename),'w')
                
            f = self.file_handlers[filename]

            if not data['line'] == '_EOF_':
                f.write(data['line'])
            else : 
                f.flush()
                f.close
                self.file_handlers.pop(filename)
                print 'file',filename,'recived'

        elif cmd == 'disconnected':
            print caller.name ,'was disconnected.'
            if caller.name in self.connected_stubs:
                self.connected_stubs.pop(caller.name)     
                
            to_pop = []
            for c_s in self.RPC_MODULES :
                if self.RPC_MODULES[c_s].name == caller.name : to_pop.append(c_s)
            print 'removing modules by stub '
            for i in to_pop :
                print '>>',i
                self.RPC_MODULES.pop(i)

        elif cmd == 'RPC_RESULT' or cmd == 'RPC_EXCEPTION' :
            d = json.loads(data)

            source = self.RPC_CALLS[d['RPC_ID']]['source']
            source.send(input_line)
        
        elif cmd == 'REG_MODULE':
            self.RPC_MODULES[data[:-3]] = caller
            self.check_file(os.path.join(caller.folder,data),'reg_mod',[caller.name])
            print 'Module Regestersd from ',caller.name
        
        elif cmd == 'CHECK_FILE_OK':
            print data['file_name'] ,'ok'
            
        elif cmd == 'CHECK_FILE_NOK':
            print data['file_name'] ,'not ok','resending ...'
           #################
           ################
           ############
           ######calller is the one to send to 
            self.send_file(data['file_name'],to = caller.name)    

                

####################                       #####################
    
                    
        if cmd == 'send_to_all' or cmd == 'sta':
            self.send_to_all(json.dumps({'cmd':'MSG','data':data}))
    
        elif cmd == 'who_is_in' or cmd == 'wii':
            for con_stub in self.connected_stubs:
                print con_stub

            for reg_mod in self.RPC_MODULES:
                print reg_mod

        elif cmd == 'send_file':
            self.send_file(data)
        
        elif cmd == 'RPC_CALL':
            d = json.loads(data)
            mod_name = d['mod_name']
            RPC_ID = d['RPC_ID']

            #### to check if the module is still regestierd 
            dist  = self.RPC_MODULES[mod_name]
            self.RPC_CALLS[RPC_ID] = {'source':caller,'dist':dist}
            dist.send(input_line)
    
        elif cmd == '_end_':
            print 'Shutting Down',
            for con_stub in self.connected_stubs:
                self.connected_stubs[con_stub].send('{"cmd": "_end_", "data": ""}')
                print '.',
                #time.sleep(1)
                self.connected_stubs[con_stub].connection.close()
            os._exit(0)



def main():
    print 'Server Stub PID : ',os.getpid()

    parser = OptionParser()
    parser.add_option('-a','--address',dest='address',default='',type='string',help='Set the ip address for the server to bind with.')
    parser.add_option('-p','--port'   ,dest='port',default=0,type='int',help='Set the port of the server stub.')
    parser.add_option('-l','--live_console'   ,dest='live_console',default =False,action='store_true',help='Activate the live console for the server stub.')
    parser.add_option('-c','--config_file',dest='conf_file',default='./conf',help='Configration file to save commonly used settings.')

    (options,args) = parser.parse_args()

    conf_file = options.conf_file
    if os.path.exists(conf_file):
        conf = cStub.load_settings(conf_file)

        if 'ip'   in conf : ip   = conf['ip']
        if 'port' in conf : port = conf['port']
        if 'live_console' in conf : live_console = conf['live_console']
    
    else:
        ip = options.address
        port = options.port
        live_console = options.live_console

        conf = dict()
        conf['ip'] = ip
        conf['port'] = port 
        conf['live_console'] = live_console

    if ip == '':
        ip   = raw_input('Server IP :')

    if port == 0:
        port = int(raw_input('Port  :'))   

    SStub = ServerStub(conf)
    SStub.start_listening()
    SStub_Th = SStub.get_thread()
    SStub_Th.start()    

    while live_console :

        cmd = raw_input('>')
        place = cmd.find(':')
        data = ''

        if place > -1 :
            data = cmd[place+1:]
            cmd  = cmd[:place] 
                    
        SStub.process(json.dumps({'cmd':cmd,'data':data}))

    
if __name__ == '__main__':
	main()
