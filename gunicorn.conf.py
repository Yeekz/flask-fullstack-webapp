"""Loopback-only WSGI service, intended to sit behind an HTTPS reverse proxy."""
import os

bind = os.environ.get("BIND", "127.0.0.1:4593")
workers = 1
threads = 1
worker_class = "sync"
timeout = 30
max_requests = 1000
max_requests_jitter = 50
accesslog = "-"
errorlog = "-"
capture_output = True
