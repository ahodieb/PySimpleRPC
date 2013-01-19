#PySimpleRPC

during my distributed systems course , i decided to create a simple RPC model that simulated what RPC should do . it got a little bit complex while i was doing it cuz i got somehow excited and did changes to the core system at least twice.


##How it works
* my concept while implementing this RPC was that i want to use functions from a certain module from one client and it runs the code at the server then return me the results, and try to do it without adding any weird code in the application itself , all u have to have is an extra module in ur application and run the client stub and ur good to go.
 
1.  The Server stub runs and starts listening for client stubs to connect. 
2.  A client stub connects to the server stub and starts sharing some basic info like names to identify himself.
3.  The Server Stub receives the info and stores it in a dictionary. and also it checks for duplicate names and if one was found it requests a new name from the client (complexity increased Awesome !!).
4.  You have some commands to show which clients are connected , send them a message and other stuff.
5.  You can have an ongoing shell that u can use to send commands in both the server and client stub, but by default it’s disabled and u can enable them using arguments or saving it in a conf file.
6.  The conf files are used to save ur configurations to use them fast.
7.  To share a module u register it from the client stub. (you have to have the live console)
8.  The client sends the module file to the server in chunks (implemented a very simple file sending function which is very inefficient)
9.	The server receives the file , register it in his modules dictionary , create a parsed version for it and sends this parsed version ( which contains just the headers of the functions and a call to the server stub ) to the rest of the connected clients.
10. Any new client who connects will start receiving md5 checksums of the parsed modules from the server if its not found or changed , the server starts re-sending the file.
11. When an app wants to use the module on the server u have sendingto import the pasrsed module and also import the common.py module which has a small server which connects to the client stub and rquests a call to the server stub ( Awesome )
12.  The server stub receives the request , executes the call , and sends back the results or exceptions that were raised.
13.  The client then sends them to the application . and the application never knows what goes in the background , it just works like it should.

* All the message passed are in JSON format even the file chunks . 
* The results from the remote call should be simple data types or if its a complex data type it should have json serialization technique . and a de serialization option at the app level. (the project got complex enough so i didn't even think of doing something about that).

* This is a simple [Graph][1] showing the request route.
  [1]: https://docs.google.com/drawings/d/1Ykiz8VoJoPFvBSVkeXshoSPedxcgmmNmcTh7nK0a0i0/edit

##How to test it and run it
1.  Run ServerStub.py
2.  Run ClientStub.py
3.  Run ClientStub.py with args '-c conf2' 
4.  Run ClientStub.py with args '-c conf3'
5. in clientstub1 window register module z.py by : 
	rm:../z.py
6.  the file should be parsed . sent to server ,then sent to the other 2 clients
7.  run app.py from test_app to test the results 
