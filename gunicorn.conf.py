"""
Gunicorn configuration for production deployment
"""

# Server socket
bind = "unix:/var/www/AffilaiteWebsite/affiliate-website.sock"
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
accesslog = "/var/log/affiliate-website/access.log"
errorlog = "/var/log/affiliate-website/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = 'affiliate-website'

# Server mechanics
daemon = False
pidfile = '/var/run/affiliate-website.pid'
user = 'www-data'
group = 'www-data'
tmp_upload_dir = None

# SSL (if needed)
# keyfile = '/path/to/ssl/key.pem'
# certfile = '/path/to/ssl/cert.pem'
