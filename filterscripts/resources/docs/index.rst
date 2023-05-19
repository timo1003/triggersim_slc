.. _filterscripts:

=============
filterscripts
=============

* Maintainer: Erik Blaufuss (blaufuss @ umd.edu)

.. toctree::
   :maxdepth: 3

   release_notes


Overview
--------

This is the level 1 (L1) and level 2 (L2) processing project.

L1 : Pole processing
  Any processing that occurs at pole to select the events to be sent north.

L2 : North processing
  Any global (standard) processing that gets run on all data before being
  released to analyzers.
  
For simulation, L1 and L2 are run back-to-back to mimic normal data,
with a few changes to remove compression and space saving.


Usage
-----

Users wanting to do their own L2 processing should use the following
directions:

.. toctree::
   :maxdepth: 2
   
   ic86_2015
   ic86_2014
   ic86_2013
   ic86_2012
   ic86_2011


TFT Planning
------------

The `Trigger Filter Transmission Board 
<https://wiki.icecube.wisc.edu/index.php/Trigger_Filter_Transmission_Board>`_
is in charge of changes to the detector as an interface between
analysis groups and operations. Changes to triggers or filters
go through annual review.

See the wiki pages:

| 2018 : https://drive.google.com/open?id=1a5LRRn8faCpTF0DVJtqk0XvQlQ-oF7ka
| 2016 : http://wiki.icecube.wisc.edu/index.php/TFT_2016_Season_Planning
| 2015 : http://wiki.icecube.wisc.edu/index.php/TFT_2015_Season_Planning
| 2014 : http://wiki.icecube.wisc.edu/index.php/TFT_2014_Season_Planning
| 2013 : http://wiki.icecube.wisc.edu/index.php/TFT_2013_Season_Planning
| 2012 : http://wiki.icecube.wisc.edu/index.php/TFT_2012_Season_Planning
| 2011 : http://wiki.icecube.wisc.edu/index.php/TFT_2011_Season_Planning

C++ Documentation
-----------------

`Generated doxygen for this project <../../doxygen/filterscripts/index.html>`_

