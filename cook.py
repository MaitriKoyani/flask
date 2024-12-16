from flask import Flask, request, make_response 

app = Flask(__name__) 

# Using set_cookie( ) method to set the key-value pairs below. 
@app.route('/setcookie') 
def setcookie(): 
	
	# Initializing response object 
	resp = make_response('Setting the cookie') 
	resp.set_cookie('GFG','ComputerScience Portal') 
	return resp 

app.run()
