import multiprocessing
import os

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gthread"
threads = 4
worker_connections = 1000
timeout = 60
keepalive = 5

# Process naming
proc_name = "mobiprice_gunicorn"

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Security & Lifecycle
max_requests = 1000
max_requests_jitter = 50
preload_app = False
