# Streamrecord
***
A python3 web app to record internet radio streams and present them in a podcast

### Requirements

- python3
- sqlite3
- jinja2
- cherrypy
- uwsgi
- mkvmerge
- avconv

### Installation

- Checkout the source to somewhere on your system. In the examples below, the path to the root of the source is /home/streamrecord/app/. Cd to here.
- Write the config for uwsgi, start that daemon
- Write the config for nginx, and view the page.
- Create a symbolic link in static/ pointing to files/output/. Command: `mkdir files/ ; mkdir files/output/ ; mkdir files/temp/ ; ln -s ../files/output static/test `
- Add a cron job to call http://my.server/api/tick every minute. 

Podcast usage: each schedule has a numerical id. To view the podcast, http://my.server/api/getPodcast?id=[number]

### Uwsgi config

Something like:

```
[uwsgi]
uid = streamrecord
pid = streamrecord
plugins = python3
touch-reload = /home/streamrecord/app/app.py
chdir = /home/streamrecord/app/
wsgi-file = /home/streamrecord/app/app.py
callable = application
master = true
processes = 1
socket = 127.0.0.1:3330
pidfile = /tmp/streamrecord.pid
enable-threads = true
no-threads-wait = true
die-on-term = true
```

### Nginx config

Something like:

```
server {
	listen 30000;
	listen [::]:30000 ipv6only=on;
	include uwsgi_params;
	access_log /var/log/nginx/stremrecord.log;
	location / {
		uwsgi_pass 127.0.0.1:3330;
	}
	location /streamrecord/static/ {
		autoindex off;
		alias /home/streamrecord/app/static/;
	}
}
```