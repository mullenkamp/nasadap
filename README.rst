nasadap - A Python package for downloading NASA data using DAP
=======================================================================

The nasadap package contains a class and associated methods/functions to download NASA satellite data products and convert them to `xarray <http://xarray.pydata.org>`_ datasets. It uses the python package `pydap <https://pydap.readthedocs.io>`_ to access the NASA `Hyrax <https://docs.opendap.org/index.php/Hyrax>`_ OPeNDAP servers.

At the moment, nasadap can only download the satellite precipitation data from the TRMM and GPM missions.

The official list of precipitation products can be found `here <https://pmm.nasa.gov/data-access/downloads/>`_.
The products available via nasadap are described below.

New users must register an account with `Earthdata <https://urs.earthdata.nasa.gov/users/new>`_ to get a username and password to access any NASA data. Then `register <https://disc.gsfc.nasa.gov/earthdata-login>`_ "apps" once logged in. These "apps" are: NASA GESDISC DATA ARCHIVE, GES DISC, and Pydap. More details on general data access can be found on the `Eathdata wiki <https://wiki.earthdata.nasa.gov/display/EL/Earthdata+Login+Knowledge+Base>`_.

Installation
------------
nasadap can be installed via pip or conda::

  pip install nasadap

or::

  conda install -c mullenkamp nasadap

The core dependencies are `xarray <http://xarray.pydata.org>`_, `pydap <https://pydap.readthedocs.io>`_, and `requests <http://docs.python-requests.org/en/master/>`_.

Mission and product descriptions
--------------------------------
Tropical Rainfall Measuring Mission (TRMM)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A full description and documentation of the TRMM can be found on the `NASA TRMM site <https://doi.org/10.5067/TRMM/TMPA/3H/7>`_ [1].
"This dataset is the output from the TMPA (TRMM Multi-satellite Precipitation) Algorithm, and provides precipitation estimates in the TRMM regions that have the (nearly-zero) bias of the ”TRMM Combined Instrument” precipitation estimate and the dense sampling of high-quality microwave data with fill-in using microwave-calibrated infrared estimates. The granule size is 3 hours."

This dataset has two downloadable products: The core 3 hour product (3B42) and the daily aggregate (3B42_Daily). The spatial resolution is  0.25° x 0.25° (~25 km).

The dataset that most people would want is called "precipitation".

.. [1] Tropical Rainfall Measuring Mission (TRMM) (2011), TRMM (TMPA) Rainfall Estimate L3 3 hour 0.25 degree x 0.25 degree V7, Greenbelt, MD, Goddard Earth Sciences Data and Information Services Center (GES DISC), Accessed: 2018-12-28, `10.5067/TRMM/TMPA/3H/7 <https://doi.org/10.5067/TRMM/TMPA/3H/7>`_

Global Precipitation Mission (GPM)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A full description and documentation of the GPM can be found on the `NASA GPM site <https://doi.org/10.5067/GPM/IMERG/3B-HH/05>`_ [2].
"The Integrated Multi-satellitE Retrievals for GPM (IMERG) is the unified U.S. algorithm that provides the Day-1 multi-satellite precipitation product for the U.S. GPM team.

The precipitation estimates from the various precipitation-relevant satellite passive microwave (PMW) sensors comprising the GPM constellation are computed using the 2014 version of the Goddard Profiling Algorithm (GPROF2014), then gridded, intercalibrated to the GPM Combined Instrument product, and combined into half-hourly 10x10 km fields."

This dataset has six downloadable products and are broken up into two sets of three.
The core product set has a temporal resolution of 30 minutes and have three different "runs": Early (3IMERGHHE), Late (3IMERGHHL), and Final (3IMERGHH). Early is 4 hours behind real-time, Late is 12 hours behind real-time, and Late has been rain-gauge calibrated and is several months behind. A more thorough description can be found at the link above.
The second set of products are daily aggregates of the first product set. Early (3IMERGDE), Late (3IMERGDL), and Final (3IMERGDF).
The spatial resolution is  0.1° x 0.1° (~10 km).

The dataset that most people would want is called "precipitationCal".

**NOTE:** According to the `official TRMM docs <https://docserver.gesdisc.eosdis.nasa.gov/public/project/GPM/README.TRMM.pdf>`_ under B-9, NASA will be reprocessing the TRMM data back until 2000 using the GPM IMERG V05 algorithm for consistency across the two mission's products. This will be integrated into nasadap once it's up.

.. [2] George Huffman (2017), GPM IMERG Final Precipitation L3 Half Hourly 0.1 degree x 0.1 degree V05, Greenbelt, MD, Goddard Earth Sciences Data and Information Services Center (GES DISC), Accessed: 2018-12-28, `10.5067/GPM/IMERG/3B-HH/05 <https://doi.org/10.5067/GPM/IMERG/3B-HH/05>`_

Usage Examples
--------------
At the moment, there is a single class called NASA that provides access to the data. It's highly recommended to use a cache directory as NASA's Hyrax server is a bit slow.

.. code-block:: python

  from nasadap import Nasa, min_max_dates

  ###############################
  ### Parameters

  username = '' # Need to change!
  password = '' # Need to change!
  mission1 = 'trmm'
  mission2 = 'gpm'
  from_date = '2018-01-30'
  to_date = '2018-02-02'
  product1 = '3B42_Daily'
  product2 = '3IMERGDF'
  dataset_type1 = 'precipitation'
  dataset_type2 = 'precipitationCal'
  min_lat=-49
  max_lat=-33
  min_lon=165
  max_lon=180
  cache_dir = 'nasa/precip'

  ###############################
  ### Tests

  min_max = min_max_dates(mission1) # Will give you the min and max available dates for products

  ge1 = Nasa(username, password, mission1, cache_dir)
  dataset_types = ge1.get_dataset_types()
  ds1 = ge1.get_data(product1, dataset_type1, from_date, to_date, min_lat, max_lat, min_lon, max_lon)
  ge1.close()

  ge2 = Nasa(username, password, mission2, cache_dir)
  ds2 = ge2.get_data(product2, dataset_type2, from_date, to_date, min_lat, max_lat, min_lon, max_lon)
  ge2.close()
