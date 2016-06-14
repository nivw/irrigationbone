#!/usr/bin/python
from flask import Flask
import subprocess

def run():
  stop_ospi()
  app = Flask(__name__)
  @app.route('/', defaults={'path': ''})
  @app.route('/<path:path>')
  def catchall(path):
      return path

  app.run(host='127.0.0.1', port=80, debug=False, use_reloader=False, threaded=True)
  start_ospi()
  
def stop_ospi():
  ret =subprocess.call(['systemctl', 'is-active', 'ospi.service'])
  if not ret:
    subprocess.call(['systemctl', 'stop', 'ospi.service'])
  
def start_ospi():
  subprocess.call(['systemctl', 'start', 'ospi.service'])

  
if __name__ == '__main__':
  run()
