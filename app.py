#!/usr/bin/env python3

STREAM_STATUS_ACTIVE = 0
STREAM_STATUS_PAUSED = 1
STREAM_STATUS_ERROR = 2

import sys
import os
import os.path
import cherrypy
import json
import signal
from jinja2 import Environment, FileSystemLoader
from libs import database
from libs import recordTick
from feedgen.feed import FeedGenerator
from datetime import datetime

if __name__ == '__main__' or 'uwsgi' in __name__:
	appdir = "/home/streamrecord/app"
	appconf = {
		'/': {
			#'tools.proxy.on':True,
			#'tools.proxy.base': conf["base"]["url"],
			'tools.sessions.on':True,
			'tools.sessions.storage_type':'file',
			'tools.sessions.storage_path':appdir+'/sessions/',
			'tools.sessions.timeout':525600,
			'request.show_tracebacks': True
		},
		'/media': {
			'tools.staticdir.on': True,
			'tools.staticdir.dir': appdir+"/static/"
		}
	}
	
	cherrypy.config.update({
		'server.socket_port':3000,
		'server.thread_pool':1,
		'server.socket_host': '0.0.0.0',
		'sessionFilter.on':True,
		'server.show.tracebacks': True
	})
	
	cherrypy.server.socket_timeout = 5
	
	# env - jinja2 template renderer
	env = Environment(loader=FileSystemLoader("/home/streamrecord/app/templates"))
	# db - slightly custom sqlite3 object. rows = db.execute(query, args)
	db = database()
	# REC - recorder thread - see recordTick.py
	#REC = recordTick(db)
	
	def render(template, args):
		templatesCache = pysite.cacheTemplates()
		defaults = {"templates":templatesCache}
		for item in args:
			defaults[item] = args[item]
		return quickRender(template, defaults)
	
	def quickRender(template, args):
		template = env.get_template(template)
		return template.render(args)
	
	class siteRoot(object):
		def __init__(self):
			print("Siteroot init !")
			self.templateCache = self.cacheTemplates()
		
		def cacheTemplates(self):
			templateFiles = os.listdir("jstemplates/")
			templateList = []
			nameList = []
			for item in templateFiles:
				name = item.split(".")
				templateList.append({"name":name[0],"content":open("jstemplates/"+item,"r").read().replace("\t", "").replace("\n","")})
				nameList.append(name[0])
			return quickRender("templates.html", {"names":json.dumps(nameList), "templates":templateList})
		
		@cherrypy.expose
		def index(self):
			return render("html.html", {})
		
		@cherrypy.expose
		def htmltest(self):
			return render("html.tpl", {})
		#index.exposed = True
		
		@cherrypy.expose
		def templates(self):
			return self.templateCache
	
	class api(object):
		def __init__(self):
			self.REC = recordTick(db)
		
		@cherrypy.expose
		def getStreams(self):
			streamList = db.execute('SELECT * FROM "streams"')
			
			for stream in streamList:
				stream["time"] = db.execute('SELECT * FROM "times" WHERE streamid=?', [stream["id"]])[0]
				stream["files"] = self._getFiles(stream["id"])
			
			return json.dumps(streamList)
		
		def _getStream(self,id):
			streamList = db.execute('SELECT * FROM "streams" WHERE "id"=?', [int(id)])
			
			for stream in streamList:
				stream["time"] = db.execute('SELECT * FROM "times" WHERE streamid=?', [stream["id"]])[0]
				stream["files"]=self._getFiles(id)
			return streamList[0]
		
		@cherrypy.expose
		def getStream(self, id):
			return json.dumps(self._getStream(id))
		
		@cherrypy.expose
		def changeTimeDay(self, streamid, day, value):
			streamid = int(streamid)
			value = value == "true"
			
			col = ""
			if day == "daysu":
				col="su"
			elif day == "daym":
				col="m"
			elif day == "dayt":
				col="t"
			elif day == "dayw":
				col="w"
			elif day == "dayr":
				col="r"
			elif day == "dayf":
				col="f"
			elif day == "daysa":
				col="sa"
			else:
				raise cherrypy.HTTPError(500, message="Day not found")
			
			db.execute('UPDATE "times" SET "'+col+'"=? WHERE "streamid"=? ;', [1 if value else 0,streamid])
			
			return json.dumps({"result":True})
		
		@cherrypy.expose
		def changeName(self, streamid, value):
			streamid = int(streamid)
			db.execute('UPDATE "streams" SET "name"=? WHERE "id"=?', [value,streamid])
			return json.dumps({"result":True})
		@cherrypy.expose
		def changeUrl(self, streamid, value):
			streamid = int(streamid)
			db.execute('UPDATE "streams" SET "url"=? WHERE "id"=?', [value,streamid])
			return json.dumps({"result":True})
		@cherrypy.expose
		def changeTime(self, streamid, startHour, startMin, endHour, endMin):
			startHour=int(startHour)
			assert startHour>=0 and startHour<=23
			startMin=int(startMin)
			assert startMin>=0 and startMin<=59
			endHour=int(endHour)
			assert endHour>=0 and endHour<=23
			endMin=int(endMin)
			assert endMin>=0 and endMin<=59
			
			db.execute('UPDATE "times" SET "starthour"=?, "startmin"=?, "endhour"=?, "endmin"=? WHERE "streamid"=? ;', [startHour, startMin, endHour, endMin, streamid])
			return json.dumps({"result":True})
		
		def _filterName(self, input):
			allowed="abcdefghijklmnopqrstuvwxyz123456789-"
			input = input.replace(" ", "-").lower()
			output=[]
			for i in range(0, len(allowed)):
				if input[i:i+1] in allowed:
					output.append(input[i:i+1])
			return ''.join(output)
		
		@cherrypy.expose
		def createStream(self, data):
			data = json.loads(data)
			
			assert not data["name"] == ""
			assert not data["url"] == ""
			assert data["time"]["su"] or data["time"]["m"] or data["time"]["t"] or data["time"]["w"] or data["time"]["r"] or data["time"]["f"] or data["time"]["sa"]
			
			dirName = self._filterName(data["name"])
			
			rowid = db.execute('INSERT INTO "streams" ("user", "name", "url", "directory", "status", "message") VALUES (?, ?, ?, ?, ?, ?);', [0, data["name"], data["url"], dirName, data["status"], ""])
			db.execute('INSERT INTO "times" ("streamid", "su", "m", "t", "w", "r", "f", "sa", "starthour", "startmin", "endhour", "endmin") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);', [
				rowid,
				data["time"]["su"],
				data["time"]["m"],
				data["time"]["t"],
				data["time"]["w"],
				data["time"]["r"],
				data["time"]["f"],
				data["time"]["sa"],
				data["time"]["startHour"],
				data["time"]["startMin"],
				data["time"]["endHour"],
				data["time"]["endMin"]
			])
			
			return json.dumps({"result":rowid})
		
		def _getFiles(self, id):
			stream = db.execute('SELECT * FROM "streams" WHERE "id"=?', [int(id)])[0]
			recordingsDir = "files/output/"+stream["directory"]+"/"
			files = []
			if os.path.exists(recordingsDir):
				files = os.listdir(recordingsDir)
			files.sort()
			allFiles = []
			for i in range(0, len(files)):
				item = files[i]
				size = os.path.getsize(recordingsDir+item)
				allFiles.append({
					"filename":item,
					"directory":recordingsDir,
					"streamdir":stream["directory"],
					"filenum":i,
					"bytes":size,
					"mbytes":round(size/1024.0/1024.0, 2),
					"date":os.path.getmtime(recordingsDir+item)
				})
			return allFiles
		
		@cherrypy.expose
		def getFiles(self, id):
			files = self._getFiles(id)
			return json.dumps({"data":files})
		
		@cherrypy.expose
		def download(self, id, fn):
			files = self._getFiles(id)
			item = files[int(fn)]
			raise cherrypy.HTTPRedirect("/static/output/"+item["streamdir"]+"/"+item["filename"], 302)
		
		@cherrypy.expose
		def getUrl(self, id, fn):
			files = self._getFiles(id)
			item = files[int(fn)]
			return json.dumps({"result":"/static/output/"+item["streamdir"]+"/"+item["filename"]})
		
		@cherrypy.expose
		@cherrypy.tools.response_headers(headers=[('Content-Type', 'application/rss+xml')])
		def getPodcast(self, id):
			stream = self._getStream(id)
			# Thu, 31 Jul 2014 07:13:48 +0000
			for f in stream["files"]:
				f["date"]=datetime.fromtimestamp(f["date"]).strftime("%a, %m %b %Y %H:%M:%S +%z")
			return str.encode(render("podcast.html", {
				"stream":stream,
				"builddate": datetime.now().strftime("%a, %m %b %Y %H:%M:%S +0100")#Thu, 31 Jul 2014 07:13:48 +0000
			}))
				
			
		@cherrypy.expose
		def getRecStatus(self, id):
			print(self.REC)
			print(self.REC.threads)
			print(self.REC.getSelf())
			print(self.REC.getSelf().threads)
			return json.dumps({"data":self.REC.streamStatus(int(id))})
	
	pysite = siteRoot()
	pysite.api = api()
	
	print( "Ready to start application" )
	
	if(len(sys.argv)>1 and sys.argv[1]=="test"):
		print("test!")
		application = cherrypy.quickstart(pysite, '/', appconf)
	else:
		sys.stdout = sys.stderr
		cherrypy.config.update({'environment': 'embedded'})
		application = cherrypy.tree.mount(pysite, "/", appconf)
