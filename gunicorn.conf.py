"""
Gunicorn configuration for production deployment
"""

# Server socket
import os
socket_dir = os.path.join(os.getcwd(), 'sockets')
os.makedirs(socket_dir, exist_ok=True)
bind = f"unix:{os.path.join(socket_dir, 'affiliate-website.sock')}"
backlog = 2048

# Worker processes
workers = 3
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Logging
import os
log_dir = os.path.join(os.getcwd(), 'logs')
os.makedirs(log_dir, exist_ok=True)
accesslog = os.path.join(log_dir, "access.log")
errorlog = os.path.join(log_dir, "error.log")
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = 'affiliate-website'

# Server mechanics
daemon = False
pidfile = os.path.join(os.getcwd(), 'affiliate-website.pid')
# Comment out user/group for container environments
# user = 'www-data'
# group = 'www-data'
tmp_upload_dir = None

# SSL (if needed)
# keyfile = '/path/to/ssl/key.pem'
# certfile = '/path/to/ssl/cert.pem'
