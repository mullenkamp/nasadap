# -*- coding: utf-8 -*-
"""
Created on Wed May  9 15:12:14 2018

@author: MichaelEK
"""
import pytest
from nasaprecip import Nasa

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


###############################
### Tests


def test_trmm():
    ge = Nasa(username, password, mission1)
    ds1 = ge.get_data(dataset_type1, from_date, to_date, min_lat, max_lat, min_lon, max_lon)

    assert ds1[dataset_type1].shape == (3, 52, 56)


def test_gpm():
    ge = Nasa(username, password, mission2)
    ds2 = ge.get_data(dataset_type2, from_date, to_date, min_lat, max_lat, min_lon, max_lon)

    assert ds2[dataset_type2].shape == (3, 130, 140)

