import unittest
import shutil
#from usr.lib.python2.7.dist-packages.irrigationbone/ import func_name
import sys
sys.path.insert(0, '/usr/lib/python2.7/dist-packages/irrigationbone/')
import get_pm_by_pos
import json

class TestGetPmByPos(unittest.TestCase):
    def test_get_station_pos(self):
        #get_station_pos_file='get_station_pos.json'
        #shutil.copyfile(get_station_pos_file, 'MeteoMapService.json')
        filename = 'MeteoMapService.json'
        with open(filename,'rb') as f:
            MeteoMapService = json.load(f, encoding='utf8')
        my_pos=( 32.1733282, 34.840809799999995 )
        with open('city_pos.json') as f:
            city_pos=json.load(f, encoding='utf8')
        debug=True
        test_city_pos=get_pm_by_pos.get_station_pos(my_pos,MeteoMapService)
        self.assertFalse( cmp(test_city_pos,city_pos))

if __name__ == '__main__':
    unittest.main()
