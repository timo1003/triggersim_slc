##
##  Examples for running the 2013 online base processing and example filter
##

### For data:

./IceCube_BaseProc.py -g ./GCD_Run00121585_Subrun00000000.i3.gz -i ./PFRaw_PhysicsTrig_PhysicsFiltering_Run00121585_Subrun00000000_00000000.i3.gz -o test.i3 --qify -d --disable-vemcal --disable-ofu

## Note:  -d flag-> decode I3DAQData
##        --qify -> translate P frames in input file to Q frames (PFRaw files need this)
##        --disable-vemcal and --disable-ofu -> IceRec does not have the necessary projects to run these

### For simulation sets (already triggered but unfiltered)

#Herem using data from benchmark set 9993, where 1/100th of the files are saved 
#    at "trigger level". Other corsika/NuMu processing should be similar

./IceCube_BaseProc.py -g ./GeoCalibDetectorStatus_2013.56429_icesim3.i3.gz -i IC86.2013_corsika.009993.000000.i3 -o test_sim.i3 --simdata --disable-vemcal and --disable-ofu
