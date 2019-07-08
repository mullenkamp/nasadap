# -*- coding: utf-8 -*-
"""
Created on Wed May  9 15:12:14 2018

@author: MichaelEK
"""
import pytest
import xarray as xr
from nasadap import Nasa, parse_nasa_catalog
from time import time
import pandas as pd

pd.options.display.max_columns = 10

###############################
### Parameters

mission = 'gpm'
version = 5
product2d = '3IMERGHHE'
product2e = '3IMERGHHL'
product2f = '3IMERGHH'
dataset_type1 = 'precipitation'
dataset_type2 = 'precipitationCal'
min_lat=-49
max_lat=-33
min_lon=165
max_lon=180
#cache_dir = r'\\fs02\GroundWaterMetData$\nasa\cache\nz'
cache_dir = ''

###############################
### Tests

## gpm

@pytest.mark.parametrize('product', [product2d, product2e, product2f])
def test_gpm_catalog(product):
    min_max1 = parse_nasa_catalog(mission, product, version, min_max=True)

    assert len(min_max1) > 2

