"""
Gunicorn configuration file for production deployment
"""

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = 4  # Adjust based on CPU cores (2-4 x CPU cores recommended)
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"
umask = 0
user = None
group = None
tmp_upload_dir = None

# Logging
errorlog = "-"  # Log to stdout
accesslog = "-"  # Log to stdout
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = "resume-screener"

# Server hooks
def on_starting(server):
    print("Starting Resume Screener & Matcher Agent")

def on_reload(server):
    print("Reloading Resume Screener & Matcher Agent")

def worker_int(worker):
    print("Worker received INT signal")

def worker_abort(worker):
    print("Worker received ABORT signal")
