"""
Common Stub Package
"""

from threading import Thread
import os ,sys ,json,hashlib,tempfile,socket

ThreadedNetworkFolder = os.path.dirname(os.path.abspath('../ThreadedNetwork'))
if ThreadedNetworkFolder not in sys.path:
    sys.path.insert(0,ThreadedNetworkFolder)

from ThreadedNetwork import connection as ThCon

class StubThread(Thread):
    """
    Thread Class for handling incomeing connection requests.
    As long as the thread is running it will listen for new connections. 
    """

    def __init__(self,stub):
        Thread.__init__(self)
        self.stub = stub
    
    def run(self):        
        print 'Server Stub Listening'
        while self.stub.alive :
            self.stub.listen_socket.listen(1)
            con,data = self.stub.listen_socket.accept()

            self.stub.unamed_connected_stubs.append(ConnectedStub('',ThCon.Connection(con),self.stub.process))


class ConnectedStub():
    def __init__(self,Name,Connection,callback=None):
        self.name = Name
        self.connection = Connection
        self.connection.call = self.callback
        self.connection.start_channel_threads()
        
        self.folder = '.'
        self.call = callback

    def send(self,data):
        self.connection.send(data)

    def callback(self,input_line):
        self.call(input_line,self)

class CommonStub(object):

    def connect(self):
        self.connection = ThCon.Connection(None,self.process)
        self.connection.connect(self.server_address,self.server_port)
        self.connection.send(json.dumps({'cmd':'NAME','data':self.name}))
    
    def start_listening(self):
        self.listen_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.listen_socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
       

    def get_thread(self,auto_start=False):
        st = StubThread(self)        
        if auto_start : st.start_new
        return st

    def send(self,data):
        self.connection.send(data)

    def shutdown(self):
        self.connection.close()
        self.alive = False


    def send_file(self,data,without=None,to=None):
        dir_name = os.path.dirname(data)
        file_name = os.path.basename(data)
        print 'sending file',file_name
        f = open(os.path.join(dir_name,file_name),'r')

        for l in f:
            if without : self.send_to_all(json.dumps({'cmd':'FILE','data':{'file_name':data ,'line': l}}),without)
            elif to    : self.send(to,json.dumps({'cmd':'FILE','data':{'file_name':data ,'line': l}}))
            else       : self.send(json.dumps({'cmd':'FILE','data':{'file_name':file_name ,'line': l}}))
        # l = f.readlines()
        # if without : self.send_to_all(json.dumps({'cmd':'FILE','data':{'file_name':data ,'line': l}}),without)
        # else       : self.send(json.dumps({'cmd':'FILE','data':{'file_name':file_name ,'line': l}}))
        
        f.close()
        if without : self.send_to_all(json.dumps({'cmd':'FILE','data':{'file_name':data ,'line':'_EOF_'}}),without)
        elif to    : self.send(to,json.dumps({'cmd':'FILE','data':{'file_name':data ,'line':'_EOF_'}}))
        else       : self.send(json.dumps({'cmd':'FILE','data':{'file_name':file_name ,'line':'_EOF_'}}))

    def check_file(self,data,file_type='',without=None):
        dir_name = os.path.dirname(data)
        file_name = os.path.basename(data)
        print 'Checking file',file_name
        md5 = get_md5(os.path.join(dir_name,file_name))

        if without : self.send_to_all(json.dumps({'cmd':'CHECK_FILE','data':{'file_name':data ,'md5':md5,'file_type':file_type}}),without)
        else       : self.send(json.dumps({'cmd':'CHECK_FILE','data':{'file_name':data ,'md5':md5,'file_type':file_type}}))

    def proccess_check_file(self,data,folder=None):

        print 'Checking File in',
        filename = data['file_name']
        filename = os.path.join(folder,os.path.basename(filename))
        print filename
        check_ok = False
        if os.path.exists(filename):
            md5 = get_md5(filename)
            print md5
            print data['md5']
            if md5 == data['md5']:
                check_ok = True
                print 'file exists'

        return check_ok

def load_settings(conf_file):
    conf = ''
    with open(conf_file,'r') as f:
        for l in f : conf+= l.replace('\n','')
    conf = json.loads(conf)
    return conf

def save_settings(conf_file,conf):
    with open(conf_file ,'w') as f:
        f.write(json.dumps(conf))
        f.flush()
        



def get_md5(data):
    print 
    md5 = hashlib.md5()
    with open(data,'rb') as f:
        for chunk in iter(lambda:f.read(128),''):
            md5.update(chunk)
    return md5.hexdigest()
    

def parse_module(data):
    dir_name = os.path.dirname(data)
    file_name = os.path.basename(data)

    f = open(os.path.join(dir_name,file_name),'r') 
    tf = os.path.join(tempfile.gettempdir(),file_name)
    w = open(tf,'w')
    in_func = False

    w.write('import common\n\n')

    for l in f:
        if in_func: 
            mod_name  = file_name[:-3]
            func_name = l[3:l.find('(')].replace(' ','')
            prams     = l[l.find('((') + 2 : l.find('))')]
            w.write(l)
            w.write('\treturn common.request("'+mod_name+ '","'+ func_name +'",['+prams+  '])\n\n')
            w.flush()
            in_func = False
            
        in_func = '%function%' in l
        
    w.flush()
    w.close()
    f.close()
    print 'file parssed'
    return tf

