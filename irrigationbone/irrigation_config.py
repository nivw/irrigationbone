import json
import os
from datetime import datetime
from munch import *
import syslog
from syslog import LOG_WARNING

BASEDIR = os.path.join('/home', 'debian')
IRRIGATION_CONFIG_FILENAME = os.path.join(BASEDIR, 'irrigation.json')

class IrrigationConfig(Munch):
  """ Irrigation config in Munch object"""
  def __init__(self, irrigation_dict=None):
    if not irrigation_dict:  
      try:
        with open( IRRIGATION_CONFIG_FILENAME, "r" ) as f:
          irrigation_dict = json.load( f )
      except Exception as e:
        syslog.syslog( LOG_WARNING, 'Failed to read saved data from {} got {}'.format( IRRIGATION_CONFIG_FILENAME, e ) )
      else:
        next_irrigation = irrigation_dict['next_irrigation']
        irrigation_dict['scheduale'] = datetime.strptime( next_irrigation ,'%Y-%m-%dT%H:%M:%SZ' )
    if irrigation_dict:
      for k,v in irrigation_dict.items():
        self.update({k:v})

  def save(self):
    if os.path.exists(IRRIGATION_CONFIG_FILENAME):
      os.remove(IRRIGATION_CONFIG_FILENAME)
    d = self.copy()
    if 'scheduale' in d:
      d.pop('scheduale')
    with open( IRRIGATION_CONFIG_FILENAME, 'wb' ) as f:
      json.dump( d , f )
