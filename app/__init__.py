import os
from flask import Flask, render_template, request, redirect, url_for, session, make_response # The Flask request object contains the data that the client (eg a browser) has sent to your app - ie the URL parameters, any POST data, etc.
import requests #The requests library is for your app to make HTTP request to other sites, usually APIs. It makes an outgoing request and returns the response from the external site.
import json

app = Flask(__name__)
app.secret_key = 'any random string'

userLink = 'https://hunter-todo-api.herokuapp.com/user'
userAuth = 'https://hunter-todo-api.herokuapp.com/auth'
userToDoLink = 'https://hunter-todo-api.herokuapp.com/todo-item'

@app.route('/')
def home():
	if session.get('user', None):
		return redirect('auth')
	else:
		return render_template('home.html')

@app.route('/login', methods = ['POST', 'GET'])
def login():
	if request.method == 'POST':
		user = request.form['user_name']
		session['username'] = user
		curr_user = {"username": user}
		# User Authentication
		token = requests.post(userAuth, json = curr_user).json()['token']
		#url_for expects the function name and creates the address, redirect just expects the address.
		return redirect(url_for('prof', user = user, token=token))
	return render_template("login.html")

@app.route('/register', methods = ['POST', 'GET'])
def register():
	if request.method == 'POST':
		#retrieving JSON data and decoding it
		data = requests.get(userLink).json()
		user_ = request.form['new_user']
		userFound = False
		#loop in dictionary
		for accounts in data:
			#specify to key 'username'
			if accounts['username'] == user_:
				userFound = True
				break
		if not userFound:
			#if not in API, create dictionary for user
			new_user = {"username": user_}
			#post to API
			requests.post(userLink, json = new_user)
			userFound = True
		if userFound:
			curr_user = {"username": user_}
			session['username'] = user_
			# User Authentication
			token = requests.post(userAuth, json = curr_user).json()['token']
			#url_for expects the function name and creates the address, redirect just expects the address.
			return redirect(url_for('prof', user = user_, token=token))
	return render_template("register.html")


@app.route('/profile', methods = ['GET'])
def prof():
	#grabs user from the redirect method called
	user = request.args['user']
	token = request.args['token']
 	#note that .format() adds the string passed to whereveer we put the {0} -- 0 means only one argument; 1 will mean two arguments
	#getting the specific data as json for the user
	url = userLink + '?username={0}'.format(user)
	data = requests.get(url).json()
	#setting cookie
	resp = make_response(render_template("profile.html", data = data, user = user))
	resp.set_cookie('sillyauth', token)
	return resp

@app.route('/auth', methods = ['POST', 'GET'])
def auth():
	if request.method == 'GET' or request.method == 'POST':
		#dispays list to user
		data_to_do = requests.get(userToDoLink, cookies=request.cookies).json()
		return render_template("mytodos.html", data_to_do = data_to_do)

@app.route('/new_item', methods = ['POST', 'GET'])
def new_item():
	if request.method == 'POST':
		#get list to check if the task submitted is already in there
		data_to_do = requests.get(userToDoLink, cookies = request.cookies).json()
		task_already_in_list = False
		new_item = request.form['to_do_item']
		for tasks in data_to_do:
			if tasks["content"] == new_item:
				task_already_in_list = True
				break
		if not task_already_in_list:
			new_to_do = {"content": new_item}
			#post to the API and pass the cookie so that they can know its the current user
			response = requests.post(userToDoLink, json = new_to_do, cookies = request.cookies)
			#get updated list
			data_to_do = requests.get(userToDoLink, cookies = request.cookies).json()
			return render_template("mytodos.html", data_to_do = data_to_do)
	data_to_do = requests.get(userToDoLink, cookies = request.cookies).json()
	return render_template("mytodos.html", data_to_do = data_to_do)


#Will get an error if user tries to refresh
@app.route('/itemdata', methods = ['POST'])
def itemdata():
	id_num = request.form['id_number']
	URL = userToDoLink + '/{0}'.format(id_num)
	data = requests.get(URL, cookies = request.cookies).json()
	return render_template('taskdata.html', id_num = id_num, data = data)


@app.route('/completed', methods = ['POST', 'GET'])
def completed():
	if request.method == 'POST':
		#get list to check if the task submitted is already as complete
		data_to_do = requests.get(userToDoLink, cookies = request.cookies).json()
		found = False
		id_number = request.form['id_number']
		for tasks in data_to_do:
			if tasks["id"] == int(id_number):
				found = True
				break
		if not found:
			return redirect(url_for('auth'))
		to_b_updated = {"completed": True}
		dataURL = userToDoLink + '/{0}'.format(id_number)
		requests.put(dataURL, json = to_b_updated, cookies = request.cookies)
		data_to_do = requests.get(userToDoLink, cookies = request.cookies).json()
		return render_template("mytodos.html", data_to_do = data_to_do)
	return redirect(url_for('auth'))

@app.route('/deleted', methods = ['POST', 'GET'])
def deleted():
	if request.method == 'POST':
		#get list to check if the task submitted is already deleted
		data_to_do = requests.get(userToDoLink, cookies = request.cookies).json()
		found = False
		id_number = request.form['id_number']
		for tasks in data_to_do:
			if tasks["id"] == int(id_number):
				found = True
				break
		if not found:
			return redirect(url_for('auth'))
		dataURL = userToDoLink + '/{0}'.format(id_number)
		requests.delete(dataURL, cookies = request.cookies)
		data_to_do = requests.get(userToDoLink, cookies = request.cookies).json()
		return render_template("mytodos.html", data_to_do = data_to_do)
	return redirect(url_for('auth'))

@app.route('/logout')
def logout():
	session.pop('username', None)
	return redirect(url_for('home'))

if __name__ == "__main__":
	port = int(os.environ.get("PORT", 5000))
	app.run(host="0.0.0.0", port=port, threaded=True)
