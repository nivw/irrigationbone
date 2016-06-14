
#!/usr/bin/python
#This will cause all requests to lead to localhost then serve the files from here
import os, shutil
import requests
import BaseHTTPServer
#,SimpleHTTPServer
import SocketServer
from contextlib import contextmanager
import thread
@contextmanager
def set_loopback():
  if not os.path.isfile('/etc/hosts.temp'):
    shutil.copy2('/etc/hosts','/etc/hosts.temp')
  with open('/etc/hosts','a') as f:
      f.write('127.0.0.1 www.meteo.co.il')
  thread.start_new_thread(run_while_true,())
  yield
  shutil.move('/etc/hosts.temp','/etc/hosts')

"""
Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
httpd = SocketServer.TCPServer(('', 80), Handler)
httpd.serve_forever()
"""
def run_while_true(server_class=BaseHTTPServer.HTTPServer,
                   handler_class=BaseHTTPServer.BaseHTTPRequestHandler):
    """
    This assumes that keep_running() is a function of no arguments which
    is tested initially and after each request.  If its return value
    is true, the server continues.
    """
    server_address = ('', 80)
    httpd = server_class(server_address, handler_class)
    while keep_running():
      httpd.handle_request()

def keep_running():
  return True

#did not work html = requests.get('http://www.meteo.co.il:8000/DynamicTable.aspx', params={'G_ID':'8'})
with set_loopback():
  html = requests.get('http://www.meteo.co.il:8000/DynamicTable.aspx', params='G_ID=8')
  print(html)


#thread.start_new_thread(httpd.handle_request, ()
