nasaprecip - A Python package for downloading NASA precip missions data
=======================================================================

The nasaprecip package contains a class and associated methods/functions to download satellite precipitation data from the TRMM and GPM missions and convert them to `xarray <http://xarray.pydata.org>`_ datasets. It uses the python package `pydap <https://pydap.readthedocs.io>`_ to access the OPeNDAP servers with the precipitation data.

At the moment, only the "Final" daily data for both missions are possible to download via the nasaprecip package. I might consider adding in the others (i.e. early/late, subdaily) when properly motivated.

New users must register an account `here <https://urs.earthdata.nasa.gov/users/new>`_ to get a username and password to access the data via nasaprecip.

.. Documentation
.. --------------
.. The primary documentation for the package can be found `here <http://hydrointerp.readthedocs.io>`_.

Installation
------------
nasaprecip can be installed via pip or conda::

  pip install nasaprecip

or::

  conda install -c mullenkamp nasaprecip

The core dependencies are `xarray <http://xarray.pydata.org>`_ and `pydap <https://pydap.readthedocs.io>`_.

Usage Examples
--------------
At the moment, there is a single class called Nasa that provides access to the data.

.. code-block:: python

  from nasaprecip import Nasa

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

  ###############################
  ### Tests

  ge1 = Nasa(username, password, mission1)
  ds1 = ge1.get_data(dataset_type1, from_date, to_date, min_lat, max_lat, min_lon, max_lon)
  ge1.close()

  assert ds1[dataset_type1].shape == (3, 52, 56)

  ge2 = Nasa(username, password, mission2)
  ds2 = ge2.get_data(dataset_type2, from_date, to_date, min_lat, max_lat, min_lon, max_lon)
  ge2.close()

  assert ds2[dataset_type2].shape == (3, 130, 140)
