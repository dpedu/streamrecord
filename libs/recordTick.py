#!/usr/bin/env python3

from threading import Thread
import time
import datetime
from sched import scheduler
import cherrypy
import sys
import subprocess
import os
import os.path

class recordTick:
	def __init__(self, database):
		# sqlite3 reference
		self.db = database
		# list of downloader threads
		self.threads = {}
	
	def run(self):
		time.sleep(3)
		
		## TESTING CODE
		#now=datetime.datetime.now()
		#self.db.execute('UPDATE "times" SET "starthour"=?, "startmin"=?, "endhour"=?, "endmin"=? WHERE "streamid"=? ;', (now.hour, now.minute, now.hour, now.minute+1, 1))
		#self.tick()
		## END TESTING CODE
		
		#self.scheduleTick()
		
		## TESTING CODE
		
		while True:
			time.sleep(self.timeToNextMinute())
			self.tick()
			print("Ticked")
	
	def tick(self):
		now=datetime.datetime.now()
		#print("Tick start: %s" % now)
		
		# Look for starting times set to now
		days = ["m", "t", "w", "r", "f", "sa", "su"]
		day = days[datetime.datetime.now().weekday()]
		
		startTimes = self.db.execute('SELECT * FROM "times" where "starthour"=? AND "startmin"=? AND "'+day+'"=1', (now.hour, now.minute))
		for startTime in startTimes:
			# Start each downloader
			self.startStream(startTime["streamid"])
		
		# Look for end times set to now
		endTimes = self.db.execute('SELECT * FROM "times" where "endhour"=? AND "endmin"=?', (now.hour, now.minute))
		for endTime in endTimes:
			# terminate each downloader
			self.endStream(endTime["streamid"])
		
		#print("Tick end: %s" % now)
	
	def startStream(self, id):
		# Find stream information
		stream = self.db.execute('SELECT * FROM "streams" WHERE "id"=? ;', (id,))[0]
		
		# if the downloader isnt running already:
		if not stream["id"] in self.threads:
			# Create the recording thread
			self.threads[stream["id"]] = recordThread(stream["url"], stream["directory"])
	
	def endStream(self, id):
		if id in self.threads:
			# tell the downloader to finish
			self.threads[id].cancel()
			del self.threads[id]
	
	def streamStatus(self, id):
		if not id in self.threads:
			return -1
		
		return self.threads[id].status
	
	def getSelf(self):
		return self
	
	def scheduleTick(self):
		# schedule tick in the next minute
		self.timer.enter(self.timeToNextMinute(), 1, self.tick)
		self.timer.run()
		# Schedule the next tick
		Thread(target=self.scheduleTick).start()
	
	def timeToNextMinute(self):
		# calculate time to the milliscond until the next minute rolls over
		# Find the next minute
		then = datetime.datetime.now()+datetime.timedelta(minutes=1)
		# Drop the seconds
		then = then-datetime.timedelta(seconds=then.second,microseconds=then.microsecond)
		# calculate difference
		wait = then - datetime.datetime.now()
		waitMillis = wait.seconds + int(wait.microseconds/1000)/1000
		return waitMillis

class recordThread(Thread):
	def __init__(self, url, directory):
		Thread.__init__(self)
		# Status
		self.status = 1
		# URL to download
		self.url = url
		# Directory name to use
		self.directory = directory
		# True means the downloader keeps alive on failure
		self.running = True
		# Start time of the recording
		self.startdate = None
		
		self.start()
	
	def run(self):
		print("%s starting downloader for %s" % (datetime.datetime.now(), self.url))
		# Download the stream to temp file(s)
		self.status = 2
		self.downloadStream()
		# Combine files into 1 audio file
		self.status = 3
		self.mergeStream()
		# Encode to mp3
		self.status = 4
		self.transcodeStream()
		# Delete temp files, move recording to save directory
		self.status = 5
		self.cleanup()
		print("%s finished downloader for %s" % (datetime.datetime.now(), self.url))
		self.status = 0
		
	def downloadStream(self):
		self.startdate = datetime.datetime.now()
		# As long as we're supposed to keep retrying
		while self.running:
			# Create the temp dir for this stream
			if not os.path.exists("files/temp/"+self.directory):
				os.mkdir("files/temp/"+self.directory)
			
			# If there are already files, we're resuming. take the next available number
			recNum = 0
			while os.path.exists("files/temp/%s/recdate%s.mp3" % (self.directory, ".%s"%recNum)):
				recNum = recNum + 1
			# Filename is something like files/temp/stream-name/rec-y-m-d_h-m-s.0.mp3
			fileName = "files/temp/%s/recdate%s.mp3" % (self.directory, "" if recNum == None else ".%s"%recNum)
			
			# Args if we download with curl (bad)
			args_curl = [
				'/usr/bin/curl',
				#'-s',
				'-A',
				'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36',
				'--output', fileName, self.url]
			
			# args if we download/transcode with avconv (HERO!)
			args_libav = [
				'/usr/bin/avconv',
				'-loglevel',
				'error',
				'-i',
				self.url,
				'-ab',
				'128k',
				fileName
			]
			self.proc = subprocess.Popen(args_libav, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			output = self.proc.communicate()
			print("LibAV output for %s:\n%s" % (self.url, output))
			self.proc = None
			
	
	def mergeStream(self):
		# Get an ordered list of the piece files
		files = os.listdir("files/temp/%s"%self.directory)
		files.sort()
		# merge audio tracks into a matroska audio file
		command = ['/usr/bin/mkvmerge', '-o', "files/temp/%s/temp.mka"%self.directory, "files/temp/%s/%s"%(self.directory,files.pop(0))]
		for fname in files:
			command.append("+files/temp/%s/%s"%(self.directory,fname))
		self.mergeproc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		# Wait for the merge to finish
		output = self.mergeproc.communicate()
	
	def transcodeStream(self):
		# Delete the existing output file
		if os.path.exists("files/temp/%s/out.mp3"%self.directory):
			os.unlink("files/temp/%s/out.mp3"%self.directory)
		
		# Convert the matroska file to mp3
		command = ['/usr/bin/avconv', '-i', "files/temp/%s/temp.mka"%self.directory, '-q:a', '0', '-ab', '128k', "files/temp/%s/out.mp3"%self.directory]
		self.transcodeproc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		# wait for the trancode to finish
		output = self.transcodeproc.communicate()
	
	def cleanup(self):
		# create a dated name for the file
		newname = self.startdate.strftime("%Y-%m-%d_%H-%M-%S")+".mp3"
		
		# make it's finished storage location
		if not os.path.exists("files/output/"+self.directory):
			os.mkdir("files/output/"+self.directory)
		
		# copy final recording to output dir
		os.rename("files/temp/%s/out.mp3"%(self.directory), "files/output/%s/%s"%(self.directory,newname))
		
		# Delete temp files
		files = os.listdir("files/temp/%s"%self.directory)
		for f in files:
			os.unlink("files/temp/%s/%s"%(self.directory,f))
	
	def cancel(self):
		print("Closing %s" % self.url)
		# turn off keep-alive dow the downloader
		self.running = False
		# Kill the download process
		self.proc.terminate()
		Thread(target=self.kill).start()
	
	def kill(self):
		print("Starting kill thread for %s" % self.url)
		time.sleep(3)
		# kill the thread
		if not self.proc == None:
			# One more chance to go quietly...
			self.proc.terminate()
			time.sleep(3)
		else:
			print("Nothing to kill for %s" % self.url)
		if not self.proc == None:
			# Kill it
			self.proc.kill()
	