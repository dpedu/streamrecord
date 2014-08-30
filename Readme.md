# Streamrecord
***
A python3 web app to record internet radio streams and present them in a podcast

### Requirements

- python3
- sqlite3
- jinja2
- cherrypy
- feedgen
- uwsgi
- mkvmerge
- avconv

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
		autoindex on;
		alias /home/streamrecord/app/static/;
	}
}
```