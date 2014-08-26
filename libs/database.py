#!/usr/bin/env python3
import sqlite3
import threading

class database(threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.db = None
		self.start()
	
	def run(self):
		self.db = self.openDB()
	
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