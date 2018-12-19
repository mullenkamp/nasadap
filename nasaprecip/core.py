# -*- coding: utf-8 -*-
"""
Created on Wed Sep 12 10:27:09 2018

@author: MichaelK
"""
import os
import pandas as pd
import xarray as xr
from pydap.client import open_url
from pydap.cas.urs import setup_session

base_url_trmm = 'https://disc2.gesdisc.eosdis.nasa.gov:443/opendap/TRMM_L3'
base_url_gpm = 'https://gpm1.gesdisc.eosdis.nasa.gov:443/opendap/GPM_L3'

product_dict = {'trmm': {'daily': '3B42_Daily', 'subdaily': '3B42'}, 'gpm': {'daily': '3IMERGDF', 'subdaily': '3IMERGHH'}}

trmm_daily_path = '{mission}_{product}.7/{year}/{month}/{product}.{date}.7.nc4'
gpm_daily_path = '{mission}_{product}.05/{year}/{month}/3B-DAY{run}.MS.MRG.3IMERG.{date}-S000000-E235959.V05.nc4'

trmm_subdaily_path = '{mission}_{product}.7/{year}/{dayofyear}/{product}.{date}.{hour}.7.HDF'
gpm_subdaily_path = '{mission}_{product}.05/{year}/{dayofyear}/3B-HHR{run}.MS.MRG.3IMERG.{date}-S{time_start}-E{time_end}.{minutes}.V05B.HDF5'

class Nasa(object):
    """
    Class to download, select, and convert trmm and gpm data.

    Parameters
    ----------
    username : str
        The username for the login.
    password : str
        The password for the login.
    mission : str
        Should be either trmm or gpm.
    cach_dir : str or None
        A path to cache the netcdf files for future reading or None.

    Returns
    -------
    Nasa object
    """
    def __init__(self, username, password, mission, cache_dir=None):
        if mission == 'trmm':
            self.base_url = base_url_trmm
            self.filepath = trmm_daily_path

        elif mission == 'gpm':
            self.base_url = base_url_gpm
            self.filepath = gpm_daily_path
        else:
            raise ValueError('mission should be either trmm or gpm')

        self.mission = mission

        self.cache_dir = cache_dir

        self.session = setup_session(username, password, check_url=self.base_url)

    def close(self):
        """
        Closes the session.
        """
        self.session.close()


    def get_dataset_types(self):
        """
        Function to get all of the dataset types and associates attributes.

        Returns
        -------
        dict
            of dataset types as the keys
        """
        url2 = self.filepath.format(mission=self.mission.upper(), product=product_dict[self.mission]['daily'], year='2016', month='01', date='20160101', run='')
        url3 = self.base_url + '/' + url2

        dataset = open_url(url3, session=self.session)

        dataset_dict = {}
        for i in dataset:
            dataset_dict.update({dataset[i].name: dataset[i].attributes})

        return dataset_dict


    def get_data(self, dataset_types, from_date, to_date, min_lat=None, max_lat=None, min_lon=None, max_lon=None):
        """
        Function to download trmm or gpm data and convert it to an xarray dataset.

        Parameters
        ----------
        dataset_types : str or list of str
            The dataset types variable to be extracted.
        from_date : str
            The start date
        to_date : str
            The end date
        min_lat : int, float, or None
            The minimum lat to extract in WGS84 decimal degrees.
        max_lat : int, float, or None
            The maximum lat to extract in WGS84 decimal degrees.
        min_lon : int, float, or None
            The minimum lon to extract in WGS84 decimal degrees.
        max_lon : int, float, or None
            The maximum lon to extract in WGS84 decimal degrees.

        Returns
        -------
        xarray dataset
            Coordinates are time, lon, lat
        """
        if isinstance(dataset_types, str):
            dataset_types = [dataset_types]
        dates = pd.date_range(from_date, to_date)

        urls2 = [self.filepath.format(mission=self.mission.upper(), product=product_dict[self.mission]['daily'], year=i.strftime('%Y'), month=i.strftime('%m'), date=i.strftime('%Y%m%d'), run='') for i in dates]

        if isinstance(self.cache_dir, str):
            save_dirs = set([os.path.join(self.cache_dir, os.path.split(s)[0]) for s in urls2])
            for path in save_dirs:
                if not os.path.exists(path):
                    os.makedirs(path)

        ds_list = []
        for u in urls2:
            try:
                u1 = os.path.join(self.cache_dir, u)
                ds = xr.open_dataset(u1)
                ds2 = ds[dataset_types].sel(lat=slice(min_lat, max_lat), lon=slice(min_lon, max_lon))
                print('Found local file')
            except:
                print('Downloading from web')
                u1 = self.base_url + '/' + u
                store = xr.backends.PydapDataStore.open(u1, session=self.session)
                ds = xr.open_dataset(store)
                ds2 = ds[dataset_types].sel(lat=slice(min_lat, max_lat), lon=slice(min_lon, max_lon))

                lat = ds2.lat.values
                lon = ds2.lon.values

                for ar in ds2.data_vars:
                    da1 = xr.DataArray(ds2[ar].values.reshape(1, len(lon), len(lat)), coords=[[pd.Timestamp(ds2.attrs['BeginDate'])], lon, lat], dims=['time', 'lon', 'lat'], name=ar)
                    da1.attrs = ds2[ar].attrs
                    ds2[ar] = da1

            print(u1)

            ## Save data as cache
            if isinstance(self.cache_dir, str):
                u2 = os.path.join(self.cache_dir, u)
                if not os.path.isfile(u2):
                    print('Saving data')
                    ds2.to_netcdf(u2)

            ds_list.append(ds2)

        ds_all = xr.concat(ds_list, dim='time')

        return ds_all
