# -*- coding: utf-8 -*-
"""
Created on Wed May  9 15:12:14 2018

@author: MichaelEK
"""
import pytest
from nasaprecip import Nasa
import requests
from lxml import html
from bs4 import BeautifulSoup
import re
import urllib3
import pydap.lib

###############################
### Parameters

username = '' # Need to change for test
password = '' # Need to change for test
mission1 = 'trmm'
mission2 = 'gpm'
from_date = '2018-01-01'
to_date = '2018-01-03'
dataset_type1 = 'precipitation'
dataset_type2 = 'precipitationCal'
min_lat=-48
max_lat=-34
min_lon=166
max_lon=179
cache_dir = r'E:\ecan\local\temp\nasa'

###############################
### Tests


def test_trmm():
    ge = Nasa(username, password, mission1, cache_dir)
    ds_types = ge.get_dataset_types()
    ds1 = ge.get_data(dataset_type1, from_date, to_date, min_lat, max_lat, min_lon, max_lon)

    assert ds1[dataset_type1].shape == (3, 52, 56)


def test_gpm():
    ge = Nasa(username, password, mission2, cache_dir)
    ds_types = ge.get_dataset_types()
    ds2 = ge.get_data(dataset_type2, from_date, to_date, min_lat, max_lat, min_lon, max_lon)

    assert ds2[dataset_type2].shape == (3, 130, 140)

#################################
### Other
url1 = 'https://gpm1.gesdisc.eosdis.nasa.gov/opendap/hyrax/GPM_L3/GPM_3IMERGDL.05/contents.html'
url2 = 'https://gpm1.gesdisc.eosdis.nasa.gov/opendap/hyrax/GPM_L3/GPM_3IMERGDL.05/2014/contents.html'
url3 = 'https://gpm1.gesdisc.eosdis.nasa.gov/opendap/hyrax/GPM_L3/GPM_3IMERGDL.05/2014/03/contents.html'
page = requests.get(url3)
tree = html.fromstring(page.content)

soup = BeautifulSoup(page.content)
links = []

for link in soup.findAll('a', attrs={'href': re.compile("nc4.html")}):
    links.append(link.text[:-1])

print(links)

l1 = links[0]

def min_max_dates(mission, product):













