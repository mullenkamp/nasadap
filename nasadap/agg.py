# -*- coding: utf-8 -*-
"""
Aggregation functions♀
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


def time_combine(mission, product, datasets, save_dir, username, password, cache_dir, tz_hour_gmt, freq, min_lat, max_lat, min_lon, max_lon, dl_sim_count):
    """
    Function to aggregate the data from the cache to netcdf files and update the cache if new data has been added to the NASA server.

    Parameters
    ----------
    mission : str
        Mission name.
    product : str
        The product associated with the mission.
    datasets : str or list of str
        The dataset(s) to be aggregated.
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
    freq : str
        Pandas str frequency indicator for the time periods. e.g. 'M' is month and 'A' is annual.
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

    if isinstance(datasets, str):
        datasets = [datasets]

    ge = Nasa(username, password, mission, cache_dir)
    sp_file_name1 = sp_file_name.format(mission=mission, product=product, version=7)
    product_path = os.path.join(save_dir, mission + '_' + product)
    if not os.path.exists(product_path):
        os.makedirs(product_path)
    files1 = [os.path.join(product_path, f) for f in os.listdir(product_path) if sp_file_name1 in f]
    print('*Reading existing files...')
    min_max = min_max_dates(mission, product)
    end_date = str(min_max['end_date'].iloc[0].date())
    if files1:
        latest_file = files1[-1]
        ds1 = xr.open_dataset(latest_file)
        time0 = ds1.time.to_index()
        start_date = str(time0.max().date())
        max_test_date = ds1.time.max().values
    else:
        start_date = str(min_max['start_date'].iloc[0].date())
        max_test_date = np.datetime64('1900-01-01')
        latest_file = None
        ds1 = None
    print('*Reading new files...')
    end_dates = pd.date_range(start_date, end_date, freq=freq)
    if not end_date in end_dates:
        end_dates = end_dates.append(pd.to_datetime([end_date]))
    start_dates1 = end_dates.values.astype('datetime64[M]').astype('datetime64[ns]').copy()
    start_dates1[0] = start_date
    start_dates = pd.to_datetime(start_dates1)
    dates = list(zip(start_dates, end_dates))
    for s, e in dates:
        print(str(s.date()), str(e.date()))
        s1 = str((s - pd.DateOffset(hours=tz_hour_gmt)).date())
        e1 =  str((e + pd.DateOffset(hours=tz_hour_gmt)).date())
        ds2 = ge.get_data(product, datasets, from_date=s1, to_date=e1, min_lat=min_lat, max_lat=max_lat, min_lon=min_lon, max_lon=max_lon, dl_sim_count=dl_sim_count).load()
        ds2['time'] = ds2.time.to_index() + pd.DateOffset(hours=tz_hour_gmt)
        ds2['time'].attrs = time_dict
        if not max_test_date == ds2.time.max().values:
            print('*New data will be added')
            if isinstance(ds1, xr.Dataset):
                ds2 = ds2.combine_first(ds1).sortby('time')
                ds1.close()
                ds1 = None
                s = pd.Timestamp(ds2.time.min().data).floor('D')
            attr_dict = {key: value for key, value in ds2.attrs.items() if key in ['title']}
            if not 'title' in attr_dict:
                attr_dict['title'] = ' '.join([mission, product])
            attr_dict.update({'ProductionTime': pd.Timestamp.now().isoformat(), 'institution': 'Environment Canterbury', 'source': 'Aggregated from NASA data'})
            ds2.attrs = attr_dict
            print('*Saving new data...')
            ds2 = ds2.sel(time=slice(s, str(e.date())))
            new_dates = ds2.time.to_index().strftime('%Y%m%d')
            new_file_name = file_name.format(mission=mission, product=product, version=7, from_date=min(new_dates), to_date=max(new_dates))
            new_file_path = os.path.join(product_path, new_file_name)
            ds2.to_netcdf(new_file_path)
        else:
            new_file_path = None
    if isinstance(latest_file, str) & isinstance(new_file_path, str):
        if os.path.split(latest_file)[1] != os.path.split(new_file_path)[1]:
            print('*Removing old file')
            os.remove(latest_file)
        else:
            print('*No data to be updated')