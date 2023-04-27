Retriggering
~~~~~~~~~~~~
If you want to retrigger data or simulation, with an existing algorithm but slightly different
settings, you'll need to first generate a new GCD file.  Rationale: It's become standard practice
to bundle the GCD file with the data.  If users were allowed to retrigger data at runtime via a
script it's possible, and likely, that the data would contain an inconsistent GCD file (the
pre-retriggered file) and the link to the script that retriggered it would get lost over time.

Step 1 - Finding the Trigger Config ID
--------------------------------------
It might be helpful to first print the settings of your input GCD file.

.. code:: bash
	  
	  $ $I3_BUILD/trigger-sim/resources/scripts/print_trigger_configuration.py
	  TriggerKey : [IN_ICE:SIMPLE_MULTIPLICITY:1006]
            SimpleMajorityTrigger
              threshold = 8
              timeWindow = 5000
          TriggerKey : [IN_ICE:SIMPLE_MULTIPLICITY:1011]
            SimpleMajorityTrigger
              domSet = 6
              threshold = 3
              timeWindow = 2500
          TriggerKey : [IN_ICE:SLOW_PARTICLE:24002]
            SlowMPTrigger
              alpha_min = 140
              dc_algo = false
              max_event_length = 5000000
              min_n_tuples = 5
              rel_v = 0.5
              t_max = 500000
              t_min = 0
              t_proximity = 2500
          TriggerKey : [IN_ICE:STRING:1007]
            ClusterTrigger
              coherenceLength = 7
              domSet = 2
              multiplicity = 5
              timeWindow = 1500
          TriggerKey : [IN_ICE:VOLUME:21001]
            CylinderTrigger
              domSet = 2
              height = 75
              multiplicity = 4
              radius = 175
              simpleMultiplicity = 8
              timeWindow = 1000
          TriggerKey : [ICE_TOP:SIMPLE_MULTIPLICITY:102]
            SimpleMajorityTrigger
              threshold = 6
              timeWindow = 5000

The trigger config_id is the last number in the TriggerKey. e.g.
"TriggerKey : [IN_ICE:SIMPLE_MULTIPLICITY:1006]" for SMT8, the config_id is 1006.
Since it uniquely defines a TriggerKey there's no need to specify anymore than that.

Now that you have the config_id for the trigger you want to modify, you can pass that
to the 'generate_retriggered_GCD.py' script along with the key, value that corresponds
to the trigger setting you want to change.

Step 2 - Generating a retrigger GCD file
----------------------------------------

The following example sets the 'threshold' value to '12' for the trigger with config_id
1006 (SMT8 in this case).

.. code:: bash

	  $I3_BUILD/trigger-sim/resources/scripts/generate_retriggered_GCD.py --input-GCD=$I3_TESTDATA/GCD/GeoCalibDetectorStatus_2012.56063_V0.i3.gz --output-GCD=./GeoCalibDetectorStatus_2012.56063_V0_SMT12.i3.gz --trigger-config-id=1006 --key=threshold --value=12

Step 3 - Retriggering
---------------------

This is accomplished how one would expect using the ReTrigger segment in
simprod-scripts, passing the new GCD as a parameter.
