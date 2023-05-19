from icecube import icetray, dataclasses, filter_tools, topeventcleaning, tpx
from icecube.icetray import I3Units
from icecube.filterscripts import filter_globals
from icecube.filterscripts.offlineL2 import level2_IceTop_globals

class IceTopWaveformSplitter(icetray.I3ConditionalModule):
    
    def __init__(self, ctx):
        super(IceTopWaveformSplitter, self).__init__(ctx)
        
        self.input      = 'IceTopVEMPulses'
        self.output_hlc = 'IceTopHLCVEMPulses'
        self.output_slc = 'IceTopSLCVEMPulses'
        
        self.AddParameter('Input', 'Name of input pulse series', self.input)
        self.AddParameter('OutputHLC', 'Name of HLC pulses', self.output_hlc)
        self.AddParameter('OutputSLC', 'Name of SLC pulses', self.output_slc)
        self.AddOutBox('OutBox')
    
    def Configure(self):
        self.input      = self.GetParameter('Input')
        self.output_hlc = self.GetParameter('OutputHLC')
        self.output_slc = self.GetParameter('OutputSLC')
    
    def DAQ(self, frame):
        if not frame.Has(self.input):
            self.PushFrame(frame)
            return
        
        input_pulses = dataclasses.I3RecoPulseSeriesMap.from_frame(frame, self.input)
        output_pulses_hlc = dataclasses.I3RecoPulseSeriesMap()
        output_pulses_slc = dataclasses.I3RecoPulseSeriesMap()
        for omkey, pulse_series in input_pulses:
            om_pulses_hlc = dataclasses.I3RecoPulseSeries()
            om_pulses_slc = dataclasses.I3RecoPulseSeries()
            for pulse in pulse_series:
                flags = pulse.flags
                if (flags & dataclasses.I3RecoPulse.PulseFlags.ATWD) and (flags & dataclasses.I3RecoPulse.PulseFlags.LC):
                    om_pulses_hlc.append(pulse)
                elif not (flags & dataclasses.I3RecoPulse.PulseFlags.LC):
                    om_pulses_slc.append(pulse)
            if len(om_pulses_hlc) > 0:
                output_pulses_hlc[omkey] = om_pulses_hlc
            if len(om_pulses_slc) > 0:
                output_pulses_slc[omkey] = om_pulses_slc
        frame[self.output_hlc] = output_pulses_hlc
        frame[self.output_slc] = output_pulses_slc
        self.PushFrame(frame)


@icetray.traysegment
def CalibrateAndExtractIceTop(tray, name,
    IceTopPhysicsStream             = level2_IceTop_globals.icetop_physics_stream,
    Pulses                          = '',
    VEMPulses                       = level2_IceTop_globals.icetop_vem_pulses,
    HLCVEMPulses                    = level2_IceTop_globals.icetop_hlc_vem_pulses,
    SLCVEMPulses                    = level2_IceTop_globals.icetop_slc_vem_pulses,
    HLCTankPulses                   = level2_IceTop_globals.icetop_hlc_pulses,
    BadDOMs                         = level2_IceTop_globals.icetop_bad_doms,
    BadTanks                        = level2_IceTop_globals.icetop_bad_tanks,
    TankPulseMergerExcludedTanks    = level2_IceTop_globals.icetop_tank_pulse_merger_excluded_tanks,
    ClusterCleaningExcludedTanks    = level2_IceTop_globals.icetop_cluster_cleaning_excluded_tanks,
    CleanedHLCTankPulses            = level2_IceTop_globals.icetop_clean_hlc_pulses):
    
    tray.AddModule('I3VEMConverter', name + '_VEMConverter',
        PEPulses  = Pulses,
        VEMPulses = VEMPulses,
        If        = lambda frame: Pulses in frame
        )
    
    tray.AddModule(IceTopWaveformSplitter, name + '_IceTopWaveformSplitter',
        Input     = VEMPulses,
        OutputHLC = HLCVEMPulses,
        OutputSLC = SLCVEMPulses,
        If        = lambda frame: Pulses in frame
        )
    
    tray.AddModule('I3TankPulseMerger', name + '_TankPulseMerger',
        InputVEMPulses   = HLCVEMPulses,
        OutputTankPulses = HLCTankPulses,
        BadDomList       = BadDOMs,
        BadTankList      = BadTanks,
        ExcludedTanks    = TankPulseMergerExcludedTanks,
        MaxHGLGTimeDiff  = 40.0 * I3Units.ns,               # Default
        If               = lambda frame: Pulses in frame
        )
    
    tray.AddModule('I3TopHLCClusterCleaning', IceTopPhysicsStream,
        SubEventStreamName        = IceTopPhysicsStream,
        InputPulses               = HLCTankPulses,
        OutputPulses              = CleanedHLCTankPulses,
        BadTankList               = TankPulseMergerExcludedTanks,
        ExcludedTanks             = ClusterCleaningExcludedTanks,
        InterStationTimeTolerance = 200.0 * I3Units.ns,              # Default
        IntraStationTimeTolerance = 200.0 * I3Units.ns,              # Default
        If                        = lambda frame: Pulses in frame
        )
    
    # Distribute pole frame objects that were from the IceTopSplit
    tray.AddModule('DistributePnFObjects', name + '_distribute_Q_items_to_P',
        SubstreamNames = [IceTopPhysicsStream]
        )
    
    # Clean up the garbage we created during processing
    tray.AddModule('Delete', name + '_Delete',
        Keys = [VEMPulses]
        )
