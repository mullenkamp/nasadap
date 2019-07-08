# -*- coding: utf-8 -*-
"""
Utility functions.
"""
import requests
from re import search, IGNORECASE
import os
import pandas as pd
from xmltodict import parse
from multiprocessing.pool import ThreadPool
from time import sleep
import itertools

###############################################
### Parameters

mission_product_dict = {
        'gpm': {
                'base_url': 'https://gpm1.gesdisc.eosdis.nasa.gov:443',
                'process_level': 'GPM_L3',
                'version': 6,
                'products': {
                        '3IMERGHHE': '{mission}_{product}.{version:02}/{year}/{dayofyear:03}/3B-HHR-E.MS.MRG.3IMERG.{date}-S{time_start}-E{time_end}.{minutes}.V{version:02}B.HDF5',
                        '3IMERGHHL': '{mission}_{product}.{version:02}/{year}/{dayofyear:03}/3B-HHR-L.MS.MRG.3IMERG.{date}-S{time_start}-E{time_end}.{minutes}.V{version:02}B.HDF5',
                        '3IMERGHH': '{mission}_{product}.{version:02}/{year}/{dayofyear:03}/3B-HHR.MS.MRG.3IMERG.{date}-S{time_start}-E{time_end}.{minutes}.V{version:02}B.HDF5'
                            }
                }
        }

master_datasets = {'3IMERGHHE': ['precipitationQualityIndex', 'IRkalmanFilterWeight', 'precipitationCal', 'HQprecipitation', 'probabilityLiquidPrecipitation', 'randomError', 'IRprecipitation'],
                   '3IMERGHHL': ['precipitationQualityIndex', 'IRkalmanFilterWeight', 'precipitationCal', 'HQprecipitation', 'probabilityLiquidPrecipitation', 'randomError', 'IRprecipitation'],
                   '3IMERGHH': ['precipitationQualityIndex', 'IRkalmanFilterWeight', 'precipitationCal', 'HQprecipitation', 'probabilityLiquidPrecipitation', 'randomError', 'IRprecipitation']}



###############################################
### Functions


def parse_dates(date, url):
    """

    """
    counter = 4
    while counter > 0:
        date_xml = requests.get(url + '/catalog.xml')
        if date_xml.status_code == 200:
            break
        else:
            print('Retrying in 3 seconds...')
            counter = counter - 1
            sleep(3)
    date_lst = parse(date_xml.content)['thredds:catalog']['thredds:dataset']['thredds:dataset']
    if not isinstance(date_lst, list):
        date_lst = [date_lst]
    date_lst = [d for d in date_lst if not '.xml' in d['@name']]
    lst1 = [[date, d['@name'].split('-S')[1][:6], d['@name'].split('0-E')[1][:6], d['@name'], d['@ID'], int(d['thredds:dataSize']['#text']), d['thredds:date']['#text']] for d in date_lst]

    return lst1



def parse_nasa_catalog(mission, product, version, from_date=None, to_date=None, min_max=False):
    """
    Function to parse the NASA Hyrax dap server via the catalog xml.

    Parameters
    ----------
    missions : str, list of str, or None
        The missions to parse. None will parse all available.
    products : str, list of str, or None
        The products to parse. None will parse all available.
    version : int
        The product version.
    from_date : str or None
        The start date to query.
    end_date : str or None
        The end date to query.
    min_max : bool
        Should only the min and max dates of the product and version be returned?

    Returns
    -------
    DataFrame
        indexed by mission and product

    Notes
    -----
    I wish their server was faster, but if you try to query too many dates then it might take a while.
    """
    ## mission/product parse
    base_url = mission_product_dict[mission]['base_url']
    mis_url = '/'.join([base_url, 'opendap/hyrax',  mission_product_dict[mission]['process_level']])
    prod_xml = requests.get(mis_url + '/catalog.xml')
    prod_lst = parse(prod_xml.content)['thredds:catalog']['thredds:dataset']['thredds:catalogRef']
    prod1 = [p for p in prod_lst if (product in p['@name']) & (str(version) in p['@name'])]
    if not prod1:
        raise ValueError('No combination of product and version in specified mission')

    ## Parse available years
    years_url = '/'.join([mis_url, prod1[0]['@name']])
    years_xml = requests.get(years_url + '/catalog.xml')
    years_lst = parse(years_xml.content)['thredds:catalog']['thredds:dataset']['thredds:catalogRef']
    if isinstance(years_lst, list):
        years_dict = {int(y['@name']): y for y in years_lst}
    else:
        years_dict = {int(years_lst['@name']): years_lst}

    ## Parse available months/days of the year
    big_lst = []
    for y in years_dict:
        my_url = '/'.join([years_url, str(y)])
        my_xml = requests.get(my_url + '/catalog.xml')
        my_lst = parse(my_xml.content)['thredds:catalog']['thredds:dataset']['thredds:catalogRef']
        if not isinstance(my_lst, list):
            my_lst = [my_lst]
        big_lst.extend([[y, int(d['@name']), base_url + d['@ID']] for d in my_lst])

    my_df = pd.DataFrame(big_lst, columns=['year', 'dayofyear', 'url'])
    my_df['date'] = pd.to_datetime(my_df.year.astype(str)) + pd.to_timedelta(my_df.dayofyear - 1, unit='D')
    my_df.drop(['year', 'dayofyear'], axis=1, inplace=True)

    ## Get all requested dates
    if isinstance(from_date, str):
        my_df = my_df[(my_df.date >= from_date)]

    if isinstance(to_date, str):
        my_df = my_df[(my_df.date <= to_date)]

    if min_max:
        my_df = my_df.iloc[[0, -1]]

    iter1 = [(row.date, row.url) for index, row in my_df.iterrows()]
    big_lst = ThreadPool(30).starmap(parse_dates, iter1)
    big_lst2 = list(itertools.chain.from_iterable(big_lst))

    date_df = pd.DataFrame(big_lst2, columns=['date', 'start_time', 'end_time', 'file_name', 'file_url', 'file_size', 'modified_date'])
    date_df['modified_date'] = pd.to_datetime(date_df['modified_date'] + '+00')
    date_df['start_time'] = pd.to_datetime(date_df['start_time'], format='%H%M%S', errors='coerce').dt.time.astype(str) + 'Z+00'
    date_df['end_time'] = pd.to_datetime(date_df['end_time'], format='%H%M%S', errors='coerce').dt.time.astype(str) + 'Z+00'
    date_df['from_date'] = pd.to_datetime(date_df['date'].astype(str) + 'T' +  date_df['start_time'])
    date_df['to_date'] = pd.to_datetime(date_df['date'].astype(str) + 'T' +  date_df['end_time'])
    date_df.drop(['date', 'start_time', 'end_time'], axis=1, inplace=True)

    ## Add in extra columns and return
    date_df['mission'] = mission
    date_df['product'] = product
    date_df['version'] = version

    return date_df


def rd_dir(data_dir, ext):
    """
    Function to read a directory of files and create a list of files associated with a spcific file extension. Can also create a list of file numbers from within the file list (e.g. if each file is a station number.)
    """

    files = [filename for filename in os.listdir(data_dir) if search('.' + ext + '$', filename, IGNORECASE)]

    return files




















