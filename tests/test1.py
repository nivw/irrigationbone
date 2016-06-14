from multiprocessing import Process
import web_mirror
import requests
import contextlib
import json
from datetime import datetime, timedelta
import irrigationbone.schedule_irrigation as schedule_irrigation

@contextlib.contextmanager
def simulator():
  web_server = Process( target=web_mirror.run )
  web_server.start()
  print('before yield')
  yield
  web_server.terminate()
  web_server.join()

def print1():
  print('print1')
  
def test1():
  with simulator():
    #print(requests.get('http://127.0.0.1:8011/abc').content)
    with open('/tmp/irrigation.json') as f:
      data=json.load(f)
    data['next_irrigation'] = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
    with open('/tmp/irrigation.json', 'w') as f:
      json.dump(data, f)

    #subprocess.call(["python", "schdule.py"])
    test_proccess = Process( target=print1 )
    test_proccess.start()
    

if __name__ == '__main__':
  test1()

