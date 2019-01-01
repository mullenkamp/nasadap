# -*- coding: utf-8 -*-
"""
Created on Wed Jan  2 08:58:12 2019

@author: MichaelEK
"""
import os
import numpy as np
import pandas as pd
import xarray as xr
from nasadap import Nasa, min_max_dates


###################################################
### Parameters

sp_file_name = '{mission}_{product}_v{version:02}'
file_name = '{mission}_{product}_v{version:02}_{from_date}-{to_date}.nc4'

####################################################
### Aggregate files


def year_combine(param_dict, save_dir, username, password, cache_dir, tz_hour_gmt, min_lat, max_lat, min_lon, max_lon, dl_sim_count):
    """
    Function to aggregate the data from the cache to yearly netcdf files and update the cache if new data has been added to the NASA server.

    Parameters
    ----------
    param_dict : dict
        A dict of {mission: {product: dataset}}
    save_dir : str
        The path to where the yearly files should be saved.
    username : str
        The username for the login.
    password : str
        The password for the login.
    cach_dir : str or None
        A path to cache the netcdf files for future reading. If None, the currently working directory is used.
    tz_hour_gmt : int
        The timezone hour from GMT. e.g. GMT+12 would simply be 12.
    min_lat : int, float, or None
        The minimum lat to extract in WGS84 decimal degrees.
    max_lat : int, float, or None
        The maximum lat to extract in WGS84 decimal degrees.
    min_lon : int, float, or None
        The minimum lon to extract in WGS84 decimal degrees.
    max_lon : int, float, or None
        The maximum lon to extract in WGS84 decimal degrees.
    dl_sim_count : int
        The number of simultaneous downloads on a single thread. Speed could be increase with more simultaneous downloads, but up to a limit of the PC's single thread speed.

    Returns
    -------
    None
    """
    time_dict = {'long_name': 'time', 'tz': 'GMT{}'.format(tz_hour_gmt)}

    for m in param_dict:
        print(m)
        ge = Nasa(username, password, m, cache_dir)
        products = param_dict[m]
        for p in products:
            print(p)
            sp_file_name1 = sp_file_name.format(mission=m, product=p, version=7)
            product_path = os.path.join(save_dir, m + '_' + p)
            if not os.path.exists(product_path):
                os.makedirs(product_path)
            files1 = [os.path.join(product_path, f) for f in os.listdir(product_path) if sp_file_name1 in f]
            print('*Reading existing files...')
            if files1:
                ds1 = xr.open_dataset(files1[-1])
                time0 = ds1.time.to_index() - pd.DateOffset(hours=tz_hour_gmt)
                max_date = str(time0.floor('D').max().date())
                max_test_date = ds1.time.max().values
            else:
                ds1 = xr.Dataset()
                min_max = min_max_dates(m, p)
                max_date = str(min_max['start_date'].iloc[0].date())
                max_test_date = np.nan
            print('*Reading new files...')
            ds2 = ge.get_data(p, products[p], from_date=max_date, min_lat=min_lat, max_lat=max_lat, min_lon=min_lon, max_lon=max_lon, dl_sim_count=dl_sim_count)
            ds2['time'] = ds2.time.to_index() + pd.DateOffset(hours=tz_hour_gmt)
            ds2['time'].attrs = time_dict
            if not max_test_date == ds2.time.max().values:
                print('*New data will be added')
                ds3 = ds2.combine_first(ds1)
                ds1.close()
                attr_dict = {key: value for key, value in ds3.attrs.items() if key in ['title']}
                if not 'title' in attr_dict:
                    attr_dict['title'] = ' '.join([m, p])
                attr_dict.update({'ProductionTime': pd.Timestamp.now().isoformat(), 'institution': 'Environment Canterbury', 'source': 'Aggregated from NASA data'})
                ds3.attrs = attr_dict
                all_years = ds3.time.dt.year
                new_years = np.unique(ds2.time.dt.year.values)
                print('*Saving new data...')
                for y in new_years:
                    year_index = all_years == y
                    new_ds1 = ds3.sel(time=year_index)
                    new_dates = new_ds1.time.to_index().strftime('%Y%m%d')
                    new_file_name = file_name.format(mission=m, product=p, version=7, from_date=min(new_dates), to_date=max(new_dates))
                    new_file_path = os.path.join(product_path, new_file_name)
                    new_ds1.to_netcdf(new_file_path)
            else:
                print('*No data to be updated')