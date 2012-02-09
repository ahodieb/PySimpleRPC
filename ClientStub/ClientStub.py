#!/usr/bin/env python

import socket,os,sys,types,json,uuid,imp
from optparse import OptionParser


ThreadedNetworkFolder = os.path.dirname(os.path.abspath('../ThreadedNetwork'))
if ThreadedNetworkFolder not in sys.path:
    sys.path.insert(0,ThreadedNetworkFolder)

CommonStubFolder = os.path.dirname(os.path.abspath('../Common'))
if CommonStubFolder not in sys.path:
    sys.path.insert(0,CommonStubFolder)

from ThreadedNetwork import connection as ThCon
from Common      import CommonStub as cStub
StubThread = cStub.StubThread

class ClientStub(cStub.CommonStub):
    def __init__(self,conf):

        self.config = conf
        self.listen_socket = None

        self.local_apps = []    
        self.unamed_connected_stubs=self.local_apps      
        self.connection = None
        self.alive = True

        self.FILE_HANDLERS = dict()
        self.RPC_CALLS = dict()
    
    def connect(self):
        self.connection = ThCon.Connection(None,self.process)
        self.connection.connect(self.config['ip'],self.config['port'])
        self.connection.send(json.dumps({'cmd':'NAME','data':self.config['name']}))
    
    def start_listening(self):
        super(ClientStub,self).start_listening()
        self.listen_socket.bind(('127.0.0.1',self.config['app_port']))

    def reg_module(self,data):
        pm = cStub.parse_module(data)
        self.check_file(pm,'reg_mod')

    def process(self,input_line,caller=None):
        i = json.loads(input_line)
        cmd  = i['cmd']
        data = i['data']

        if cmd == "send" or cmd =='s':
            self.send(json.dumps({'cmd':'MSG','data':data}))

        elif cmd == '_end_':
            self.shutdown()
            os._exit(0)

        elif cmd == 'disconnected':
            if isinstance(caller,type(None)):
                self.shutdown()
                os._exit(0)
            else :  print 'App Dissconnected'

        elif cmd == 'parse_module' or cmd == 'pm':
            print cStub.parse_module(data)

        elif cmd == 'send_file' or cmd == 'sf':
            self.send_file(data)
        
        elif cmd == 'check_file' or cmd == 'cf':
            self.check_file(data)

        elif cmd == 'reg_module' or cmd =='rm':
            self.reg_module(data)
            mod = {os.path.basename(data):data}
            if 'reg_mods' in self.config :
                self.config['reg_mod'][os.path.basename(data)] = data
            else : self.config['reg_mod'] = mod
        
        elif cmd == 'save_config' or cmd == 'sc':
            cStub.save_settings(data,self.config)
            print 'config saved'

        elif cmd == 'RPC_REQUEST' :
            d = json.loads(data)

            RPC_ID = d['RPC_ID']

            self.RPC_CALLS[RPC_ID] = caller #{'source':caller,'result':None}
            self.send(json.dumps({'cmd':'RPC_CALL','data':data}))
        
        elif cmd == 'RPC_RESULT' or cmd == 'RPC_EXCEPTION':
            d = json.loads(data)
            source = self.RPC_CALLS[d['RPC_ID']]
            source.send(data)

            if cmd == 'RPC_RESULT':
                print 'rpc result back',d['RPC_RESULT']
            elif cmd == 'RPC_EXCEPTION':
                print 'Exception has happened' ,d['RPC_EXCEPTION']                

####################                       #####################

        elif cmd == 'MSG':
            print data
        
        elif cmd == 'NAME_ERROR':
            print 'Error , Name is not unique, shutting down....'
            self.config['name'] += '_'
            #self.name = self.name+'_'
            self.send(json.dumps({'cmd':'NAME','data':self.config['name'] }))

        elif cmd == 'CHECK_FILE':
            check_ok = self.proccess_check_file(data,self.config['reciving_dir'])
            if check_ok : self.send(json.dumps({'cmd':'CHECK_FILE_OK','data':{'file_name':data['file_name'],'file_type':data['file_type']}}))
            else        : self.send(json.dumps({'cmd':'CHECK_FILE_NOK','data':{'file_name':data['file_name'],'file_type':data['file_type']}}))
                
       
        elif cmd == 'CHECK_FILE_OK':
            print data['file_name'] ,'ok'
            if data['file_type'] == 'reg_mod':
                self.send(json.dumps({'cmd':'REG_MODULE','data':os.path.basename(data['file_name'])}))
        
        elif cmd == 'CHECK_FILE_NOK':
            print data['file_name'] ,'not ok','resending ...'
            self.send_file(data['file_name'])    
            if data['file_type'] == 'reg_mod':
                self.send(json.dumps({'cmd':'REG_MODULE','data':os.path.basename(data['file_name'])}))    
       
        elif cmd == 'FILE':
            filename = data['file_name']
            print 'reciving ' ,filename
            if not filename in self.FILE_HANDLERS:
                self.FILE_HANDLERS[filename] = open(os.path.join(self.config['reciving_dir'],filename),'w')     
                           
            f = self.FILE_HANDLERS[filename]
            if not data['line'] == '_EOF_':
                f.write(data['line'])
            else : 
                f.flush()
                f.close
                self.FILE_HANDLERS.pop(filename)
                print 'file',filename,'recived'

        elif cmd == 'RPC_CALL':

            data = json.loads(data)
            mod_name = data['mod_name'] +'.py'
            mod_path = self.config['reg_mod'][mod_name]
            func_name = data['func_name']
            prams = data['prams']
            RPC_ID = data['RPC_ID']

            print 'RPC incoming',mod_name,func_name,prams

            try:
                
                f ,fn ,dsc = imp.find_module(mod_name[:-3],[os.path.dirname(mod_path)])
                mod = imp.load_module(mod_name,f,fn,dsc)

                print mod

                f = None
                for a in dir(mod):
                    f = mod.__dict__.get(a)
                    if isinstance(f,types.FunctionType):
                        if f.func_name == func_name:
                            break
                if not f.func_name  == func_name:
                    raise Exception('Function not found.')

                result = f(prams)
                result = json.dumps({'RPC_ID':RPC_ID,'RPC_RESULT':result})

                self.send(json.dumps({'cmd':'RPC_RESULT','data':str(result)}))
                #print result

            except Exception as e:
                exc_type , exc_obj , exc_tb  = sys.exc_info()
                self.send(json.dumps({'cmd':'RPC_EXCEPTION','data':json.dumps({'RPC_ID':RPC_ID,'RPC_EXCEPTION':str(e) + ', in line ' + str(exc_tb.tb_lineno)})}))
                print e
            # finally:
            #     f.close()
                
        elif cmd == '_end_' : 
            self.shutdown()
            print 'Shutdowwn Command Sent'
            os._exit(0)

        else :
            print '<',input_line

def main():
    print 'Client STUB PID : ',os.getpid()

    parser = OptionParser()
    parser.add_option('-a','--address',dest='address',default='',type='string',help='Server Stub address.')
    parser.add_option('-p','--port'   ,dest='port' ,default=0,type='int',help='Server Stub port.')
    parser.add_option('-q','--application_port'   ,dest='app_port' ,default=8765,type='int',help='Application Execution Port.')
    parser.add_option('-n','--name',dest='name'  ,default = '',type='string',help='Client name to be recognized at the Server Stub, note that the name must be unique , or the connection will fail.')
    parser.add_option('-l','--live_console'    ,dest='live_console',default =False,action='store_true',help='Activate the live console for the server stub.')
    parser.add_option('-c','--config_file' ,dest='conf_file',default='./conf',help='Configration file to save commonly used settings.')
    parser.add_option('-d','--reciving_dir' ,dest='reciving_dir',default='./',help='Directory in which you recive the parsed modules.')

    (options,args) = parser.parse_args()

    conf_file = options.conf_file
    if os.path.exists(conf_file):

        conf = cStub.load_settings(conf_file)

        if 'ip'   in conf : ip   = conf['ip']
        if 'port' in conf : port = conf['port']
        if 'app_port' in conf : app_port = conf['app_port']
        if 'name' in conf : name = conf['name']
        if 'live_console' in conf : live_console = conf['live_console']
        if 'reciving_dir' in conf : reciving_dir = conf['reciving_dir']


    else:    

 
            
        ip = options.address
        port = options.port
        app_port = options.app_port
        name = options.name
        live_console = options.live_console
        reciving_dir = options.reciving_dir

        if ip == '':
            ip   = raw_input('Server IP :')

        if port == 0:
            port = int(raw_input('Port  :'))   
        
        if name =='':
            name = raw_input('Name:')    

        conf = dict()
        conf['ip'] = ip
        conf['port'] = port
        conf['app_port'] = app_port
        conf['name'] = name
        conf['live_console']=live_console
        conf['reciving_dir']= reciving_dir





    d = os.path.dirname(reciving_dir)
    if not os.path.exists(d):
        os.makedirs(d)

    stub = ClientStub(conf)
    stub.connect()
    stub.start_listening()
    stub_th = stub.get_thread()
    stub_th.start()

    while live_console :
        cmd = raw_input('>')
        place = cmd.find(':')
        data = ''

        if place > -1 :
            data = cmd[place+1:]
            cmd  = cmd[:place] 
        stub.process(json.dumps({'cmd':cmd,'data':data}))            
if __name__ == '__main__':
    main()
