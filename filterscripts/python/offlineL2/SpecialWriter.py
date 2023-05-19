#!/usr/bin/env python3
### special output files ###

from functools import partial

from I3Tray import *
from icecube import (icetray, dataclasses, dataio, 
                     phys_services, gulliver, cscd_llh)

from icecube.filterscripts.offlineL2.Globals import ehe_wg, ehe_wg_Qstream
from icecube.filterscripts.offlineL2 import level2_IceTop_globals
from icecube.phys_services.which_split import which_split

@icetray.traysegment
def IceTopWriter(tray, name, Filename):
    """IceTop Output"""
    tray.AddModule('I3Writer', name,
        Filename=Filename,
        Streams=[icetray.I3Frame.DAQ, icetray.I3Frame.Physics ],  
        DropOrphanStreams=[icetray.I3Frame.DAQ],
        If=which_split(split_name=level2_IceTop_globals.icetop_physics_stream) | (lambda f: f.Stop == icetray.I3Frame.DAQ)
    )

@icetray.traysegment
def EHEWriter(tray, name, Filename):
    """EHE Output"""
    tray.AddModule('I3Writer', name,
        Filename=Filename,
        Streams=[icetray.I3Frame.DAQ, icetray.I3Frame.Physics ],
        DropOrphanStreams=[icetray.I3Frame.DAQ],
        If=lambda f:ehe_wg(f) or ehe_wg_Qstream(f)
    )

@icetray.traysegment
def SLOPWriter(tray, name, Filename):
    """SLOP Output"""
    tray.AddModule('I3Writer', name,
        Filename=Filename,
        Streams=[icetray.I3Frame.DAQ, icetray.I3Frame.Physics ],
        DropOrphanStreams=[icetray.I3Frame.DAQ],
        If=which_split(split_name='SLOPSplit') | (lambda f: f.Stop == icetray.I3Frame.DAQ)
    )

@icetray.traysegment
def RootWriter(tray, name, Filename):
    """Root Output"""
    from icecube import tableio, rootwriter
    root = rootwriter.I3ROOTTableService(Filename, 'MasterTree')
    converter = phys_services.converters.I3EventInfoConverterFromRecoPulses()
    tray.AddModule(tableio.I3TableWriter, 'TableWriter',
        TableService=root,
        SubEventStreams=['InIceSplit'],
        Keys=[
              # things from Pole
              'I3EventHeader',
              'PoleMuonLinefit',
              'PoleMuonLlhFit',
              'PoleMuonLlhFitFitParams',
              'CascadeFilter_ToiVal',
              'CascadeFilter_LFVel',
              'CascadeFilter_CscdLlh',
              'OnlineL2_PoleL2IpdfGConvolute_2it',  #Reco results from online L2
              'OnlineL2_PoleL2IpdfGConvolute_2itFitParams',
              'OnlineL2_PoleL2MPEFit',
              'OnlineL2_PoleL2MPEFitFitParams',
              'OnlineL2_PoleL2MPEFitCuts',
              'OnlineL2_PoleL2MPEFitMuE',
              'OnlineL2_PoleL2BayesianFit',
              'OnlineL2_PoleL2BayesianFitFitParams',
              'OnlineL2_CramerRaoPoleL2IpdfGConvolute_2itParams',
              'OnlineL2_CramerRaoPoleL2MPEFitParams',
              'PoleMuonLlhFitCutsFirstPulseCuts',
              'OnlineL2_PoleL2SPE2it_TimeSplit1',
              'OnlineL2_PoleL2SPE2it_TimeSplit2',
              'OnlineL2_PoleL2SPEFit2it_GeoSplit1',
              'OnlineL2_PoleL2SPEFit2it_GeoSplit2',
              'OnlineL2_PoleL2MPEFit_TruncatedEnergy_AllBINS_MuEres',
              'OnlineL2_PoleL2MPEFit_TruncatedEnergy_AllBINS_Muon',
              'OnlineL2_PoleL2MPEFit_TruncatedEnergy_AllBINS_Neutrino',
              'I3TriggerHierarchy',
              'FilterMask',
              'QFilterMask',
              # 'I3VEMCalData', # cannot be deserialized
                  
              # MC
              'CorsikaWeightMap',
              'I3MCTree',
              'I3MCTree_preMuonProp',
              'I3MCWeightDict',
              'MCPrimary',
              'MCPrimaryInfo',
              'WIMP_lep_weight',
              'WIMP_nu_weight',
              'WIMP_vgen',
              'WimpTime',
                
              # pulses
              'SRTInIcePulses',
              # remove north pole processing
              #'TWCSRTInIcePulses',
              #'NorthMuonImprovedLinefit',
              #'NorthMuonLlhFit',
              'SRTTWOfflinePulsesDC',
              'TWOfflinePulsesHLC',
              'TWSRTOfflinePulses_WIMP',
              'RTTWOfflinePulses_FR_WIMP',
                  
              # muon
              'SPEFit2',
              'SPEFit2CramerRao',
              'MPEFit',
              'MPEFitCramerRao',
              'MPEFitMuE',
              'MPEFitMuEX',
              'CVMultiplicity',
              'CVStatistics',
              'MPEFitCharacteristics',
              'SPEFit2Characteristics',
                  
              # cascades
              'CascadeLineFit_L2',
              'CascadeDipoleFit_L2',
              'CascadeLast_L2',
              'CascadeLlhVertexFit_L2',
              'CascadeLlhVertexFitSplit_L2',
              'CascadeFillRatio_L2',
              'CascadeSplitPulses_L2',
              'CascadeLineFitSplit_L2',
              'CascadeToISplit_L2',
              'CascadeImprovedLineFit_L2',
              'CascadeContainmentTagging_L2',
              'CascadeTopo_CscdSplitCount',
              'CascadeLlhVertexFit_L2Params',
                  
              # deepcore
              'DipoleFit_DC',
              'CascadeLast_DC',
              'ToI_DC',
                  
              # WIMP
              'LineFit_WIMP',
              'SPEFitSingle_WIMP',
              'SPEFit2_WIMP',
              'FiniteRecoFit_WIMP',
              #'FiniteRecoLlh_WIMP', # no default converter
              #'FiniteRecoCuts_WIMP', # no default converter
                  
              #FSS
              'SPEFit2CramerRao_FSS',
              'SPEFit2MuE_FSS',
        ]
    )

# Create a module to calculate the gaps and livetime of data files
class CalculateGaps(icetray.I3Module):
    def __init__(self, context):
        icetray.I3Module.__init__(self, context)
        self.AddParameter('OutputFileName','Name of Output Gaps File','')
        self.AddParameter('EventHeaderName','Name of the Event Header',
                          'I3EventHeader')
        self.AddParameter('MinGapTime', ('Minimum time (in seconds) ' +
                          'between events to consider as a data gap'), 30)
        self.AddOutBox("OutBox")

    def Configure(self):
        self.outputFileName = self.GetParameter('OutputFileName')
        self.eventHeaderName = self.GetParameter('EventHeaderName')
        self.minGapTime = self.GetParameter('MinGapTime')

        self.firstEvent = True
        self.totalGap = 0

        self.outputlines = []

        self.eventTime = None
        self.eventID = None
        self.prevEventTime = None
        self.prevEventID = None
        self.firstTime = None

    def DAQ(self, frame):
        if frame.Has(self.eventHeaderName):
            eventHeader = frame[self.eventHeaderName]
            self.eventTime = eventHeader.start_time
            runID = eventHeader.run_id
            self.eventID = eventHeader.event_id

            if self.firstEvent:
                self.firstTime = self.eventTime.utc_daq_time
                line = 'Run: %d\n' % runID
                self.outputlines.append(line)
                line = 'First Event of File: %d %d %d\n' % (self.eventID,
                    self.eventTime.utc_year, self.eventTime.utc_daq_time)
                self.outputlines.append(line)
                self.firstEvent = False
            else:
                deltaT = (self.eventTime.utc_daq_time -
                          self.prevEventTime.utc_daq_time ) / 1e10
                if (deltaT > self.minGapTime):
                    self.totalGap += deltaT
                    line = 'Gap Detected: %.2f %d %d %d %d\n' % (deltaT,
                        self.prevEventID, self.prevEventTime.utc_daq_time,
                        self.eventID, self.eventTime.utc_daq_time)
                    self.outputlines.append(line)
            
            self.prevEventTime = self.eventTime
            self.prevEventID = self.eventID

        self.PushFrame(frame, "OutBox")
    
    def Finish(self):
        self.outfile = open(self.outputFileName, 'w')
    
        for line in self.outputlines:
            self.outfile.write(line)
    
        if self.firstEvent:
            icetray.logging.log_warn("No %s has been found. Gaps file will be empty." % self.eventHeaderName)
        else:
            line = 'Last Event of File: %d %d %d\n' % (self.eventID,
                self.eventTime.utc_year, self.eventTime.utc_daq_time)
            self.outfile.write(line) 
            livetime = ((self.eventTime.utc_daq_time - self.firstTime) / 1e10 -
                        self.totalGap)
            line = 'File Livetime: %.2f\n' % livetime
            self.outfile.write(line)

        self.outfile.close()

@icetray.traysegment
def GapsWriter(tray, name, Filename, MinGapTime = 30):
    tray.AddModule(CalculateGaps, name,
        OutputFileName=Filename,
        MinGapTime = MinGapTime
    )
