from flask import Flask, request, session
from flask.ext.cors import CORS
from phpserialize import *
import couchdb
import psycopg2
import requests
import urllib
import config

# Flask Init
app = Flask(__name__)
app.config['DEBUG'] = config.debug
cors = CORS(app, resources={r"/*": {"origins": config.CORS_origins, "supports_credentials": True}})

# CouchDB Init
couch = couchdb.Server(config.couchURL)

# PostgreSQL Init
pg = psycopg2.connect("host={0} dbname={1} user={2} password={3}".format(config.sessiondb_host, config.sessiondb_db, config.sessiondb_user, config.sessiondb_pw))
pgcur = pg.cursor()

@app.route('/<database>/<document>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def couchdbProxy(database, document):
	# Debug
	if app.config['DEBUG']:
		for methodname in [ "headers", "data" ]:
			print("======== Incoming_{0} ========".format(methodname))
			print(getattr(request, methodname))
			print("======== /Incoming_{0} ========".format(methodname))

	# Session Cookie
	try:
		sessionid = request.cookies[config.cookieName]
	except KeyError:
		print("missing {0} cookie".format(config.cookieName))
		return "Access Denied", 403

	# CouchDB AuthLayer
	couchdb = couch[database]
	couchdoc = couchdb[document]
	try:
		couchdoc['authLayer']
	except KeyError:
		print('{0}/{1} is not configured for authLayer (missing authLayer dict)'.format(database, document))
		return "Access Denied", 403

	acl = []
	try:
		acl = acl + couchdoc['authLayer'][request.method]
	except KeyError:
		if app.config['DEBUG']:
			print("missing {0} ACL for {1}/{2}".format(request.method, database, document))
		pass
	try:
		acl = acl + couchdoc['authLayer']['ANY']
	except KeyError:
		if app.config['DEBUG']:
			print("missing ANY ACL for {0}/{1}".format(database, document))
		pass
	if not acl:
		print('{0}/{1} authLayer is not configured for {2} requests (missing {2} or ANY list)'.format(database, document, request.method))
		return "Access Denied", 403

	# PostgreSQL Session Data
	pgcur.execute("SELECT session_data FROM session WHERE session_id = '{0}'".format(sessionid))
	raw_session_data = pgcur.fetchone()[0]
	session_data = {}
	for item in raw_session_data.split(";"):
		try:
			key = item.split("|")[0]
			value_semicolon = item.split("|")[1] + ";"
			value = unserialize(value_semicolon.encode('UTF-8'), object_hook=phpobject)
			try:
				value = value.decode('UTF-8')
			except AttributeError:
				pass
			session_data[key] = value
		except IndexError:
			pass

	# ACL matching
	for line in acl:
		for key, value in line.items():
			if key not in session_data:
				print("{0} is missing from session_data".format(key))
				break
			if session_data[key] != value:
				print("{0} ({1}) does not match session_data ({2})".format(key, value, session_data[key]))
				break
		else:
			print("{0} Access to {1}/{2} Granted for {3}".format(request.method, database, document, line))
			# Make a copy of the Requst Headers, but modify them before Proxying the Request
			proxy_request_headers_dict = {}
			for key in request.headers.keys():
				proxy_request_headers_dict[key] = request.headers.get(key)
			proxy_request_headers_dict['Host'] = config.couchHost
			if not proxy_request_headers_dict['Content-Length']:
				proxy_request_headers_dict['Content-Length'] = 0
			del proxy_request_headers_dict['Referer']
			del proxy_request_headers_dict['Origin']
			del proxy_request_headers_dict['Cookie']
			if app.config['DEBUG']:
				print("======== Proxied_Headers ========")
				for key in proxy_request_headers_dict:
					print("{0}: {1}".format(key, proxy_request_headers_dict[key]))
				print("======== /Proxied_Headers ========")
			# Proxy using the new Headers, but the original method and data
			proxy_url = config.couchURL + urllib.parse.quote("/" + database + "/" + document)
			proxy_request = requests.Request(method=request.method, url=proxy_url, headers=proxy_request_headers_dict, data=request.data )
			proxy_response = requests.Session().send(proxy_request.prepare())
			return (proxy_response.text, proxy_response.status_code, proxy_response.headers.items())

	# Default Deny
	return "Access Denied", 403

if __name__ == "__main__":
	app.run(host='0.0.0.0', port=5984)
