.. _trigger-sim:

trigger-sim
===========

**Maintainer:** Alex Olivas

.. toctree::
   :titlesonly:

   release_notes

.. toctree::
   :maxdepth: 3

   trigger_sim_segment
   trigger_config_ids
   slow_trigger_monopole
   global_trigger_sim
   pruner
   time_shifter
   retrigger
   
Overview
~~~~~~~~
This project contains several trigger modules and corresponding utilities.

The Modules
~~~~~~~~~~~

* :cpp:class:`SimpleMajorityTrigger` - Simple majority trigger for InIce and
  IceTop. The simple majority trigger only passes events that contains a certain
  number of DOMLaunches ("threshold") within a given time window ("timeWindow").
  This module works both on InIce and IceTop DOM launches.
* :cpp:class:`ClusterTrigger` - This trigger emulates the string trigger in
  IceCube.
* :cpp:class:`CylinderTrigger` - This trigger emulates the cylinder trigger in
  IceCube.
* :cpp:class:`SlowMonopoleTrigger` - Slow monopole trigger.
* :cpp:class:`I3GlobalTriggerSim` - Collects the various trigger hierarchies and
  builds a global trigger.
* :cpp:class:`I3Pruner` - Cleans IceCube DOMs outside of the readout window.
* :py:class:`I3TimeShifter` - Shifts the times of all known elements in the
  frame with respect to the the event time.

Note: The CylinderTrigger now has the ability to accept both I3DOMLaunches (from IC86) and I3RecoPulses (from the IceCube Upgrade or Gen2).

Utility Classes
~~~~~~~~~~~~~~~

* :cpp:class:`ReadoutWindowUtil`

:cpp:any:`DOMSetFunctions`

.. cpp:namespace:: DOMSetFunctions

* :cpp:func:`InDOMSet`
* :cpp:func:`GetDefaultDOMSets`

:cpp:any:`GTSUtils`

.. cpp:namespace:: GTSUtils

* :cpp:func:`LessThan`
* :cpp:func:`KeyToSubDetector`
* :cpp:func:`TriggerPrettyPrint`
* :cpp:func:`DumpChildren`
* :cpp:func:`Stringize`

:cpp:any:`TimeShifterUtils`

.. cpp:namespace:: TimeShifterUtils

* :cpp:func:`ShiftFrameObjects`


Algorithms
~~~~~~~~~~

* :cpp:class:`TriggerHit`
* :cpp:class:`TimeWindow`
* :cpp:class:`ClusterTriggerAlgorithm`
* :cpp:class:`CylinderTriggerAlgorithm`
