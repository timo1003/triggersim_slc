
from icecube import icetray
from icecube.filterscripts.offlineL2 import level2_IceTop_globals

# the online filter globals
from icecube.filterscripts import filter_globals

###################################################
########## CONDITIONAL EXECUTION STUFF ############
###################################################

#def which_split(frame,split_name=None,keep_q=False):
#    if frame.Stop == icetray.I3Frame.Physics:
#        if frame['I3EventHeader'].sub_event_stream == split_name:
#                return 1
#        else:
#                return 0
#    elif keep_q and frame.Stop == icetray.I3Frame.DAQ:
#        return 1
#    else:
#        return 0

### DEEPCORE ###
def deepcore_wg(frame):
    if frame.Stop == icetray.I3Frame.Physics and frame.Has('FilterMask'):
        if frame['FilterMask'].get(filter_globals.DeepCoreFilter).condition_passed:
            return 1
        else:
            return 0
    else:
        return 0

### WIMP ####
def wimp_wg(frame):
    if frame.Stop == icetray.I3Frame.Physics and frame.Has('FilterMask'):
        if (frame['FilterMask'].get(filter_globals.MuonFilter).condition_passed or
            frame['FilterMask'].get(filter_globals.LowUpFilter).condition_passed or
            frame['FilterMask'].get(filter_globals.DeepCoreFilter).condition_passed or
            frame['FilterMask'].get(filter_globals.VEFFilter).condition_passed):
                return True
        else:
            return False
    else:
        return False

### MUON ####
def muon_wg(frame):
     try:
         return (
                  (frame['FilterMask'].has_key(filter_globals.DeepCoreFilter) and bool(frame['FilterMask'][filter_globals.DeepCoreFilter])) or
                  (frame['FilterMask'].has_key(filter_globals.MuonFilter)     and bool(frame['FilterMask'][filter_globals.MuonFilter])) or
                  (frame['QFilterMask'].has_key(filter_globals.HighQFilter)   and bool(frame['QFilterMask'][filter_globals.HighQFilter])) or
                  (frame['FilterMask'].has_key(filter_globals.FilterMinBias)  and bool(frame['FilterMask'][filter_globals.FilterMinBias])) or
                  #(frame['FilterMask'].has_key(filter_globals.LowUpFilter)    and bool(frame['FilterMask'][filter_globals.LowUpFilter])) or                                                                                                                                         
                  (frame['FilterMask'].has_key(filter_globals.SunFilter)      and bool(frame['FilterMask'][filter_globals.SunFilter])) or
                  (frame['FilterMask'].has_key(filter_globals.MoonFilter)     and bool(frame['FilterMask'][filter_globals.MoonFilter])))
     except KeyError:
         return False

### icetop-muon coincident ###
def icetop_wg_coinc_icetop(frame):
    if not frame.Has(level2_IceTop_globals.icetop_clean_coinc_pulses):
        return False
    has_STAx = False
    has_inice_coincidence = False
    if frame.Has('QFilterMask'):
        filter_mask_map = frame['QFilterMask']
        for filter_mask in filter_mask_map:
            name = filter_mask.key()
            filter = filter_mask.data()
            # All events passing IceTopSTA3_13 should be included in SDST_IceTopSTA3_13
            # Same for InIceSMT_IceTopCoincidence_13
            if name in ['SDST_IceTopSTA3_13', 'IceTopSTA5_13'] and filter.condition_passed:
                has_STAx = True
            elif name == 'SDST_InIceSMT_IceTopCoincidence_13' and filter.condition_passed:
                has_inice_coincidence = True
    return (has_STAx and has_inice_coincidence)

### CASCADE ###
def cascade_wg(frame):
    if frame.Stop == icetray.I3Frame.Physics and frame.Has('FilterMask'):
        if frame['FilterMask'].get(filter_globals.CascadeFilter).condition_passed:
            return 1
        else:
            return 0
    else:
        return 0


### FSS ###
# lots of different splits: fss_wg is the main one that includes everything
#                           fss_wg_finiteReco is used WIMP hit cleaning and reco
#			    fss_wg_energy_reco is used in Muon reco for special MuEX
def fss_wg(frame):
    if (
          frame.Has('FilterMask') and
           (((frame['FilterMask'][filter_globals.FSSFilter].condition_passed == True) and 
             (frame['FilterMask'][filter_globals.FSSFilter].prescale_passed == True))) 
            #or 
            #(frame.Has('QFilterMask')and 
            # (frame['QFilterMask'][filter_globals.SDST_FilterMinBias].condition_passed == True) and 
            # (frame['QFilterMask'][filter_globals.SDST_FilterMinBias].prescale_passed == True))
            ):
        return True
    return False

def fss_wg_finiteReco(frame):
    if (frame.Has('FilterMask') and (
            ((frame['FilterMask'][filter_globals.FSSFilter].condition_passed == True) and 
             (frame['FilterMask'][filter_globals.FSSFilter].prescale_passed == True)))
            ): 
        return True
    return False

def fss_wg_energy_reco(frame):
    if (
        frame.Has('FilterMask') and 
    
        (frame['FilterMask'][filter_globals.FSSFilter].condition_passed == True) and 
        (frame['FilterMask'][filter_globals.FSSFilter].prescale_passed == True)

        #or 
            #(frame.Has('QFilterMask')
             # and 
             #(frame['QFilterMask'][filter_globals.SDST_FilterMinBias].condition_passed == True) and 
             #(frame['QFilterMask'][filter_globals.SDST_FilterMinBias].prescale_passed == True))
             
             ):
        return True
    return False

### EHE ###
def ehe_wg(frame):
    if frame.Stop == icetray.I3Frame.Physics and frame.Has('QFilterMask'):
        if frame['QFilterMask'].get(filter_globals.HighQFilter).condition_passed :
            return 1
        else:
            return 0
    else:
        return 0

def ehe_wg_Qstream(frame):
    if frame.Stop == icetray.I3Frame.DAQ and frame.Has('QFilterMask'):
        if frame['QFilterMask'].get(filter_globals.HighQFilter).condition_passed :
            return 1
        else:
            return 0
    else:
        return 0

### Monopole ###
def monopole_wg(frame):
    return "FilterMask" in frame and frame["FilterMask"][filter_globals.MonopoleFilter].condition_passed


###################################################
####### PHOTON TABLES :( ##########################
###################################################

PhotonicsServiceFiniteReco = "PhotonicsServiceFiniteReco"
