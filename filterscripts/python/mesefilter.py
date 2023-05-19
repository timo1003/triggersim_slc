from icecube import icetray
from icecube.icetray import I3Units
import operator

# MESE Filter Traysegment - 2015

@icetray.traysegment
def MeseFilter(tray,name, pulses='RecoPulses',If = lambda f: True):
    """
    Traysegment for the MESE veto filter. NEW
    """
    # load needed libs, the "False" suppresses any "Loading..." messages
    from icecube.filterscripts import filter_globals
    icetray.load("filterscripts",False)

    from icecube import dataclasses
    
    TriggerEvalList = [
     filter_globals.inicesmttriggered,
     filter_globals.deepcoresmttriggered,
     filter_globals.inicestringtriggered,
     filter_globals.volumetrigtriggered,
    ]
    def If_with_triggers(frame):
        if not If(frame):
            return False
        for trigger in TriggerEvalList:
            if frame[trigger].value:
                return True
        return False

    tray.AddModule('I3LCPulseCleaning', name+'_lcclean1',
        Input=pulses,
        OutputHLC= pulses+'HLC'+name,
        OutputSLC=pulses+'SLC'+name,
        If = If_with_triggers)
    
    def CleanDeepCore(frame):
        pulsemap = dataclasses.I3RecoPulseSeriesMap.from_frame(frame, pulses+'HLC'+name)
        mask = dataclasses.I3RecoPulseSeriesMapMask(frame, pulses+'HLC'+name, lambda om, idx, pulse: om.string <= 78)
        frame[pulses+'HLC_NoDC'] = mask 
    tray.AddModule(CleanDeepCore, 'nodc', If = If_with_triggers)
    
    def DefineLayers(tray, name, **kwargs):        
    
        def IC79OuterVeto(gcddict):  
            """
            Define the DOMs that make up the downgoing muon veto region for IC79-like geometries.
        
            :param gcddict: a dictionary of OMKey -> (I3OMGeo, I3DOMCalibration, I3DetectorStatus)
                            containing only the DOMs that produce data.
            """
            
            cap_thickness = 90.*icetray.I3Units.m

            from collections import defaultdict
            from icecube.dataclasses import I3OMGeo
            import numpy
        
            # Sort InIce DOMs into strings, ordered by depth
            strings = defaultdict(list)
            for key, items in gcddict.items():
                if items[0].omtype == I3OMGeo.IceCube:
                    strings[key.string].append((key, items))
            for entries in strings.values():
                entries.sort(key=lambda items: items[1][0].position.z, reverse=True) 
        
            # Measure the thickness of the veto cap from the top of the deepest non-DeepCore string
            top = min([entries[0][1][0].position.z for string, entries in strings.items() if string <= 78])
        
            neighbors = defaultdict(int)
            for k in strings:
                head = strings[k][0][1][0].position
                for ok in strings:
                    ohead = strings[ok][0][1][0].position
                    d = numpy.hypot(head.x-ohead.x, head.y-ohead.y)
                    if ok != k and d < 160:
                        neighbors[k] += 1
        
            # Points on the border of a hexagonal grid have fewer than 6 neighbors
            outer = set([k for k, v in neighbors.items() if v < 6])
            inner = set(strings.keys()).difference(outer).difference(set(range(79, 87)))
        
            outer_layer = []
        
            # All DOMs on the outer strings participate in the veto
            for string in outer:
                for key, items in strings[string]:
                    outer_layer.append(key)
                
            # On inner strings, only a layer of DOMs on the top and bottom are in the veto 
            for string in inner:
                for key, (geo, calib, stat) in strings[string]:
                    if geo.position.z >= top - cap_thickness:
                        outer_layer.append(key)
                # Also add the bottom-most active DOM, whereever it is.
                outer_layer.append(strings[string][-1][0])
        
            # Add a second veto layer just under the dust peak
            dust_layer = []
            for string, entries in strings.items():
                for key, (geo, calib, stat) in entries:
                    z = geo.position.z
                    # if z > -220 and z < -160:
                    if z > -220 and z < -100:
                        dust_layer.append(key)
                        
            icetray.logging.log_info( 'IC{0} outer-layer veto: {1} DOMs'.format(len(strings), len(set(outer_layer))) )
            icetray.logging.log_info( 'IC{0} dust-layer veto: {1} DOMs'.format(len(strings), len(set(dust_layer))) )
            return [outer_layer, dust_layer]
        
        kwargs['VetoLayers'] = IC79OuterVeto
        tray.AddModule("LayerVeto", name, **kwargs)

    tray.AddSegment(DefineLayers, name + "L4VetoLayer",
                    Pulses=pulses+'HLC'+name,
                    Output="L4VetoLayer",
                    If=If_with_triggers) 

    # apply the veto 
    tray.AddModule('HomogenizedQTot', name+'_qtot_causal', 
        Pulses=pulses, Output='CausalQTot_MESE', VertexTime='L4VetoLayerVertexTime',
        If = If_with_triggers)
        
    # Cut out small, non-starting, and coincident events
    def precut(frame):
        layer_veto_charge = frame['L4VetoLayer0'].value + frame['L4VetoLayer1'].value
        nstring = len(set(om.string for om in dataclasses.I3RecoPulseSeriesMap.from_frame(frame, pulses+'HLC'+name).keys()))
        frame["NString"] = icetray.I3Int(nstring)
        if operator.le(layer_veto_charge,3) and nstring>3 and frame['CausalQTot_MESE'].value>100.:
            isVetoed = False
            # print "Event", frame['I3EventHeader'].start_time, "Qtot:", frame['HomogenizedQTot_MESE'], "NString:",  frame["NString"], "L0:", frame['L4VetoLayer0'].value, "L1:", frame['L4VetoLayer1'].value
        else:
            isVetoed = True
        frame["MESEVeto_Bool"] = icetray.I3Bool(isVetoed)
        
        
    tray.AddModule(precut, name+"_precut", Streams=[icetray.I3Frame.Physics], If=If_with_triggers) 
        
    tray.AddModule("I3FilterModule<I3MeseFilter_15>",
                   name+"MeseFilter",
                   TriggerEvalList = TriggerEvalList,
                   DecisionName = filter_globals.MESEFilter,
                   If = If)

    # clean up after ourselves
    def cleanup(frame, Keys=[]):
        for key in Keys:
            if key in frame:
                del frame[key]
    tray.AddModule(cleanup, name+"_cleanup", Streams=[icetray.I3Frame.Physics],
        Keys = [
            "CausalQTot_MESE",
            "NString",
            "MESEVeto_Bool",
            pulses+'HLC'+name,
            pulses+'SLC'+name,
            'L4VetoLayerPulses0',
            'L4VetoLayerPulses1',
            pulses+'HLC_NoDC'
        ],
        If = If_with_triggers)
