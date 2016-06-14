#!/usr/bin/python
import requests
import syslog
import wfs
from logger import logger
import sys
from irrigate_by_pm_config import *
import time
import get_pm
from subprocess import call
import smtplib
from email.mime.text import MIMEText
import os.path
import json
import base64
from socket import gethostname
from garden_config import *
from datetime import datetime
import ast

cookie = 0
garden_config_file = '/home/debian/cwvw.json'
def login() :
  r = requests.post( 'http://localhost/login', params={'password':'opendoor'} )
  cookie = { 'webpy_session_id': r.cookies['webpy_session_id'] }
  return cookie

def switch_to_manual_mode() :
  logger.info( 'Switch to manual mode' )
  r = requests.get( 'http://localhost/cv?pw=opendoor&mm=1' )

def get_password() :
  if os.path.isfile(ospi_config):
    with open(ospi_config) as f:
      ospi_data=json.load(f)
    if ospi_data['ipas'] :
      return base64.b64decode(ospi_data['ipas'])
    else:
      return base64.b64decode(ospi_data['pwd'])

def set_manual_mode( ospi_port ):
  logger.info('set_manual_mode')
  pwd=get_password()
  r = requests.get( 'http://localhost:{}/cv?pw={}&mm=1'.format( ospi_port, pwd) )

def unset_manual_mode( ospi_port ):
  logger.info('unset_manual_mode')
  pwd=get_password()
  r = requests.get( 'http://localhost:{}/cv?pw={}&mm=0'.format( ospi_port, pwd) )

def open_faucet( faucet_id, port ) :
  logger.info( '{} is openning faucet: {}'.format( __name__, faucet_id ) )
  #only 1st faucet r = requests.get( 'http://localhost:8080/sn1=1&t=0' )
  #see http://rayshobby.net/opensprinkler/svc-use/svc-web/#httpget
  set_manual_mode( port )
  r = requests.get( 'http://localhost:{}/sn{}=1'.format( port, faucet_id ) )
  if r.status_code != requests.codes.ok :
    message = 'Failed to open faucet {} got this status code: {}'.format( faucet_id, r.status_code )
    logger.error( message )
    raise Exception( message )

def close_faucet( faucet_id, port ) :
  logger.info( '{} is closing faucet: {}'.format( __name__, faucet_id ) )
  set_manual_mode(port)
  r = requests.get( 'http://localhost:{}/sn{}=0'.format( port, faucet_id ) )
  if r.status_code != requests.codes.ok :
    message = 'Failed to close faucet {} got this status code: {}'.format( faucet_id, r.status_code )
    logger.error( message )
    print >> sys.stderr, 'Error closing faucet, restarting ospi serivce'
    call(['systemd', 'restart', 'ospi'])
  unset_manual_mode( port )

def calc_avg( data ):
  if "avg_pm" in data :
    data["avg_pm"] = ( data["avg_pm"] * 0.66) + (data["pm"] * 0.33)
    data["avg_rain"] = ( data["avg_rain"] * 0.66) + ( data["mm_rain"] * 0.33)
  else:
    data["avg_pm"] = data["pm"]
    data["avg_rain"] = data["mm_rain"]

def faulty_pm_value( saved_data ):
  saved_data['name'] = FAULTY_ST_NAME
  if 'avg_pm' in saved_data :
    saved_data['pm'], saved_data['mm_rain'] = saved_data['avg_pm'], saved_data['avg_rain']
  elif 'pm' not in saved_data:
    saved_data['pm'], saved_data['mm_rain'] = 5, 0
  return saved_data

def duration_in_min(d):
  if d < 60 :
    duration = '{} secs'.format( d )
  else :
    duration = '{} mins and {} secs'.format( (d//60), (d%60) )
  return duration

def send_email(recipient, message):
  line = unicode('Email {} to: {}'.format(message, recipient), 'utf8')
  logger.debug(line.encode('utf8', 'replace') )
  msg = MIMEText(message)
  msg['Subject'] = 'Irrigation from {}'.format(gethostname())
  msg['From'] = EMAIL_SENDER
  msg['To'] = recipient
  s = smtplib.SMTP('localhost')
  s.sendmail(EMAIL_SENDER, recipient,msg.as_string())
  s.quit()

def calc_irrigation( faucet, irrigation_config ):
  """ Caluculate how many liters to irrigate using a dict with these values:
        size, plant_type, rain_size, saved_rain, mm_rain, pm, saved_pm
        1.34 is the coefficiant for Dagan
  """
  logger.info('Calling calc_irrigation with these values: {}'.format(irrigation_config))
  litre_rain = ( irrigation_config['mm_rain'] + irrigation_config['saved_rain'] ) * irrigation_config['rain_size']
  litre_to_irrigate = ( irrigation_config['pm'] + irrigation_config['saved_pm'] ) \
                      * irrigation_config['size'] * irrigation_config['plant_type'] * irrigation_config['comp_coef']
  message = None
  if litre_rain >= litre_to_irrigate :
    if not irrigation_config['name'][1:].islower():
      message = u'Last two days it rained {} mm, more then the needed {} mm, according to meteorological data from {}'.format( \
              litre_rain, litre_to_irrigate, irrigation_config['name'][::-1] )
    else:
      message = u'Last two days it rained {} mm, more then the needed {} mm, according to meteorological data from {}'.format( \
              litre_rain, litre_to_irrigate, irrigation_config['name'] )
    message = message.encode('utf8', 'replace')
    logger.info( message )
  else :
    litres = litre_to_irrigate - litre_rain
  logger.info('Calculted {} liters for faucet {}'.format(litres, faucet))
  return litres

def good_irrigation_msg(irrigation_config, duration, litres, faucet):
  faucet_name = get_faucet_name()[int(faucet)-1]

  message = u'Irrigated {} , {} , which was {} liters , last two days it rained {} mm according to meteorological data from {}'.format( \
        faucet_name, duration, litres, \
        ( irrigation_config['mm_rain'] + irrigation_config['saved_rain'] ),\
        irrigation_config['name'] )

  message = message.encode('utf8', 'replace')
  print >> sys.stderr, message

  if not irrigation_config['name'][1:].islower():
    logger.debug('I found the station name to be in hebrew')
    message = u'Irrigated {} , {} , which was {} liters , last two days it rained {} mm according to meteorological data from {}'.format( \
        faucet_name, duration, litres, \
        ( irrigation_config['mm_rain'] + irrigation_config['saved_rain'] ),\
        irrigation_config['name'][::-1] )

    message = message.encode('utf8', 'replace')
  return message

def safe_irrigate(faucet, ospi_port, litres):
    start_time = time.time()
    try:
      open_faucet(faucet, ospi_port)
      wfs.main(litres)
    except Exception as e:
      print >> sys.stderr, 'Exception in safe irrigate: {}'.format( e )
    finally:
      duration = duration_in_min( time.time() - start_time )
      close_faucet(faucet, ospi_port)
      return duration

def safe_get_pm_coef( saved_data, pos ):
  try:
    current_pm_data = get_pm.get_pm( saved_data, pos )
  except Exception as e:
    logger.error( 'Failed to get valid PM due to: {} using avg values instad'.format( e ) )
    current_pm_data = faulty_pm_value( saved_data )
    if 'connection_error_date' not in saved_data:
      current_pm_data['connection_error_date'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
  else:
    logger.info( u'Using station {} today pm is: {} , and it rained {} mm coef: {}'.format( \
                   current_pm_data['name'], current_pm_data['pm'], current_pm_data['mm_rain'], \
                   current_pm_data['comp_coef'] ) )
    if 'connection_error_date' in current_pm_data:
      print >> sys.stderr, 'Communication disconnected since {}, comm is now restored'.format( \
                            current_pm_data['connection_error_date'] )
      current_pm_data.pop('connection_error_date')
    calc_avg( current_pm_data )
  if 'saved_pm' not in current_pm_data :
    current_pm_data['saved_pm'] , current_pm_data['saved_rain'] = current_pm_data['pm'], current_pm_data['mm_rain']
  logger.debug('safe_get_pm_coef() returns: {}'.format(current_pm_data))
  return current_pm_data

def run_irrigation( irrigation_config, garden_config ) :
  if garden_config.get('faucets'):
    for faucet, data in garden_config['faucets'].items() :
      irrigation_config.update(data)
      if data['roof']:
        irrigation_config['rain_size'] = 0
      else:
        irrigation_config['rain_size'] = garden_config['faucets'][faucet]['size']
      litres = calc_irrigation( faucet, irrigation_config )
      duration = safe_irrigate( faucet, read_ospi_port(), litres)
      message = good_irrigation_msg(irrigation_config, duration, litres, faucet)
      if garden_config.get('email'):
        send_email(garden_config['email'], message)
  irrigation_config.pop('saved_pm')
  irrigation_config.pop('saved_rain')
  return irrigation_config

def read_ospi_port() :
  if os.path.isfile(ospi_config):
    with open(ospi_config) as f:
      ospi_data=json.load(f)
      return ospi_data['htp']

def get_faucet_name() :
  if os.path.isfile(faucets_names):
    with open(faucets_names) as f:
      string_data = f.read()
    data = ast.literal_eval(string_data)
    return data

if __name__ == '__main__':
  saved_data = Munch()
  saved_data["pm"] = 5
  saved_data["saved_pm"] = 5
  saved_data["avg_pm"] = 5
  saved_data["mm_rain"] = 0
  saved_data["avg_rain"] = 0
  saved_data["saved_rain"] = 0
  run_irrigation( saved_data )
