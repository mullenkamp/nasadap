# -*- coding: utf-8 -*-
"""
Created on Wed Sep 12 10:27:09 2018

@author: MichaelK
"""
import pandas as pd
import xarray as xr
from pydap.client import open_url
from pydap.cas.urs import setup_session

base_url_trimm = 'https://disc2.gesdisc.eosdis.nasa.gov:443/opendap/TRMM_L3'
base_url_gpm = 'https://gpm1.gesdisc.eosdis.nasa.gov:443/opendap/GPM_L3'

product_dict = {'trmm': {'daily': '3B42_Daily', 'subdaily': '3B42'}, 'gpm': {'daily': '3IMERGDF', 'subdaily': '3IMERGHH'}}

trmm_url_str = '{base_url}/{mission}_{product}.7/{year}/{month}/{product}.{date}.7.nc4'
gpm_url_str = '{base_url}/{mission}_{product}.05/{year}/{month}/3B-DAY.MS.MRG.3IMERG.{date}-S000000-E235959.V05.nc4'


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

    Returns
    -------
    Nasa object
    """
    def __init__(self, username, password, mission):
        if mission == 'trmm':
            self.base_url = base_url_trimm
        elif mission == 'gpm':
            self.base_url = base_url_gpm
        else:
            raise ValueError('mission should be either trmm or gpm')

        self.mission = mission

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
        url2 = '{mission}_{product}/2016/01/'.format(mission=self.mission.upper(), product=product_dict[self.mission]['daily'])
        if self.mission == 'gpm':
            file_name = '3B-DAY.MS.MRG.3IMERG.20160101-S000000-E235959.V05.nc4'
        elif self.mission == 'trmm':
            file_name = '3B42_Daily.20160101.7.nc4'

        full_url = self.base_url + '/' + url2 + file_name

        dataset = open_url(full_url, session=self.session)

        dataset_dict = {}
        for i in dataset:
            dataset_dict.update({i.name: i.attributes})

        return dataset_dict


    def get_data(self, dataset_type, from_date, to_date, min_lat=None, max_lat=None, min_lon=None, max_lon=None):
        """
        Function to download trmm or gpm data and convert it to an xarray dataset.

        Parameters
        ----------
        dataset_type : str
            The dataset type variable to be extracted.
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
        dates = pd.date_range(from_date, to_date)

        if self.mission == 'trmm':
            urls1 = trmm_url_str
        elif self.mission == 'gpm':
            urls1 = gpm_url_str

        urls2 = [urls1.format(base_url=self.base_url, mission=self.mission.upper(), product=product_dict[self.mission]['daily'], year=i.strftime('%Y'), month=i.strftime('%m'), date=i.strftime('%Y%m%d')) for i in dates]

        ds_list = []
        for u in urls2:
            print(u)
            store = xr.backends.PydapDataStore.open(u, session=self.session)
            ds = xr.open_dataset(store)
            ds2 = ds[[dataset_type]].sel(lat=slice(min_lat, max_lat), lon=slice(min_lon, max_lon))

            lat = ds2.lat.values
            lon = ds2.lon.values

            values1 = ds2[dataset_type].values

            da1 = xr.DataArray(values1.reshape(1, len(lon), len(lat)), coords=[[pd.Timestamp(ds2.attrs['BeginDate'])], lon, lat], dims=['time', 'lon', 'lat'], name=dataset_type)
            da1.attrs = ds2[dataset_type].attrs

            ds3 = da1.to_dataset()
            ds3.attrs['title'] = ds2.attrs['title']
            ds3.attrs['ProductionTime'] = ds2.attrs['ProductionTime']

            ds_list.append(ds3)

        ds_all = xr.concat(ds_list, dim='time')

        return ds_all
