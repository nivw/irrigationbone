#! /usr/bin/env python
#this should be invoked using cron every 10 min
import requests
from requests import ConnectionError
from datetime import datetime, timedelta
import irrigate_by_pm
import re, json
import os,sys
import syslog
from syslog import LOG_WARNING
from garden_config import *
from irrigation_config import *

key =  'f2be361b85d1f3e8'
wunde_url = "http://api.wunderground.com/api/%s/astronomy/q/Israel/Tel_Aviv.json" % (key)
#BASEDIR = os.path.dirname(sys.argv[0])

LOCK_FILENAME = os.path.join('/tmp','irrigation.pid')

def get_sunset() :
  try:
    j = requests.get(wunde_url).json()
    hour = int ( j["moon_phase"]["sunset"]["hour"] )
    minute = int ( j["moon_phase"]["sunset"]["minute"] )
  except Exception  as e:
    print >> sys.stderr, 'Got this exception in get_sunset(): {} see log for http replay'.format(e)
    syslog.syslog('Faulty replay in get_sunset(): {}'.format(j))
    raise e
  else:
    syslog.syslog( 'Sunset is at {}:{:02}'.format(hour,minute) )
    return ( hour , minute )

def get_run_time():
  sunset_hour , sunset_min = get_sunset()
  run_hour = sunset_hour+3
  tomorrow = datetime.now() + timedelta(days=2) #every two days
  syslog.syslog( 'Set next irrigate to {}-{:02}-{:02} {:02}:{:02}:00'.format( \
                 tomorrow.year, tomorrow.month, tomorrow.day, run_hour, sunset_min) )
  run_time = datetime(tomorrow.year, tomorrow.month, tomorrow.day, \
    run_hour, sunset_min)
  return run_time

def is_lock():
  try:
    with open(LOCK_FILENAME, 'r') as lock:
      pid = int(lock.read().strip())
      if not os.path.exists("/proc/"+str( pid ) ):
        unlock()       
        return False
      return True
  except IOError as e:
    return False

def lock():
  if is_lock() :
    syslog.syslog( LOG_WARNING, 'Exiting as a previous session is running' )
    sys.exit()
  with open( LOCK_FILENAME, 'w' ) as lock:
    lock.write( str( os.getpid() ) )

def unlock():
  os.remove(LOCK_FILENAME)

def print_config( irrigation_config ):
  yesterday_pm = irrigation_config["saved_pm"]
  yesterday_rain = irrigation_config["saved_rain"]
  syslog.syslog( 'Time to irrigate. yesterday_pm was: {}, yesterday_rain was: {}'.format( yesterday_pm, yesterday_rain ) )

def save_next_irrigation( irrigation_save_data ):
  next_irrigation = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
  try:
    run_time = get_run_time()
  except ConnectionError as e:
    syslog.syslog( LOG_ERR, 'Failed to get the sunset time got: {}'.format( e ) )
    if 'connection_error_date' not in irrigation_save_data:
      irrigation_save_data['connection_error_date'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
  else: #got next run time
    if 'connection_error_date' in irrigation_save_data :
      print >> sys.stderr, 'Had a communication error since {}, but now comm is fine'.format( irrigation_save_data['connection_error_date'] )
      irrigation_save_data.pop('connection_error_date')
    next_irrigation = run_time.strftime('%Y-%m-%dT%H:%M:%SZ')
  finally:
    irrigation_save_data["next_irrigation"] = next_irrigation
    irrigation_save_data["saved_pm"] = irrigation_save_data["pm"]
    irrigation_save_data["saved_rain"] = irrigation_save_data["mm_rain"]
    irrigation_save_data.save()

def main():
  lock()
  syslog.syslog('Read saved_data')
  irrigation_config = IrrigationConfig()
  garden_config = GardenConfig()

  pos = (garden_config['latitude'], garden_config['longitude'])
  if 'next_irrigation' not in irrigation_config:
    current_pm_data = irrigate_by_pm.safe_get_pm_coef(irrigation_config, pos)
    save_next_irrigation( current_pm_data )
  else:
    now = datetime.now()
    if irrigation_config.scheduale < now :
        irrigation_config = irrigate_by_pm.safe_get_pm_coef(irrigation_config, pos)
        new_irrigation_config = irrigate_by_pm.run_irrigation( irrigation_config, garden_config )
        save_next_irrigation( new_irrigation_config )
    elif irrigation_config.scheduale < now + timedelta(days=1) \
         and 'saved_pm' not in irrigation_config: # in the rest day I just need to save data
        irrigation_config = irrigate_by_pm.safe_get_pm_coef(irrigation_config, pos)
        irrigation_config.save()
  unlock()

if __name__ == '__main__':
  main()
