import os
import sys

backend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(backend_dir)

if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if __name__ == '__main__':
    from celery_app import celery_app
    celery_app.worker_main(['worker', '--loglevel=info', '--pool=solo'])