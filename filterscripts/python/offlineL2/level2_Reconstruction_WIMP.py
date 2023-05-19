#!/usr/bin/env python3

###
# A Traysegement that does the IC86:2012 Level2 Processing specific for the WimpGroup 
# Please e-mail Meike de With (meike.de.with@desy.de) if you have any questions about this tray segment
###

from icecube import icetray, dataclasses
from I3Tray import I3Units
from icecube.filterscripts.offlineL2 import Globals
from icecube.filterscripts.offlineL2.Globals import wimp_wg
from icecube.phys_services.which_split import which_split
######################## MAIN ################################
@icetray.traysegment #This should be the main routine 
def WimpReco(tray, name,
  If=lambda f: True,
  suffix = '_WIMP'): 
  
  #tray.AddSegment(BasicFits, name+"_BasicFits",
  #  If = If,
  #  suffix = suffix,
  #  Pulses = 'TWSRTOfflinePulses'+suffix )

  tray.AddSegment(FiniteReco, name+"_FiniteReco",
    If = If,
    suffix = '',
    Pulses = 'RTTWOfflinePulses_FR' + suffix) 
    
  tray.AddModule("Delete","WIMP_Cleanup",
    keys=['LineFit'+suffix+'_debiasedPulses', 'LineFit'+suffix+'_linefit_final_rusage', name+"_FiniteReco_VertexReco_rusage", name+"_FiniteReco_FiniteRecoLlh_rusage"])

  #TopologicalSplitter in count-split mode
  icetray.load("TopologicalSplitter")
  tray.AddModule("ttrigger<I3RecoPulse>", name+"TopoSplit",
    InputName      =  "SRTInIcePulses", #should be SRT-cleanedOffline
    OutputName     =  "SRTInIcePulses_TS", #do not forget to delete these later
    Multiplicity   =  4, #Default=4 //Solarwimp-IC79 setting
    TimeWindow     =  4000, #Default=4000 ns
    XYDist         =  300, #Default=500 m //Solarwimp-IC79 setting
    ZDomDist       =  15, #Default=30 //Solarwimp-IC79 setting
    TimeCone       =  1000, #Default=1000 ns
    SaveSplitCount =  True,
    If             =  which_split(split_name='InIceSplit') & (lambda f: wimp_wg(f)))

  tray.AddModule("Delete","WIMP_SplitPulse_Cleanup",
    keys=['SRTInIcePulses_TS0', 'SRTInIcePulses_TS1', 'SRTInIcePulses_TS2', 'SRTInIcePulses_TS3', 'SRTInIcePulses_TS4', 'SRTInIcePulses_TS5', 'SRTInIcePulses_TS6', 'SRTInIcePulses_TS7'])


########################### BASIC FITS DEF ############################

@icetray.traysegment
def BasicFits(tray, name,
  If = lambda f: True,
  suffix = '_WIMP',
  Pulses = ''):
    
    from icecube import linefit, lilliput     
    import icecube.lilliput.segments

    tray.AddSegment( linefit.simple,'LineFit'+suffix,
      inputResponse = Pulses,
      fitName = 'LineFit'+suffix,
      If = If)
  
    #single iteration fit
    tray.AddSegment( lilliput.segments.I3SinglePandelFitter, 'SPEFitSingle'+suffix,
      fitname = 'SPEFitSingle'+suffix,
      pulses = Pulses,
      seeds = ['LineFit'+suffix],
      If = If)
    
    #a 2 iteration fit
    tray.AddSegment( lilliput.segments.I3IterativePandelFitter, 'SPEFit2'+suffix,
      fitname = 'SPEFit2'+suffix,
      pulses = Pulses,
      n_iterations = 2,
      seeds = ['SPEFitSingle'+suffix],
      If = If)                     

  
########################### FINITE RECO DEF ###########################  
@icetray.traysegment #NOTE coppied from std-processing 2011
def FiniteReco(tray, name,
  If = lambda f: True,
  suffix = '',
  Pulses = '',
  PhotonicsServiceName = Globals.PhotonicsServiceFiniteReco,
  InputTrackName = 'SPEFit2',
  FiniteRecoFit = 'FiniteRecoFit',
  FiniteRecoLlh = 'FiniteRecoLlh',
  FiniteRecoCuts = 'FiniteRecoCuts'):
   

    # strings installed in the detector     nk: moved from wg globals
    ic86 = [ 21, 29, 39, 38, 30, 40, 50, 59, 49, 58, 67, 66, 74, 73, 65, 72, 78, 48, 57, 47,
      46, 56, 63, 64, 55, 71, 70, 76, 77, 75, 69, 60, 68, 61, 62, 52, 44, 53, 54, 45,
      18, 27, 36, 28, 19, 20, 13, 12, 6, 5, 11, 4, 10, 3, 2, 83, 37, 26, 17, 8, 9, 16,
      25, 85, 84, 82, 81, 86, 35, 34, 24, 15, 23, 33, 43, 32, 42, 41, 51,
      31, 22, 14, 7, 1, 79, 80] # Taken from http://wiki.icecube.wisc.edu/index.php/Deployment_order

 
    icetray.load('finiteReco', False)
    tray.AddService('I3GulliverFinitePhPnhFactory', name + 'PhPnh' + suffix,
        InputReadout = Pulses,
        PhotorecName = PhotonicsServiceName,
        ProbName = 'PhPnhPhotorec', # Use photorec tables to calculate probabilities
        RCylinder = 200, # Radius around the track in which probabilities are considered
        SelectStrings = ic86,)

    #first guess to start-stop points
    tray.AddModule('I3StartStopPoint', name + '_VertexReco' + suffix,
        Name = InputTrackName + suffix, 
        InputRecoPulses = Pulses,
        ExpectedShape = 70, # Contained track, this way the start AND stop point are reconstructed
        CylinderRadius = 200, # Cylinder radius for the cut calculation,  take care to use Cylinder Radius ==200
        If = If,)

    #starting/stopping probability
    tray.AddModule('I3StartStopLProb', name + '_FiniteRecoLlh' + suffix,
        Name = InputTrackName + suffix + '_Finite', # Name of the input track with _Finite added from I3StartStopPoint
        ServiceName = name + 'PhPnh' + suffix, # Name of the service is the instance name from I3GulliverFinitePhPnhFactory
        If = If,)

    # rename the finiteReco track 
    tray.AddModule('Rename', name + '_FiniteRecoRename' + suffix,
        Keys = [InputTrackName + suffix + '_Finite', 'FiniteRecoFit' + suffix],)

    # rename the finitRecoLlh
    tray.AddModule('Rename', name + '_FiniteRecoLlhRename' + suffix,
        Keys = [name + '_FiniteRecoLlh' + suffix + '_StartStopParams', 'FiniteRecoLlh' + suffix],)  # Name is instance name of I3StartStopLProb with _StartStopParams added

    # rename the finiteReco cuts
    tray.AddModule('Rename', name + '_FiniteRecoCutsRename' + suffix,
        Keys = [InputTrackName + suffix + '_FiniteCuts', 'FiniteRecoCuts' + suffix],) # Name of the input track with _FiniteCuts added from I3StartStopPoint
        
