# -*- coding: utf-8 -*-
"""
Created on Wed Sep 12 10:27:09 2018

@author: MichaelK
"""
import os
import pickle
import pandas as pd
import xarray as xr
import requests
from time import sleep
from lxml import etree
import itertools
from multiprocessing.pool import ThreadPool
#from pydap.client import open_url
from pydap.cas.urs import setup_session
from nasadap.util import parse_nasa_catalog, mission_product_dict, master_datasets
#from util import parse_nasa_catalog, mission_product_dict, master_datasets

#######################################
### Parameters

file_index_name = 'file_index.pickle'

#######################################


def download_files(url, path, session, master_dataset_list, dataset_types, min_lat, max_lat, min_lon, max_lon):
#    print('Downloading and saving to...')
    print(path)
#    print(url)
    counter = 4
    while counter > 0:
        try:
            store = xr.backends.PydapDataStore.open(url, session=session)
            ds = xr.open_dataset(store, decode_cf=False)

            if 'nlon' in ds:
                ds = ds.rename({'nlon': 'lon', 'nlat': 'lat'})
            ds2 = ds[master_dataset_list].sel(lat=slice(min_lat, max_lat), lon=slice(min_lon, max_lon))

            lat = ds2.lat.values
            lon = ds2.lon.values

            ds_date1 = ds.attrs['FileHeader'].split(';\n')
            ds_date2 = dict([t.split('=') for t in ds_date1 if t != ''])
            ds_date = pd.to_datetime([ds_date2['StopGranuleDateTime']]).tz_convert(None)
            ds2['time'] = ds_date

            for ar in ds2.data_vars:
                da1 = xr.DataArray(ds2[ar].values.reshape(1, len(lon), len(lat)), coords=[ds_date, lon, lat], dims=['time', 'lon', 'lat'], name=ar)
                da1.attrs = ds2[ar].attrs
                ds2[ar] = da1

            counter = 0
        except Exception as err:
            print(err)
            print('Retrying in 3 seconds...')
            counter = counter - 1
            sleep(3)

    ## Save data as cache
    if not os.path.isfile(path):
#        print('Saving data to...')
#        print(path)
        ds2.to_netcdf(path)

    return ds2[dataset_types]


def parse_dap_xml(date, file_path, mission, product, version, process_level, base_url):
    path1 = file_path.format(mission=mission.upper(), product=product, year=date.year, dayofyear=date.dayofyear, version=version)
    path2 = '/'.join([process_level, path1])
    url1 = '/'.join([base_url, 'opendap', path2, 'catalog.xml'])
    page1 = requests.get(url1)
    et = etree.fromstring(page1.content)
    urls2 = [base_url + c.attrib['ID'] for c in et.getchildren()[3].getchildren() if not '.xml' in c.attrib['ID']]
    return urls2


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
        A path to cache the netcdf files for future reading. If None, the currently working directory is used.

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
            A path to cache the netcdf files for future reading. If None, the currently working directory is used.

        Returns
        -------
        Nasa object
        """
        if mission in mission_product_dict:
            self.mission_dict = mission_product_dict[mission]
        else:
            raise ValueError('mission should be one of: ' + ', '.join(mission_product_dict.keys()))

        self.mission = mission

        if isinstance(cache_dir, str):
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)
            self.cache_dir = cache_dir
        else:
            self.cache_dir = os.getcwd()

        self.session = setup_session(username, password, check_url='/'.join([self.mission_dict['base_url'], 'opendap',  self.mission_dict['process_level']]))


    def close(self):
        """
        Closes the session.
        """
        self.session.close()


    def get_products(self):
        """
        Function to get the available products for the mission.

        Returns
        -------
        list
        """
        return list(self.mission_dict['products'].keys())


    @staticmethod
    def get_dataset_types(product):
        """
        Function to get all of the dataset types and associated attributes for a mission.

        Parameters
        ----------
        product : str
            The mission product

        Returns
        -------
        list
        """
        return master_datasets[product]


    def get_data(self, product, version, dataset_types, from_date=None, to_date=None, min_lat=None, max_lat=None, min_lon=None, max_lon=None, dl_sim_count=30, check_local=True):
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
        dl_sim_count : int
            The number of simultaneous downloads on a single thread. Speed could be increased with more simultaneous downloads, but up to a limit of the PC's single thread speed. Also, NASA's opendap server seems to have a limit to the total number of simultaneous downloads. 50-60 seems to be around the max.
        check_local : bool
            Should the local files be checked and read? Pass False if you only want to download files and not check for local files. Any local files will be overwritten!

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
        master_dataset_list = master_datasets[product]

        if isinstance(dataset_types, str):
            dataset_types = [dataset_types]

        min_max = parse_nasa_catalog(self.mission, product, version, min_max=True)
        min_date = min_max['from_date'][0].tz_convert(None)
        max_date = min_max['to_date'].iloc[-1].tz_convert(None)

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

        print('Getting data from {start} to {end}'.format(start=str(from_date.date()), end=str(to_date.date())))

        dates = pd.date_range(from_date, to_date)

        base_url = self.mission_dict['base_url']

        ## Determine what files are needed
        if 'dayofyear' in file_path1:
            print('Parsing file list from NASA server...')
            file_path = os.path.split(file_path1)[0]
            iter2 = [(date, file_path, self.mission, product, version, self.mission_dict['process_level'], base_url) for date in dates]
            url_list1 = ThreadPool(30).starmap(parse_dap_xml, iter2)
            url_list = list(itertools.chain.from_iterable(url_list1))
        elif 'month' in file_path1:
            print('Generating urls...')
            url_list = ['/'.join([base_url, 'opendap', self.mission_dict['process_level'],  file_path1.format(mission=self.mission.upper(), product=product, year=d.year, month=d.month, date=d.strftime('%Y%m%d'), version=version)]) for d in dates]

        if 'hyrax' in url_list[0]:
            split_text = 'hyrax/'
        else:
            split_text = 'opendap/'
        url_dict = {u: os.path.join(self.cache_dir, os.path.splitext(u.split(split_text)[1])[0].replace('/', '\\') + '.nc4') for u in url_list}
        path_set = set(url_dict.values())

        save_dirs = set([os.path.split(u)[0] for u in url_dict.values()])
        for path in save_dirs:
            if not os.path.exists(path):
                os.makedirs(path)

        ## Find out what files exist locally
        product_dir = file_path1.split('/')[0].format(mission=self.mission.upper(), product=product, version=version)
        product_path = os.path.join(self.cache_dir, self.mission_dict['process_level'], product_dir)
        file_index_path = os.path.join(product_path, file_index_name)

        if os.path.isfile(file_index_path):
            with open(file_index_path, 'rb') as handle:
                master_set = pickle.load(handle)
        else:
            print('Building index of existing local files...')
            master_set = set()
            for path, subdirs, files in os.walk(product_path):
                for name in files:
                    master_set.add(os.path.join(path, name))
            with open(file_index_path, 'wb') as handle:
                pickle.dump(master_set, handle, protocol=pickle.HIGHEST_PROTOCOL)

        ## Load in files locally and remotely
        if check_local:
            print('Checking if files exist locally...')
            local_set = path_set.intersection(master_set)
            remote_dict = {url: local for url, local in url_dict.items() if local not in local_set}
        else:
            local_set = set()
            remote_dict = url_dict.copy()

        ds_list = []
        if local_set:
            print('Reading local files...')
            local_list = list(local_set)
            local_list.sort()
            ds = xr.open_mfdataset(local_list, concat_dim='time', parallel=True)
            ds2 = ds[dataset_types].sel(lat=slice(min_lat, max_lat), lon=slice(min_lon, max_lon))
            ds.close()
            ds_list.append(ds2)

        if remote_dict:
            print('Downloading files from NASA...')

            iter1 = [(u, u0, self.session, master_dataset_list, dataset_types, min_lat, max_lat, min_lon, max_lon) for u, u0 in remote_dict.items()]

            output = ThreadPool(dl_sim_count).starmap(download_files, iter1)

            ds_list.extend(output)

        ds_all = xr.concat(ds_list, dim='time').sortby('time')

        ## Update the file index
        master_set.update(set(remote_dict.values()))
        with open(file_index_path, 'wb') as handle:
            pickle.dump(master_set, handle, protocol=pickle.HIGHEST_PROTOCOL)

        return ds_all

