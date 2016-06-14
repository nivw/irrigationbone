#!/usr/bin/python
import requests
from logger import logger
import sys
from irrigate_by_pm_config import *
import time
from datetime import datetime, timedelta
import requests.exceptions
import json
import get_pm_by_pos
from irrigation_config import *

def get_meteo_w_retry(my_pos):
  error = None
  for retry_counter in range(MAX_HTTP_RETRY):
    try:
      #pm, mm_rain = query_meteo( debug )
      (distance_to_pm, near_st, coef) = get_pm_by_pos.get_pm_by_pos(my_pos)
    except requests.exceptions.ConnectionError as e:
      error = e
      logger.error( 'Exception from get_pm_by_pos(): {}. Retry in 30 sec {}/{}'.format( e, retry_counter, MAX_HTTP_RETRY ) )
      time.sleep(30)
    else:
      break
  if retry_counter == (MAX_HTTP_RETRY -1) :
    logger.error( 'Failed to get valid HTTP response after {} retries'.format( MAX_HTTP_RETRY ) )
    raise error #requests.exceptions.ConnectionError
  return (distance_to_pm, near_st, coef)

def validate_pm(pm, saved_pm):
    warning_flag = False
    if saved_pm < 3 and ( saved_pm * 2 ) < pm :
      warning_flag = True
    if pm < 3 and ( pm * 2 ) < saved_pm :
      warning_flag = True
    if warning_flag :
      print >> sys.stderr, 'PM validation warning: yesterday was {} , today is {}'.format( saved_pm, pm )
    if saved_pm > MIN_PM_THRESHOLD and pm > MIN_PM_THRESHOLD \
       and ( (saved_pm/pm) > MAX_PM_FACTOR or (pm/saved_pm) > MAX_PM_FACTOR ):
      logger.error('PM validation failed for {}: Yesterday was {}, today is {}, both are more then {} , or the factor is more then {}'.format(name, saved_pm, pm, MIN_PM_THRESHOLD, MAX_PM_FACTOR))
    return True

def validate( distance_to_pm, irrigation_save_data=None ):
  if not irrigation_save_data:
    logger.info('irrigation_save_data missing in validate()')
    return IrrigationConfig({'pm':distance_to_pm[0][0], 'mm_rain':distance_to_pm[0][1], 'name':distance_to_pm[0][2]})

  saved_pm  = irrigation_save_data.get('saved_pm', distance_to_pm[0][0] )
  if isinstance(saved_pm, str):
    logger.error('In get_pm:validate() saved_pm is of type string')
    saved_pm = float(saved_pm)

  for pm, mm_rain, name in distance_to_pm:
    # should improve this to take in to account abs value.
    if validate_pm(pm, saved_pm):
        irrigation_save_data["pm"] = pm
    else:
        continue
    if mm_rain is not None and float( mm_rain ) >=0:
      irrigation_save_data["mm_rain"] = mm_rain
      irrigation_save_data["name"] = name
    #if irrigation_save_data.has_key('pm') and irrigation_save_data.has_key('mm_rain'):
      logger.debug('validate() returns: {}'.format(irrigation_save_data))
      return irrigation_save_data
  raise Exception('Could not validate any station PM')

def get_pm( irrigation_save_data, my_pos ) :
  (distance_to_pm, near_st, coef) = get_meteo_w_retry(my_pos)
  validated_irrigation = validate( distance_to_pm, irrigation_save_data )
  validated_irrigation['comp_coef'] = coef
  logger.info('get_pm returns: {}'.format( validated_irrigation ))
  return validated_irrigation

if __name__ == '__main__':
  irrigation_save_data = {
    "pm": 3.5,
    "mm_rain": 0.0,
    "next_irrigation": "2015-04-02T19:59:00Z",
    "avg_pm": 3.818206128,
    "avg_rain": 0.0,
    "saved_pm": 3.5,
    "saved_rain": 0.0
  }

  good_file = '2015-03-13.goodpage.html'
  no_value = '2015-03-08.novalue.html'
  pmfile = no_value
  with open( pmfile ) as f:
    html = f.read()
    get_pm( irrigation_save_data, html )

# 2015-02-10 it was 0.3 02-09 was 2
# 2015-02-11 is was 3.7 02-10 was 0.3
