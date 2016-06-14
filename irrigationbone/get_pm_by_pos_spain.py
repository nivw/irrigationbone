from bs4 import BeautifulSoup
import requests

headers = {'User-Agent' : 'Mozilla 5.10'}
url = 'http://crea.uclm.es/siar/estaciones/#localizacion'
html = requests.get(url, headers=headers).content.decode("utf-8")
soup = BeautifulSoup(html,'html.parser')

row = soup.find(id="localizacion").find("tbody").find("tr").findAll("td")

print(int(row[3].text))
print(int(row[4].text))
for station in soup.find(id="localizacion").find("tbody").find_all("tr"):
    line = st.find_all('td')
    print('st_name: {} latitude: {} longtitude: {}'.format(line[1], line[2], line[3]))


for i,r in enumerate(soup.find_all('table')):
  for s in r.find_all("tbody"):
    for l in s.find_all('tr'):
      line = l.find_all('td')
      print i, line[1], line[2]

import utm
print('Convert UTM to latitude longtitude')
utm.to_latlon(x, y, 30, 'T')
#utm.to_latlon(593160.0, 4345720.0, 30, 'T')
#Out[6]: (39.255808082315035, -1.9202609965516344)

                                             
