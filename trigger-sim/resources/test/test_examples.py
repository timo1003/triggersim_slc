#!/usr/bin/env python3

import unittest
import os
from os.path import expandvars
from icecube.icetray import I3Test

class TestSimpleExample(I3Test.TestExampleScripts):

    project_name = "trigger-sim"
    
    def test_change_trigger_settings(self):
        self.run_example('change_trigger_settings.py')

    def test_time_shift_events(self):
        self.run_example('time_shift_events.py')
        
    def test_add_slop_params_to_gcd(self):

        fn = expandvars("$I3_TESTDATA/GCD/GeoCalibDetectorStatus_2013.56429_V1.i3.gz")
        self.run_example('add_slop_params_to_gcd.py',
                            '--gcd', fn,
                            '--output', './new_slop_GCD.i3.gz',
                            '--dc_algo', '1',
                            '--alpha_min', '0.5',
                            '--delta_d', '1.0',
                            '--domSet', '2',
                            '--min_n_tuples', '2',
                            '--rel_v', '1',
                            '--t_proximity', '1',
                            '--t_min', '1',
                            '--t_max', '10',
                            '--max_event_length', '4'
                            )

    def tearDown(self):
        for fname in "newGCD.i3.gz", "new_slop_GCD.i3.gz":
            if os.path.exists(fname):
                os.remove(fname)

unittest.main()
