nasaprecip - A Python package for downloading NASA precip missions data
=======================================================================

The nasaprecip package contains a class and associated methods/functions to download precipitation data from the TRMM and GPM missions and convert them to `xarray <http://xarray.pydata.org>`_ datasets. It uses the python package `pydap <https://pydap.readthedocs.io>`_ to access the OPeNDAP servers with the precipitation data.

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
