# -*- coding: utf-8 -*-
"""
Created on Wed May  9 15:12:14 2018

@author: MichaelEK
"""
import pytest
import xarray as xr
from nasadap import Nasa, min_max_dates
from time import time

###############################
### Parameters

username = '' # Need to change for test
password = '' # Need to change for test
mission1 = 'trmm'
mission2 = 'gpm'
product1a = '3B42_Daily'
product1b = '3B42'
product2a = '3IMERGDE'
product2b = '3IMERGDL'
product2c = '3IMERGDF'
product2d = '3IMERGHHE'
product2e = '3IMERGHHL'
product2f = '3IMERGHH'
from_date = '2018-01-20'
to_date = '2018-01-28'
dataset_type1 = 'precipitation'
dataset_type2 = 'precipitationCal'
min_lat=-49
max_lat=-33
min_lon=165
max_lon=180
cache_dir = r'\\fs02\GroundWaterMetData$\nasa\cache\nz'

###############################
### Tests

## trmm

def test_trmm_session():
    ge = Nasa(username, password, mission1, cache_dir)

    assert ge is not None

ge = Nasa(username, password, mission1, cache_dir)


def test_trmm_dataset_types():
    ds_types = ge.get_dataset_types()

    assert ds_types is not None


def test_trmm1():
    ds1 = ge.get_data(product1a, dataset_type1, from_date, to_date, min_lat, max_lat, min_lon, max_lon)

    assert ds1[dataset_type1].shape == (4, 60, 64)


def test_trmm2():
    ds1 = ge.get_data(product1b, dataset_type1, from_date, to_date, min_lat, max_lat, min_lon, max_lon)

    assert ds1[dataset_type1].shape == (32, 60, 64)

ge.close()

## gpm


def test_gpm_session():
    ge = Nasa(username, password, mission2, cache_dir)

    assert ge is not None

ge = Nasa(username, password, mission2, cache_dir)


def test_gpm_dataset_types():
    ds_types = ge.get_dataset_types()

    assert ds_types is not None


def test_gpm1():
    ds2 = ge.get_data(product2a, dataset_type2, from_date, to_date, min_lat, max_lat, min_lon, max_lon)

    assert ds2[dataset_type2].shape == (4, 150, 160)


def test_gpm2():
    ds2 = ge.get_data(product2b, dataset_type2, from_date, to_date, min_lat, max_lat, min_lon, max_lon)

    assert ds2[dataset_type2].shape == (4, 150, 160)


def test_gpm3():
    ds2 = ge.get_data(product2c, dataset_type2, from_date, to_date, min_lat, max_lat, min_lon, max_lon)

    assert ds2[dataset_type2].shape == (4, 150, 160)


def test_gpm4():
    ds2 = ge.get_data(product2d, dataset_type2, from_date, to_date, min_lat, max_lat, min_lon, max_lon)

    assert ds2[dataset_type2].shape == (192, 150, 160)


def test_gpm5():
    ds2 = ge.get_data(product2e, dataset_type2, from_date, to_date, min_lat, max_lat, min_lon, max_lon)

    assert ds2[dataset_type2].shape == (192, 150, 160)


def test_gpm6():
    ds2 = ge.get_data(product2f, dataset_type2, from_date, to_date, min_lat, max_lat, min_lon, max_lon)

    assert ds2[dataset_type2].shape == (192, 150, 160)

ge.close()

#################################
### Other

#hdf1 = 'https://disc2.gesdisc.eosdis.nasa.gov:443/opendap/TRMM_L3/TRMM_3B42.7/1998/002/3B42.19980102.03.7.HDF'
#nc1 = 'https://disc2.gesdisc.eosdis.nasa.gov:443/opendap/TRMM_L3/TRMM_3B42_Daily.7/1998/01/3B42_Daily.19980101.7.nc4'
#nc2 = 'https://gpm1.gesdisc.eosdis.nasa.gov/opendap/hyrax/GPM_L3/GPM_3IMERGDF.05/2014/03/3B-DAY.MS.MRG.3IMERG.20140312-S000000-E235959.V05.nc4'
#hdf2 = 'https://gpm1.gesdisc.eosdis.nasa.gov/opendap/hyrax/GPM_L3/GPM_3IMERGHH.05/2014/071/3B-HHR.MS.MRG.3IMERG.20140312-S000000-E002959.0000.V05B.HDF5'
#
#store = xr.backends.PydapDataStore.open(hdf1, session=ge.session)
#ds = xr.open_dataset(store)
#
#t1 = ds.attrs['FileHeader'].split(';\n')
#t2 = dict([t.split('=') for t in t1 if t != ''])

#ds3 = xr.Dataset(coords={'time': [], 'lat': [], 'lon': []})
#ds3 = xr.Dataset()
#
#ds3.to_netcdf(t1, unlimited_dims='time')
#
#ds3 = ds2.copy()
#
#ds3['time'] = ds3.time.to_series() + pd.DateOffset(days=2)
#
#with xr.open_mfdataset(t1) as ds:
#    print(ds)
##    ds4 = xr.concat([ds2, ds], dim='time')
#    ds4 = ds.combine_first(ds2)
#    ds5 = ds4.combine_first(ds3)
##    ds4 = xr.merge([ds, ds2])
##    ds5 = xr.merge([ds4, ds2])
#    print(ds5)
#
#ds4.to_netcdf(t1, mode='a', unlimited_dims='time')
#ds5.to_netcdf(t1, mode='a', unlimited_dims='time')

ge = Nasa(username, password, mission1, cache_dir)

start1 = time()
ds1 = ge.get_data(product1a, dataset_type1, from_date, to_date, min_lat, max_lat, min_lon, max_lon, dl_sim_count=65)
end1 = time()

diff1 = end1 - start1





