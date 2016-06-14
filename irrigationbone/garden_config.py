import json
from munch import *

garden_config_file = '/home/debian/cwvw.json'
DEFAULT_POSITION = (34.77814, 31.81355)

class GardenConfig(Munch):
  """Garden config in a Munch object"""
  def __init__(self):
    try:
      with open(garden_config_file) as f:
        garden_dict = json.load(f)
    except Exception as e:
      print >> sys.stderr, 'Exception in loading garden config: {}'.format( e )
    if garden_dict and garden_dict.get('latitude') and garden_dict.get('longitude'):
        garden_dict['latitude'], garden_dict['longitude'] = float(garden_dict['latitude']), float(garden_dict['longitude'])      
    else:
        garden_dict['latitude'], garden_dict['longitude'] = DEFAULT_POSITION

    for k,v in garden_dict.items():
      self.update({k:v})
