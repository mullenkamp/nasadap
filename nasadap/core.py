# -*- coding: utf-8 -*-
"""
Created on Wed Sep 12 10:27:09 2018

@author: MichaelK
"""
import os
import pandas as pd
import xarray as xr
import requests
from lxml import etree
from pydap.client import open_url
from pydap.cas.urs import setup_session
from util import min_max_dates, mission_product_dict


class Nasa(object):
    """
    Class to download, select, and convert NASA data via opendap.

    Parameters
    ----------
    username : str
        The username for the login.
    password : str
        The password for the login.
    mission : str
        Mission name.
    cach_dir : str or None
        A path to cache the netcdf files for future reading or None.

    Returns
    -------
    Nasa object
    """
    missions_products = {m: list(mission_product_dict[m]['products'].keys()) for m in mission_product_dict}


    def __init__(self, username, password, mission, cache_dir=None):
        self.session(username, password, mission, cache_dir)

    def session(self, username, password, mission, cache_dir=None):
        """
        Function to initiate a dap session.

        Parameters
        ----------
        username : str
            The username for the login.
        password : str
            The password for the login.
        mission : str
            Mission name.
        cach_dir : str or None
            A path to cache the netcdf files for future reading or None.

        Returns
        -------
        Nasa object
        """
        if mission in mission_product_dict:
            self.mission_dict = mission_product_dict[mission]
        else:
            raise ValueError('mission should be one of: ' + ', '.join(mission_product_dict.keys()))

        self.mission = mission

        self.cache_dir = cache_dir

        self.session = setup_session(username, password, check_url='/'.join([self.mission_dict['base_url'], 'opendap',  self.mission_dict['process_level']]))


    def close(self):
        """
        Closes the session.
        """
        self.session.close()


    def get_dataset_types(self):
        """
        Function to get all of the dataset types and associated attributes for a mission.

        Returns
        -------
        dict
            of dataset types as the keys
        """
        dataset = open_url(self.mission_dict['example_path'], session=self.session)

        dataset_dict = {}
        for i in dataset:
            dataset_dict.update({dataset[i].name: dataset[i].attributes})

        return dataset_dict


    def get_data(self, product, dataset_types, from_date=None, to_date=None, min_lat=None, max_lat=None, min_lon=None, max_lon=None):
        """
        Function to download trmm or gpm data and convert it to an xarray dataset.

        Parameters
        ----------
        product : str
            Data product associated with the mission.
        dataset_types : str or list of str
            The dataset types variable to be extracted.
        from_date : str or None
            The start date that you want data in the format 2000-01-01.
        to_date : str or None
            The end date that you want data in the format 2000-01-01.
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
        if product not in self.mission_dict['products']:
            raise ValueError('product must be one of: ' + ', '.join(self.mission_dict['products'].keys()))
        else:
            product_dict = self.mission_dict['products']
            file_path1 = product_dict[product]
            file_path = os.path.split(file_path1)[0]

        if isinstance(dataset_types, str):
            dataset_types = [dataset_types]

        min_max = min_max_dates(self.mission, product)
        min_date = min_max['start_date'][0]
        max_date = min_max['end_date'][0]

        if isinstance(from_date, str):
            from_date = pd.Timestamp(from_date)
            if min_date > from_date:
                from_date = min_date
        else:
            from_date = min_date
        if isinstance(to_date, str):
            to_date = pd.Timestamp(to_date)
            if max_date < to_date:
                to_date = max_date
        else:
            to_date = max_date

        dates = pd.date_range(from_date, to_date)

        base_url = self.mission_dict['base_url']

        if 'dayofyear' in file_path:
            print('Parsing file list from NASA server...')
            url_list = []
            for d in dates:
                path1 = file_path.format(mission=self.mission.upper(), product=product, year=d.year, dayofyear=d.dayofyear)
                path2 = '/'.join([self.mission_dict['process_level'], path1])
                url1 = '/'.join([base_url, 'opendap', path2, 'catalog.xml'])
                page1 = requests.get(url1)
                et = etree.fromstring(page1.content)
                urls2 = [base_url + c.attrib['ID'] for c in et.getchildren()[2].getchildren()]
                url_list.extend(urls2)
        if 'month' in file_path:
            print('Generating urls...')
            url_list = ['/'.join([base_url, 'opendap', self.mission_dict['process_level'],  file_path1.format(mission=self.mission.upper(), product=product, year=d.year, month=d.month, date=d.strftime('%Y%m%d'))]) for d in dates]

        url_dict = {u: self.mission_dict['process_level'] + u.split(self.mission_dict['process_level'])[1] for u in url_list}
        if isinstance(self.cache_dir, str):
            for_cache = [os.path.split(u)[0] for u in set(url_dict.values())]
            save_dirs = [os.path.join(self.cache_dir, paths) for paths in for_cache]
            for path in save_dirs:
                if not os.path.exists(path):
                    os.makedirs(path)

        print('Reading files...')
        ds_list = []
        for u, u0 in url_dict.items():
            try:
                u1 = os.path.join(self.cache_dir, u0)
                ds = xr.open_dataset(u1)
                ds2 = ds[dataset_types].sel(lat=slice(min_lat, max_lat), lon=slice(min_lon, max_lon))
                print('Found local file')
            except:
                print('Downloading from web...')
                u1 = u
                store = xr.backends.PydapDataStore.open(u1, session=self.session)
                ds = xr.open_dataset(store)
                if 'nlon' in ds:
                    ds.rename({'nlon': 'lon', 'nlat': 'lat'}, inplace=True)
                ds2 = ds[dataset_types].sel(lat=slice(min_lat, max_lat), lon=slice(min_lon, max_lon))

                lat = ds2.lat.values
                lon = ds2.lon.values

                for ar in ds2.data_vars:
                    ds_date1 = ds.attrs['FileHeader'].split(';\n')
                    ds_date2 = dict([t.split('=') for t in ds_date1 if t != ''])
                    ds_date = pd.to_datetime(ds_date2['StopGranuleDateTime'])
                    da1 = xr.DataArray(ds2[ar].values.reshape(1, len(lon), len(lat)), coords=[[ds_date], lon, lat], dims=['time', 'lon', 'lat'], name=ar)
                    da1.attrs = ds2[ar].attrs
                    ds2[ar] = da1

            print(u1)

            ## Save data as cache
            if isinstance(self.cache_dir, str):
                u2 = os.path.join(self.cache_dir, u0)
                if not os.path.isfile(u2):
                    print('Saving data')
                    ds2.to_netcdf(u2)

            ds_list.append(ds2)

        ds_all = xr.concat(ds_list, dim='time')

        return ds_all
