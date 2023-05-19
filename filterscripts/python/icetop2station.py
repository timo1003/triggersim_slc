from icecube import dataclasses, icetray
from icecube.filterscripts import filter_globals


class ReevaluateTriggerOnIceTopSplit(icetray.I3ConditionalModule):
  
    def __init__(self, ctx):
        super(ReevaluateTriggerOnIceTopSplit, self).__init__(ctx)
        
        self.input  = filter_globals.CleanedHLCTankPulses
        self.output = 'IceTop_TwoStationFilter_Bool'
        
        self.AddParameter('Input',  'Name of input pulse series', self.input)
        self.AddParameter('Output', 'Name of filter decision bool', self.output)
        self.AddOutBox('OutBox')
        
        self.pair1 = [46, 81]
        self.pair2 = [80, 36]
        self.pair3 = [36, 79]
        self.pair4 = [26, 79]
        self.pair_list = [self.pair1, self.pair2, self.pair3, self.pair4]
        
    def Configure(self):
        self.input  = self.GetParameter('Input')
        self.output = self.GetParameter('Output')
    
    def Physics(self, frame):
        result = icetray.I3Bool(False)
        if frame.Has(self.input) and frame.Has(filter_globals.icetopvolumetriggered) and frame[filter_globals.icetopvolumetriggered] == True:
            pulses = dataclasses.I3RecoPulseSeriesMap.from_frame(frame, self.input)
            stations = set([omkey.string for omkey, pulse in pulses])
            for pair in self.pair_list:
                hit_count = 0
                for sta in pair:
                    if sta in stations:
                        hit_count += 1

                if hit_count == 2:
                    result.value = True
                    break
        
        frame.Put(self.output, result)
        self.PushFrame(frame)

@icetray.traysegment
def IceTopTwoStationFilter(tray, name,
    If = lambda f: True):

    icetray.load('filterscripts', False)
    
    tray.AddModule(ReevaluateTriggerOnIceTopSplit, name + '_ReevaluateTriggerOnIceTopSplit',
        Input  = filter_globals.CleanedHLCTankPulses,
        Output = 'IceTop_TwoStationFilter_Bool',
        If     = If
        )
    
    tray.AddModule('I3FilterModule<I3BoolFilter>', name + '_TwoStationFilter',
        DecisionName  = filter_globals.IceTopTwoStationFilter,
        DiscardEvents = False,
        Boolkey       = 'IceTop_TwoStationFilter_Bool',
        If            = If
        )
