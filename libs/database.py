#!/usr/bin/env python3
import sqlite3
import os.path

class database:
	def __init__(self):
		self.createDatabase()
		self.db = self.openDB()
	
	def createDatabase(self):
		queries = [
			"CREATE TABLE 'streams' ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 'user' INTEGER, 'name' TEXT, 'url' TEXT, 'directory' TEXT, 'status' INTEGER, 'message' TEXT);",
			"CREATE TABLE 'times' ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 'streamid' INTEGER, 'su' BOOLEAN, 'm' BOOLEAN, 't' BOOLEAN, 'w' BOOLEAN, 'r' BOOLEAN, 'f' BOOLEAN, 'sa' BOOLEAN, 'starthour' INTEGER, 'startmin' INTEGER, 'endhour' INTEGER, 'endmin' INTEGER)",
			"""INSERT INTO "streams" ("id","user","name","url","directory","status","message") VALUES (NULL,NULL,'WCMF Breakroom','http://1681.live.streamtheworld.com/WCMFFMAAC','wcmf-breakroom','0','')""",
			"""INSERT INTO "times" ("id","streamid","su","m","t","w","r","f","sa","starthour","startmin","endhour","endmin") VALUES (NULL,'1','0','1','1','1','1','1','0','2','0','7','15')"""
		]
		if not os.path.exists("db.sqlite") or os.path.getsize("db.sqlite")==0: # TODO: query and see if the tables exist instead
			db = sqlite3.connect("db.sqlite", check_same_thread=False, cached_statements=0, isolation_level=None)
			cursor = db.cursor()
			for query in queries:
				print("Executing: %s" % query)
				cursor.execute(query)
			db.close()
		
	def openDB(self):
		db = sqlite3.connect("db.sqlite", check_same_thread=False, cached_statements=0, isolation_level=None)
		db.row_factory = self.dict_factory
		return db
	
	def dict_factory(self, cursor, row):
		d = {}
		for idx, col in enumerate(cursor.description):
			d[col[0]] = row[idx]
		return d
	
	def execute(self, sql, params=None):
		db = self.db
		cursor = db.cursor()
		if params:
			cursor.execute(sql, params)
		else:
			cursor.execute(sql)
		data = cursor.fetchall()
		if not cursor.lastrowid==None:
			return cursor.lastrowid
		cursor.close()
		return data