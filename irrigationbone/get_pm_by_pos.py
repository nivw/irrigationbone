#!/usr/bin/python
import requests
from datetime import datetime
import os
import json
from bs4 import BeautifulSoup
from logger import logger
from get_pm_by_pos_config import *

def get_MeteoMapService(debug=False):
  MeteoMapService = False
  filename = 'MeteoMapService.json'
  if debug and os.path.exists(filename):
    with open(filename,'rb') as f:
      MeteoMapService = json.load(f, encoding='utf8')
  if not MeteoMapService:
    #when = "2015-10-30T00:18:00.616Z"
    when = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    headers = {'User-Agent' : 'Mozilla 5.10', 'Content-Type' : 'application/json', 'Referer' : 'http://www.meteo.co.il/MeteoMap.aspx'}
    payload = {"stationID":"-9999","dateTime":when,"displayLastReceivedOnly":1}
    url = 'http://www.meteo.co.il/Services/MeteoMapService.asmx/GetStationsWithData'
    r = requests.post(url, data=json.dumps(payload), headers = headers, timeout=60)
    MeteoMapService = json.loads(r.content)
    with open(filename, 'wb') as f:
      f.write(r.content)
  return MeteoMapService

def get_station_pos(my_pos, MeteoMapService):
  my_pos = (float(my_pos[0]), float(my_pos[1]))
  city_pos = dict()
  for item in MeteoMapService['d']:
    try:
      latitude = float(item['latitude'])
      longitude = float(item['longitude'])
    except ValueError:
      #logger.debug(item['name'][::-1]+u' is missing location')
      distance = 1000
    else:
      distance = ((my_pos[0] - latitude)**2) + ((my_pos[1] - longitude)**2)
      logger.info(u'Name: '+item['name'][::-1]+' longitude: ' +item['longitude'] + ' latitude: ' + item['latitude'] + ' distance: {}'.format(distance))
      #city_pos[item['name']] = {'longitude' : item['longitude'], 'latitude': item['latitude']}
      city_pos[item['name']] = distance
      with open('city_pos.json','wb') as f:
        json.dump(city_pos,f)
  return city_pos

def get_pm_html(debug=False):
  filename = 'DynamicTable.html'
  html = False
  if debug and os.path.exists(filename):
    with open(filename,'rb') as f:
      html = f.read()
  if not html:
    url = 'http://www.meteo.co.il/DynamicTable.aspx?G_ID=8'
    headers = {'User-Agent' : 'Mozilla 5.10'}
    html = requests.get(url, headers = headers, timeout=60).content
    with open(filename, 'wb') as f:
      f.write(html)
  return html

def get_compensation_coef( city_pos ):
  while len(city_pos):
    min_distance = min(city_pos.values())
    for name, distance in city_pos.iteritems():
      if min_distance == distance:
        break
    coef = PM_COMPENSATION_COEF.get(name)
    if coef:
      logger.info(u'Using compensation coef for: {} value: {}'.format(name[::-1], coef))
      return coef
    city_pos.pop(name)
  
def get_distance_to_pm( city_pos, DynamicTable ):
  soup = BeautifulSoup(DynamicTable, 'html.parser')
  try:
    table = soup.find('table')
  except AttributeError as e:
      logger.error('No tables found, in {}'.format(DynamicTable))
      with open('faulty_DynamicTable.html',wb) as f:
        f.write(DynamicTable)
  rows = table.find_all('tr')
  results = dict()
  for row in rows:
    table_data = row.find_all('td')
    if len(table_data) < 11:
      continue
    st_name = table_data[0].get_text().strip()
    st_name = st_name.replace('\n','').replace('\r','').replace('\t','')
    st_pm = table_data[11].get_text().strip()
    #st_pm = st_pm.replace('\n','').replace('\r','').replace('\t','')
    st_rain = table_data[9].get_text().strip()
    logger.info('st_name: '+st_name[::-1]+' pm coef: '+st_pm+' mm_rain: '+st_rain)
    for name, distance in city_pos.iteritems():
      if st_name.startswith(name):
        results[distance] = (st_pm, st_rain, name[::-1])
  return results

def pm_and_rain_are_valid(pm, rain):
  return pm and pm > 0 and pm < 10 and rain >=0

def sort_distance_to_pm(results):
  distance_to_pm = list()
  near_st = None
  #for i in range(len(results)):
  while len(results):
    min_distance = min(results.keys())
    try:
      pm = float(results[min_distance][0])
      rain = float(results[min_distance][1])
    except ValueError:
      pass
    else:
      if pm_and_rain_are_valid(pm, rain) and len(results[min_distance]) >2:
        if not near_st:
          near_st = results[min_distance][2]
        name = results[min_distance][2]
        distance_to_pm.append((pm, rain, name))
        logger.info(u'Sorted pm by distance: {} {} {}'.format(pm, rain, name))
    finally:
      results.pop(min_distance)
  return (distance_to_pm, near_st)

def get_pm_by_pos(my_pos):
  MeteoMapService = get_MeteoMapService()
  city_pos = get_station_pos(my_pos, MeteoMapService)
  DynamicTable = get_pm_html()
  results = get_distance_to_pm(city_pos,DynamicTable)
  (distance_to_pm, near_st) = sort_distance_to_pm(results)
  coef = get_compensation_coef(city_pos)
  return (distance_to_pm, near_st, coef)

def get_st_name(my_pos):
  city_pos = get_station_pos(my_pos)
  min_distance = min(city_pos.values())
  for name, distance in city_pos.iteritems():
    if distance == min_distance:
      return name[::-1]

if __name__ == '__main__':
  my_pos = (32.1733282, 34.840809799999995)
  debug = True
  (distance_to_pm, near_st) = get_pm_by_pos(my_pos)
  print(distance_to_pm)
  print(near_st)
