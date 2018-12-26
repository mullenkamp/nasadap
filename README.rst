nasadap - A Python package for downloading NASA data using DAP
=======================================================================

The nasadap package contains a class and associated methods/functions to download satellite data and convert them to `xarray <http://xarray.pydata.org>`_ datasets. It uses the python package `pydap <https://pydap.readthedocs.io>`_ to access the NASA `Hyrax <https://docs.opendap.org/index.php/Hyrax>`_ OPeNDAP servers.

At the moment, nasadap can only download the satellite precipitation data from the TRMM and GPM missions.

Only the "Final" daily data for both missions are possible to download via the nasadap package. I will add in the others (i.e. early/late, subdaily) when I get the time. The official list of precipitation products can be found `here <https://pmm.nasa.gov/data-access/downloads/>`_.

New users must register an account `here <https://urs.earthdata.nasa.gov/users/new>`_ to get a username and password to access the data via nasadap.

Installation
------------
nasadap can be installed via pip or conda::

  pip install nasadap

or::

  conda install -c mullenkamp nasadap

The core dependencies are `xarray <http://xarray.pydata.org>`_, `pydap <https://pydap.readthedocs.io>`_, `requests <http://docs.python-requests.org/en/master/>`_, and `beautifulsoup4 <https://www.crummy.com/software/BeautifulSoup/bs4/doc/>`_.

Usage Examples
--------------
At the moment, there is a single class called Nasa that provides access to the data.

.. code-block:: python

  from nasadap import Nasa

  ###############################
  ### Parameters

  username = '' # Need to change!
  password = '' # Need to change!
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
  cache_dir = 'nasa/precip'

  ###############################
  ### Tests

  ge1 = Nasa(username, password, mission1, cache_dir)
  dataset_types = ge1.get_dataset_types()
  ds1 = ge1.get_data(dataset_type1, from_date, to_date, min_lat, max_lat, min_lon, max_lon)
  ge1.close()

  assert ds1[dataset_type1].shape == (3, 52, 56)

  ge2 = Nasa(username, password, mission2, cache_dir)
  ds2 = ge2.get_data(dataset_type2, from_date, to_date, min_lat, max_lat, min_lon, max_lon)
  ge2.close()

  assert ds2[dataset_type2].shape == (3, 130, 140)
