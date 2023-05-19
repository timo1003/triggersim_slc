###############################################
# Tray Segments for DeepCore L3 Processing
# Adapted from 2012 L3 Scripts to work on newer
# Data.
# A Terliuk
###############################################
import icecube, numpy as np
from icecube import dataclasses
from icecube import icetray
from icecube.icetray import logging, I3Units
from icecube import NoiseEngine
from icecube import linefit
from icecube import static_twc
from icecube.DeepCore_Filter import DOMS
from icecube import tensor_of_inertia
from icecube.STTools.seededRT.configuration_services import I3DOMLinkSeededRTConfigurationService
from icecube.common_variables import hit_statistics
from icecube.filterscripts import filter_globals

#*****************************************************************
# A pythonic version of the LowEnVariables algorithms for use with
# the GRECO Online selection code. Eventually, we want to swap to
# that, but the docs and unit tests will take some time.
#*****************************************************************
def GetHitInformation(geometry,
                      hitmap, 
                      hitMode = 1):
    r"""Function to grab the hit information from the hitmap and return
    it once. This limits the amount of time we need to spend accessing
    the frame, making everything slightly more efficient

    Parameters
    -----------
    geometry : I3Geometry
             Name of the I3Geometry object to grab the x, y, z information 
             for each hit PMT

    hitmap: I3RecoPulseSeriesMap
             Pulse map from which to grab information
    
    hitMode: int
             Integer referring to how to extract information. Enumeration is:
             0: Return information about every individual pulse
             1: Return the first hit time and total charge for every PMT

    Returns
    -------
    x, y, z : np.array<float>
             Time-sorted position of each hit from the pulse map
    
    t : np.array<float>
             Time-sorted list of times for each hit from the pulse map
    
    q : np.array<float>
             Time-sorted list of charges for each hit from the pulse map
    """    
    if hitMode not in [0, 1]:
        logging.log_fatal("hitMode must be set to 0 (pulses) or 1 (modules) for extraction.",
                          "GRECO_online")
        
    # Make a place to store everything
    x, y, z, t, q = [], [] ,[], [], []

    # Start looping over the pulse map
    current = 0
    for pmt, pulses in hitmap.items():
        # Get the hit information
        position = geometry.omgeo[pmt].position
        times, charges = np.array([[pulse.time, pulse.charge] for pulse in pulses]).T

        # What is the current ID? This needs to be based on the hitMode
        if (hitMode == 0): 
            x.extend(np.ones_like(times) * position.x)
            y.extend(np.ones_like(times) * position.y)  
            z.extend(np.ones_like(times) * position.z)
            t.extend(times)
            q.extend(charges)
            continue
        else:
            x.append(position.x)
            y.append(position.y)
            z.append(position.z)
            t.append(min(times))
            q.append(sum(charges))
            

    # Done. Sort the results in time, numpyify, and return
    indicies = np.argsort(t)
    x = np.array(x, dtype=float)[indicies]
    y = np.array(y, dtype=float)[indicies]
    z = np.array(z, dtype=float)[indicies]
    t = np.array(t, dtype=float)[indicies]
    q = np.array(q, dtype=float)[indicies]

    return x, y, z, t, q


#*****************************************************************            
def TimeToSum(t, q, fraction=0.75, useCharge=True):
    r"""Find the amount of time (in ns) to reach fraction percent of the
    total charge of the event. Setting useCharge to False disables the 
    use of charge directly and instead just bases the answer on the number 
    of hits.

    Parameters
    -----------
    t, q : np.array<float>
             A time-sorted list of hit times and charges
    
    fraction: float
             A value between 0 and 1 giving the fraction of the total charge
             to find.
    
    useCharge: bool
             If True, use the fraction of the total charge of the event. If
             False, use the fraction of the total number of hits for the event.

    Returns
    -------
    float:
             The time required to reach fraction percent of the total charge.
    """    
    if len(t) == 0: 
        logging.log_info("No hits given. TimeToSum = -10000.", "GRECO_online")
        return -10000
        
    if (fraction < 0) or (fraction > 1):
        logging.log_fatal("Fraction for TimeToSum must be between [0,1]!", "GRECO_online")
    
    # Handle the charge stuff
    if useCharge: charges = q
    else: charges = np.ones(q.shape, dtype=float)

    # Actual work of the calculation
    above_threshold = ((np.cumsum(charges)/np.sum(charges)) >= fraction)
    return t[above_threshold][0] - t[0]


#*****************************************************************            
def NAboveTrigger(z, t, q, hierarchy, configIDs=[1010, 1011], 
                  tmin=-2000*I3Units.ns, tmax=0*I3Units.ns, 
                  minZ=-200, useCharge=True):
    r"""Find the number of hits in the upper IceCube region just before
    the trigger. These are potentially muon hits.

    Parameters
    -----------
    z,t,q : np.array<float>
             Time-sorted lists of z positions, times, and charges

    hierarchy: I3TriggerHierarchy
             An I3TriggerHierarchy for the event used to find the trigger times
    
    configIDs: list<int>
             A list of trigger configIDs to define the time to search for muon hits
    
    tmin,tmax: float
             Time window relative to the earliest trigger time. Negative values
             indicate a time before the trigger, positive values indicate after.

    minZ: float
             The lowest Z value to use for identifying veto hits

    useCharge: bool
             If True, return the discovered total charge. If False, return the the 
             total number of hits discovered for the event.

    Returns
    -------
    float:
             The number of hits found satisfying the timing and z criteria
    """    
    if len(t) == 0: 
        logging.log_info("No hits given. NAboveTrigger = -10000.", "GRECO_online")
        return -10000
        
    # Find the earliest satisfactory trigger
    trigger_time = np.inf
    for trigger in hierarchy:
        if trigger.key.config_id in configIDs:
            if trigger.time < trigger_time:
                trigger_time = trigger.time

    # Find the hits in the time and z window
    passes = np.ones(len(z), dtype=bool)
    passes &= (t > trigger_time + tmin) 
    passes &= (t < trigger_time + tmax)
    passes &= (z > minZ)

    # Handle the charge stuff
    if useCharge: charges = q
    else: charges = np.ones(q.shape, dtype=float)
    
    return np.sum(charges[passes])



#*****************************************************************            
def ChargeRatio(t, q, tWindow=600*I3Units.ns,
                skip=0, useCharge=True, legacy=False):
    r"""Find the fraction of charge contained in the first tWindow ns of the event

    Parameters
    -----------
    t,q : np.array<float>
             Time-sorted lists of times and charges

    tWindow: float
             Length of the time window to evaluate

    skip: int
             Skip this number of hits. Useful if there are early hits due to noise

    useCharge: bool
             If True, return the fraction of the total charge. If False, return the 
             fraction of the total number of hits.

    Returns
    -------
    float:
             The fraction of the total charge in the window
    """    
    if len(t) == 0: 
        logging.log_info("No hits given. ChargeRatio = -10000.", "GRECO_online")
        return -10000

    if skip > len(t):
        logging.log_warn("Skip set to a value larger than the number of hits. "
                         "ChargeRatio = -1 for this event", "GRECO_online")
        return -1 
   
    if tWindow < 0: 
        logging.log_warn("Negative time window specified, which is meaningless. "
                         "ChargeRatio = 0", "GRECO_online")
        return 0
    
    # Handle the charge stuff
    if useCharge: charges = q
    else: charges = np.ones(q.shape, dtype=float)

    if legacy:
        # Actually want the time of the first hit which fails instead of the last that succeeds
        # if we want to match what was done in the past. This actually means that the tWindow is
        # not what we want, but slightly longer. 
        t0 = t[skip]
        tf = t[t > t0 + tWindow][0] + 1e-5
    else:
        # Actual sane mode where we use tWindow directly.
        t0 = t[skip]
        tf = t0 + tWindow
    
    # Find the hits in the time window
    passes = np.ones(len(t), dtype=bool)
    passes &= (t >= t0)
    passes &= (t < tf)

    return np.sum(charges[passes])/np.sum(charges[skip:])


#*****************************************************************            
def AverageDistance(x, y, z):
    r"""Find the average distance between consecutive hits

    Parameters
    -----------
    x,y,z : np.array<float>
             Time-sorted lists of x, y, and z positions

    Returns
    -------
    float:
             The mean distance between consecutive hits
    """    
    if len(x) < 2: 
        logging.log_info("Less than two hits given. AverageDistance = 0.", "GRECO_online")
        return 0

    squared_dist = np.diff(x)**2
    squared_dist += np.diff(y)**2
    squared_dist += np.diff(z)**2
    distances = np.sqrt(squared_dist)
    
    if len(distances) == 0: return 0
    else: return np.mean(distances)




#*****************************************************************            
def ZTravel(z, q, useCharge=True):
    r"""Find the distance between the first quartile mean z position and average 
    z position of all hits. If too few hits are found, return the distace between 
    the first and mean hit z positions.

    Parameters
    -----------
    z, q : np.array<float>
             Time-sorted lists of z positions and charges

    useCharge: bool
             If True, define the quartiles by charge. If False, the first quartile
             is found by number of hits

    Returns
    -------
    float:
             The distance between the first quartile and average hit z positions
    """    
    if len(z) == 0: 
        logging.log_info("No hits given. ZTravel = -10000.", "GRECO_online")
        return -10000

    # Handle the charge stuff
    if useCharge: charges = q
    else: charges = np.ones(q.shape, dtype=float)


    # Define the first and last quartiles
    charges /= np.sum(charges)
    first_quartile = np.ones(len(z), dtype=bool)
    first_quartile &= np.cumsum(charges) < 0.25

    if np.sum(first_quartile) == 0:
        first_quartile[0] = True

    zavg = np.mean(z)
    z0 = np.mean(z[first_quartile])
    return zavg - z0
    


#*****************************************************************            
def CoGTravel(x, y, z, q, useCharge=True):
    r"""Find the distance between the first quartile and last quartile mean positions.
    If too few hits are found, return the distace between the first and last hit positions.

    Parameters
    -----------
    x, y, z, q : np.array<float>
             Time-sorted lists of x, y, z positions and charges

    useCharge: bool
             If True, define the quartiles by charge. If False, the first quartile
             is found by number of hits

    Returns
    -------
    float:
             The distance between the first and last quartile positions
    """    
    if len(x) == 0: 
        logging.log_info("No hits given. CoGTravel = -10000.", "GRECO_online")
        return -10000

    # Handle the charge stuff
    if useCharge: charges = q
    else: charges = np.ones(q.shape, dtype=float)

    # Define the first and last quartiles
    charges /= np.sum(charges)
    first_quartile = np.ones(len(z), dtype=bool)
    first_quartile &= np.cumsum(charges) < 0.25
    if np.sum(first_quartile) == 0: first_quartile[0] = True

    last_quartile = np.ones(len(z), dtype=bool)
    last_quartile &= np.cumsum(charges) >= 0.75
    if np.sum(last_quartile) == 0: last_quartile[-1] = True

    squared_dist = 0
    squared_dist += (np.mean(x[last_quartile]) - np.mean(x[first_quartile]))**2
    squared_dist += (np.mean(y[last_quartile]) - np.mean(y[first_quartile]))**2
    squared_dist += (np.mean(z[last_quartile]) - np.mean(z[first_quartile]))**2

    return np.sqrt(squared_dist)



    

#*****************************************************************            
def VetoCausalHits(x, y, z, t, q, 
                   hierarchy, configIDs=[1010,1011], useCharge=True):
    r"""Find the number of hits in the upper IceCube region causally connected
    to the triggers. These are potentially muon hits.

    Parameters
    -----------
    x,y,z,t,q : np.array<float>
             Time-sorted lists of positions, times, and charges

    hierarchy: I3TriggerHierarchy
             An I3TriggerHierarchy for the event used to find the trigger times
    
    configIDs: list<int>
             A list of trigger configIDs to define the time to search for muon hits

    useCharge: bool
             If True, return the discovered total charge. If False, return the the 
             total number of hits discovered for the event.

    Returns
    -------
    float:
             The number of hits causally connected to the trigger
    """    
    if len(t) == 0: 
        logging.log_info("No hits given. VetoCausalHits = -10000.", "GRECO_online")
        return -10000

    # Handle the charge stuff
    if useCharge: charges = np.copy(q)
    else: charges = np.ones(q.shape, dtype=float)

    # Perform this calculation for all triggers
    nfound = 0
    for trigger in hierarchy:
        if not trigger.key.config_id in configIDs: continue
        trigger_time = trigger.time
        
        # Find the hit associated with the trigger so we can assign a position
        index = np.argmin(np.abs(t-trigger_time))
        
        # Calculate the distance and time for each hit to this one
        distances = (x - x[index])**2
        distances += (y - y[index])**2
        distances += (z - z[index])**2
        distances = np.sqrt(distances)
        dt = t[index] - t
    
        # Apply the criteria to ID potential veto hits
        passes = np.ones(len(t), dtype=bool)
        passes &= (distances < 750)
        passes &= (dt > -5*distances + 500)
        passes &= (dt < distances/0.3 + 150)
        passes &= (dt > distances/0.3 - 1850)
        
        nfound += np.sum(charges[passes])

    return nfound


#*****************************************************************            
def MeanZ(z, q, useCharge=True):
    r"""Find the charge-weighted average Z position of the hits

    Parameters
    -----------
    z, q : np.array<float>
             Time-sorted lists of z positions and charges

    useCharge: bool
             If True, charge-weight the average Z. If False, find the 
             simple mean Z position.

    Returns
    -------
    float:
             The number of hits causally connected to the trigger
    """    
    if len(z) == 0: 
        logging.log_info("No hits given. MeanZ = -10000.", "GRECO_online")
        return -10000

    
    # Handle the charge stuff
    if useCharge: charges = q
    else: charges = np.ones(q.shape, dtype=float)

    return np.average(z, weights=charges)




#***************************************************************** 
# The LowEn Level3 used in the GRECO Online processing.
#***************************************************************** 
def TestForFilter(frame, 
                  PassedFilterNames = [filter_globals.DeepCoreFilter,],
                  FailedFilterNames = [filter_globals.SlopFilter,
                                       filter_globals.FixedRateFilterName],):    
    if not frame['I3EventHeader'].sub_event_stream == filter_globals.InIceSplitter:
        return False

    triggers = frame[filter_globals.triggerhierarchy]
    passed = False
    for trig in triggers:
        # move filter_global config ID
        if trig.key.config_id in [filter_globals.deepcoreconfigid,]: 
            passed = True
    if not passed: return False

    for key in FailedFilterNames:
        if key in frame.keys():
            if frame[key].value: return False

    for key in PassedFilterNames:
        if key in frame.keys():
            return frame[key].value

    return False

def PassedDCFilter(frame, year):
        if frame.Has(filter_globals.DeepCoreFilter):
            return frame[filter_globals.DeepCoreFilter].value
        return False


@icetray.traysegment
def DeepCoreCuts(tray, name, 
                 splituncleaned='SplitInIcePulses',
                 year='13', 
                 If=lambda frame: True):
    Pulses = name + 'SRTTWSplitInIcePulsesDC'   ### Pulsemap Generated in L2

    # Single definition of the If condition to be used for all modules here
    DC_If = lambda frame: PassedDCFilter(frame, year) & If(frame)

    tray.AddModule(hit_statistics.I3HitStatisticsCalculator, Pulses + "HScalc",
                   PulseSeriesMapName=Pulses, 
                   OutputI3HitStatisticsValuesName=name + Pulses + "HitStatistics",
                   If = DC_If)
    tray.AddModule(hit_statistics.I3HitStatisticsCalculator, name + splituncleaned + "HScalc",
                   PulseSeriesMapName=splituncleaned, 
                   OutputI3HitStatisticsValuesName=name + splituncleaned + "HitStatistics",
                   If = DC_If)


    ### Run charge-independent NoiseEngine
    ### Run NoiseEngine ###
    tray.AddSegment( NoiseEngine.WithCleaners, name + "NoiseEngine",
                     HitSeriesName = splituncleaned,
                     writePulses = True,
                     If = DC_If
                     )

    ### also no charge version as well
    # will reuse the output from previous segment
    tray.AddModule("NoiseEngine",name+"NoiseEngine",
                   HitSeriesName = splituncleaned+"_STW_ClassicRT_" + name + "NoiseEngine",
                   OutputName = name + "NoiseEngineNoCharge_bool",
                   ChargeWeight = False,
                   If= DC_If
    )

    ### Need to generate TWC Pulses // No longer present in L2 ###
    DOMList = DOMS.DOMS("IC86EDC")
    tray.AddModule('I3StaticTWC<I3RecoPulseSeries>', name + '_level3_StaticTWC_DC',
                   InputResponse = splituncleaned,
                   OutputResponse = name + 'TWSplitInIcePulsesDC',
                   TriggerConfigIDs = [1010, 1011],
                   TriggerName = "I3TriggerHierarchy",
                   WindowMinus = 5000,
                   WindowPlus = 4000,
                   If = lambda f: DC_If(f) and not f.Has(name + "TWSplitInIcePulsesDC")
                   )

    tray.AddModule("I3OMSelection<I3RecoPulseSeries>", name + "_level3_GenDCInTWFidPulses",
                    selectInverse  = True,
                    InputResponse  = name + 'TWSplitInIcePulsesDC',
                    OutputResponse = name  + 'TWSplitInIcePulsesDCFid',
		    OutputOMSelection = name + 'Baddies',
                    OmittedKeys    = DOMList.DeepCoreFiducialDOMs,
                    If = lambda f: DC_If(f) and not f.Has(name + "TWSplitInIcePulsesDCFid")
                    )

    # #############################
    # The goal here is to reduce the noise events by looking
    # for events which have tightly time correlated hits in the
    # DC Fiducial volume.
    # #############################
    tray.AddModule("I3OMSelection<I3RecoPulseSeries>", name + "GenDCPulses",
                    selectInverse  = True,
                    InputResponse  = splituncleaned,
                    OutputResponse = name + 'SplitInIcePulsesDCFid',
                    OmittedKeys    = DOMList.DeepCoreFiducialDOMs,
                    If = DC_If
                    )

    tray.AddModule("I3OMSelection<I3RecoPulseSeries>", name + "GenICVetoPulses_0",
                    selectInverse     = False,
                    InputResponse     = splituncleaned,
                    OutputResponse    = name + "SplitInIcePulsesICVeto",
                    OutputOMSelection = name + "BadOM_ICVeto_0",
                    OmittedKeys       = DOMList.DeepCoreFiducialDOMs,
                    If = DC_If
                    )

    tray.AddModule("I3DeepCoreVeto<I3RecoPulse>", name + "deepcore_filter_pulses",
                   InputFiducialHitSeries = name + "SplitInIcePulsesDCFid",
                   InputVetoHitSeries     = name + "SplitInIcePulsesICVeto",
                   DecisionName           = name + "DCFilterPulses",
                   MinHitsToVeto          = 2,
                   VetoHitsName           = name + "DCFilterPulses_VetoHits",
                   If = DC_If
                   )
    
    # #############################
    # Run a dynamic time window cleaning over the
    # StaticTW cleaned recopulses in the DeepCore
    # fiducial region.
    # #############################
    tray.AddModule("I3TimeWindowCleaning<I3RecoPulse>", name + "DynamicTimeWindow300",
                    InputResponse  = name + "TWSplitInIcePulsesDCFid",
                    OutputResponse = name + "DCFidPulses_DTW300",
                    TimeWindow     = 300,
                    If = DC_If
                    )

    # #############################
    # Count the number of hit modules found in the 
    # most populated 300 ns time window of the DC 
    # pulse series map.
    # #############################
    def MicroCount(frame):
      # if If(frame):
        MicroValuesHits = dataclasses.I3MapStringInt()
        if not frame.Has(name + "DCFidPulses_DTW300"):
            frame[name + "MicroCountHits"] = icetray.I3Int(0)
            return
        pulsemap = dataclasses.I3RecoPulseSeriesMap.from_frame(frame, name + "DCFidPulses_DTW300")
        frame[name + "MicroCountHits"] = icetray.I3Int(len(pulsemap))
        return

    # #############################
    # Add the MicroCount object to the frame
    # #############################
    tray.AddModule(MicroCount, name + "MicroCount", 
                   If = DC_If)

    # ##############################
    # Get some of the simple variables
    # ##############################
    def CalculateC2QR6AndFirstHitVertexZ(frame, PulseSeries):
        hits = dataclasses.I3RecoPulseSeriesMap.from_frame(frame, PulseSeries)
        x, y, z, t, q = GetHitInformation(frame['I3Geometry'], hits, 1)
        frame[name + 'C2HR6'] = dataclasses.I3Double(ChargeRatio(t, q, 600, 2, False))
        frame[name + "VertexGuessZ"] = dataclasses.I3Double(z[0])

    tray.AddModule(CalculateC2QR6AndFirstHitVertexZ, name + "CalcC2QR6AndFirstHitVertexZ", 
                    PulseSeries = Pulses, 
                    If = DC_If)
        
    # #############################
    # Actually add the NAbove200 variable
    # to the frame
    # ##############################
    def CalculateNAbove200(frame, PulseSeries):
        hits = dataclasses.I3RecoPulseSeriesMap.from_frame(frame, PulseSeries)
        x, y, z, t, q = GetHitInformation(frame['I3Geometry'], hits, 1)
        frame[name + 'NChAbove200'] = dataclasses.I3Double(NAboveTrigger(z, t, q, 
                                                                                   frame['I3TriggerHierarchy'], [1011],
                                                                                   -2000, 0, 
                                                                                   -200, False))
                                             
    tray.AddModule(CalculateNAbove200, name + "CalcNAbove200",
                    PulseSeries = splituncleaned,
                    If = DC_If
                    )

    # #############################
    # Jacob Daughhetee has shown that a ratio of 
    # SRT cleaned hits within DC to outside of 
    # DC can be a good bkg identifier as well.
    # Run the standard L2 SRT cleaning.
    # #############################
    tray.AddModule("I3OMSelection<I3RecoPulseSeries>", name + "GenDCCFidSRTPulses",
                    selectInverse     = True,
                    InputResponse     = Pulses,
                    OutputResponse    = name + "SRTTWSplitInIcePulsesDCFid",
                    OutputOMSelection = name + "BadOM1",
                    OmittedKeys       = DOMList.DeepCoreFiducialDOMs,
                    If = DC_If
                    )

    tray.AddModule("I3OMSelection<I3RecoPulseSeries>", name + "GenICVetoSRTPulses",
                    selectInverse     = False,
                    InputResponse     = Pulses,
                    OutputResponse    = name + "SRTTWSplitInIcePulsesICVeto",
                    OutputOMSelection = name + "BadOM2",
                    OmittedKeys       = DOMList.DeepCoreFiducialDOMs,
                    If = DC_If
                    )

    # ##############################
    # Suggestion by the WIMP group to
    # look at the RT cluster size of pulses
    # in the IC Veto region
    # ##############################
    classicSeededRTConfigService = I3DOMLinkSeededRTConfigurationService(
        treat_string_36_as_deepcore = False,
        allowSelfCoincidence    = True,
        useDustlayerCorrection  = False,
        dustlayerUpperZBoundary = 0*I3Units.m,
        dustlayerLowerZBoundary = -150*I3Units.m,
        ic_ic_RTTime           = 1000*I3Units.ns,
        ic_ic_RTRadius         = 250*I3Units.m
        )

    tray.AddModule("I3StaticTWC<I3RecoPulseSeries>", name + "TWRTVetoPulses",
                    InputResponse    = splituncleaned,
                    OutputResponse   = name + "TWRTVetoSeries",
                    TriggerConfigIDs = [1011],
                    TriggerName      = "I3TriggerHierarchy",
                    WindowMinus      = 5000,
                    WindowPlus       = 0,
                    If = DC_If
                    )

    tray.AddModule("I3OMSelection<I3RecoPulseSeries>", name + "GenRTVetoPulses",
                    selectInverse     = False,
                    InputResponse     = name + "TWRTVetoSeries",
                    OutputResponse    = name + "TWRTVetoSeries_ICVeto",
                    OutputOMSelection = name + "BadOM3",
                    OmittedKeys       = DOMList.DeepCoreFiducialDOMs,
                    If = DC_If
                    )

    tray.AddModule("I3RTVeto_RecoPulseMask_Module", name + "rtveto",
                   STConfigService         = classicSeededRTConfigService,
                   InputHitSeriesMapName   = name + "TWRTVetoSeries_ICVeto",
                   OutputHitSeriesMapName  = name + "RTVetoSeries250",
                   Streams                 = [icetray.I3Frame.Physics],
                   If = DC_If
                  )

    def CountRTVetoSeriesNChannel(frame):
        totalHits = 0.0
        if frame.Has(name + "RTVetoSeries250"):
            pulsemap = dataclasses.I3RecoPulseSeriesMap.from_frame(frame, name + "RTVetoSeries250")
            totalHits = len(pulsemap)
        frame[name + "RTVetoSeries250Hits"] = dataclasses.I3Double(totalHits)
        return

    tray.AddModule(CountRTVetoSeriesNChannel, name + "CountRTVetoSeries",
                   If = DC_If)

    # ##############################
    # Create a variable that gets pushed
    # to the frame that checks whether
    # the event passed the IC2011 LE L3
    # straight cuts and cleaning.
    # ##############################
    def passIC2012_LE_L3(frame):
        totalHitsFiducial   = len(frame[name + "SRTTWSplitInIcePulsesDCFid"])            
        totalHitsVeto       = len(frame[name + "SRTTWSplitInIcePulsesICVeto"])
        
        LE_L3_Vars = dataclasses.I3MapStringDouble()
        LE_L3_Vars["NoiseEngine"]        = frame[name + "NoiseEngineNoCharge_bool"].value
        LE_L3_Vars["STW9000_DTW300Hits"] = frame[name + "MicroCountHits"].value
        LE_L3_Vars["C2HR6"]              = frame[name + "C2HR6"].value
        LE_L3_Vars["NAbove200Hits"]      = frame[name + "NChAbove200"].value
        LE_L3_Vars["DCFiducialHits"]     = totalHitsFiducial
        LE_L3_Vars["ICVetoHits"]         = totalHitsVeto
            
        if totalHitsFiducial==0:
            # XXX: need to find a bit more elegant solution for this problem
            LE_L3_Vars['VetoFiducialRatioHits']= float("inf")
        else:  
            LE_L3_Vars['VetoFiducialRatioHits']=totalHitsVeto*1.0/totalHitsFiducial

        LE_L3_Vars["CausalVetoHits"]     = frame[name + "DCFilterPulses_VetoHits"].value
        LE_L3_Vars["VertexGuessZ"]       = frame[name + "VertexGuessZ"].value
        LE_L3_Vars["RTVeto250Hits"]      = frame[name + "RTVetoSeries250Hits"].value

        pulsemap = dataclasses.I3RecoPulseSeriesMap.from_frame(frame, name + "SRTTWSplitInIcePulsesDC")
        LE_L3_Vars["NchCleaned"]         = len(pulsemap)
        LE_L3_Vars['CleanedFullTimeLength'] = (frame[name + Pulses + 'HitStatistics'].max_pulse_time - 
                                                frame[name + Pulses + 'HitStatistics'].min_pulse_time)
        LE_L3_Vars['UncleanedFullTimeLength'] = (frame[name + splituncleaned + 'HitStatistics'].max_pulse_time - 
                                                  frame[name + splituncleaned + 'HitStatistics'].min_pulse_time)          
        frame[name + "IC2018_LE_L3_Vars"] = LE_L3_Vars

        # Calculation passing bools for RTVetoCut
        rt_veto_hit_pass     = ((LE_L3_Vars["RTVeto250Hits"] <  4.0 and LE_L3_Vars["DCFiducialHits"] <  75) or \
                                 (LE_L3_Vars["RTVeto250Hits"] <  5.0 and LE_L3_Vars["DCFiducialHits"] >= 75 and LE_L3_Vars["DCFiducialHits"] < 100) or \
                                 (LE_L3_Vars["DCFiducialHits"] >= 100) )
        nch_pass             = (LE_L3_Vars["NchCleaned"]  >= 6)
        LE_L3_Vars["RTVetoCutHit"]      = rt_veto_hit_pass
        
        # Calculating bools for L3 without RTVeto
        L3_hit_bool    = (frame[name + "NoiseEngineNoCharge_bool"].value and 
                          frame[name + "MicroCountHits"].value > 2 and 
                          frame[name + "NChAbove200"].value < 10 and 
                          totalHitsFiducial > 2 and 
                          frame[name + "VertexGuessZ"].value < -120 and 
                          frame[name + "DCFilterPulses_VetoHits"].value < 7.0 and 
                          LE_L3_Vars['VetoFiducialRatioHits'] < 1.5 and 
                          frame[name + "C2HR6"].value > 0.37 and 
                          LE_L3_Vars['UncleanedFullTimeLength'] < 13000.0 and 
                          LE_L3_Vars['CleanedFullTimeLength'] < 5000.0 ) 
        
        ## Storing all the 2018 L3 bools
        LE_L3_2018_bools =  dataclasses.I3MapStringBool()
        LE_L3_2018_bools["IC2018_LE_L3_Full"]             = (L3_hit_bool*rt_veto_hit_pass*nch_pass)
        LE_L3_2018_bools["IC2018_LE_L3_No_Nch"]           = (L3_hit_bool*rt_veto_hit_pass)
        LE_L3_2018_bools["IC2018_LE_L3_No_RTVeto"]        = (L3_hit_bool*nch_pass)
        LE_L3_2018_bools["IC2018_LE_L3_No_Nch_No_RTVeto"] = (L3_hit_bool)
        
        frame['IC2018_LE_L3_bools'] = LE_L3_2018_bools

    tray.AddModule(passIC2012_LE_L3, name + "LE_L3_pass",
                   If = DC_If)

    # ############################################
    # Remove all the bad omselections created when
    # producing the MicroCount outputs as well as
    # other junk from L3 processing
    # ############################################

    tray.AddModule("Delete", "delete_badomselection",
                   Keys = [name + "BadOMSelection",
                           name + "BadOM1",
                           name + "BadOM2",
                           name + "BadOM3",
                           name + "BadOM_DCFid_0",
                           name + "BadOM_ICVeto_0",
                           name + "DCFidPulses_DTW175",
                           name + "DCFidPulses_DTW200",
                           name + "DCFidPulses_DTW250",
                           name + "DCFidPulses_DTW300",
                           name + "SplitInIcePulses_STW_NoiseEnginess",
                           name + "SplitInIcePulses_STW_ClassicRT_NoiseEnginess",
                           name + "SRTTWSplitInIcePulsesICVeto",
                           name + "SRTTWSplitInIcePulsesDCFid",
                           name + "DCFilterPulses_VetoPE",
                           name + "DCFilterPulses_VetoHits",
                           name + "DCFilterPulses",
                           name + "C2QR6",
                           name + "C2HR6",
                           name + "Baddies",
                           name + "RTVetoSeries250",
                           name + "RTVetoSeries250PE",
                           name + "RTVetoSeries250Hits", 
                           name + "TWRTVetoSeriesTimeRange",
                           name + "TWRTVetoSeries_ICVeto",
                           name + "SplitInIcePulsesDCFid",
                           name + "SplitInIcePulsesICVeto",
                           name + "VertexGuessX",
                           name + "VertexGuessY",
                           name + "VertexGuessZ",
                           name + "TWSplitInIcePulsesDCFid",
                           name + "NAbove200",
                           name + "MicroCountPE",
                           name + "MicroCountHits",
                           name + 'SRTTWSplitInIcePulsesICVetoCleanedKeys',
                           name + 'SRTTWSplitInIcePulsesDCFidCleanedKeys',
                           name + 'TWSplitInIcePulsesDCFidCleanedKeys',
                           name + 'TWRTVetoSeries_ICVetoCleanedKeys',
                           name + 'SplitInIcePulsesDCFidCleanedKeys',
                           name + 'SplitInIcePulsesICVetoCleanedKeys',
                           ]
                   )


    return


@icetray.traysegment
def DCL3MasterSegment(tray, name, year='12'):
  #
  tray.AddModule(PassedDCFilter, year=year)
  print("WARNING! Checking the DeepCore L2 filter! Use  \"DeepCoreCuts\" module directly if you want to keep other filters")
  tray.AddSegment(DeepCoreCuts, "L3DeepCoreCuts",splituncleaned='SplitInIcePulses', year=year)

