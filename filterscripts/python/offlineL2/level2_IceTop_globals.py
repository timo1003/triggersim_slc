# the online filter globals
from icecube.filterscripts import filter_globals

bad_doms_list                              = 'BadDomsList'

# from filterscripts/python/filter_globals.py
inicesmttriggered                          = filter_globals.inicesmttriggered
icetopsmttriggered                         = filter_globals.icetopsmttriggered

icetop_physics_stream                      = filter_globals.IceTopSplitter
icetop_bad_doms                            = filter_globals.IceTopBadDoms
icetop_bad_tanks                           = filter_globals.IcetopBadTanks
icetop_tank_pulse_merger_excluded_tanks    = filter_globals.TankPulseMergerExcludedTanks
icetop_cluster_cleaning_excluded_tanks     = filter_globals.ClusterCleaningExcludedTanks
icetop_pe_pulses                           = filter_globals.IceTopDSTPulses
icetop_vem_pulses                          = 'OfflineIceTopVEMPulses'
icetop_hlc_vem_pulses                      = 'OfflineIceTopHLCVEMPulses'
icetop_slc_vem_pulses                      = 'OfflineIceTopSLCVEMPulses'
icetop_hlc_pulses                          = 'OfflineIceTopHLCTankPulses'         # these are the real icetop pulses
icetop_clean_hlc_pulses                    = filter_globals.CleanedHLCTankPulses  # this is only a pulse mask
icetop_clean_coinc_pulses                  = 'CleanedCoincOfflinePulses'
icetop_clean_trigger_hierarchy             = 'CleanedIceTopTriggerHierarchy'

# From 2012 standards
coinc_name                                 = '_IT'
#bad_doms_list                              = 'BadDomsList'

#inicesmttriggered                          = 'InIceSMTTriggered'
#icetopsmttriggered                         = 'IceTopSMTTriggered'

#icetop_physics_stream                      = 'ice_top'
icetop_filter_decision                     = 'OfflineCosmicRayFilter'
icetop_filter_mask                         = 'OfflineIceTopFilterMask'
#icetop_bad_doms                            = 'IceTopBadDOMs'
#icetop_bad_tanks                           = 'IceTopBadTanks'
#icetop_tank_pulse_merger_excluded_tanks    = 'TankPulseMergerExcludedTanks'
#icetop_cluster_cleaning_excluded_tanks     = 'ClusterCleaningExcludedTanks'
#icetop_pe_pulses                           = 'IceTopDSTPulses'
#icetop_vem_pulses                          = 'OfflineIceTopVEMPulses'
#icetop_hlc_vem_pulses                      = 'OfflineIceTopHLCVEMPulses'
#icetop_slc_vem_pulses                      = 'OfflineIceTopSLCVEMPulses'
#icetop_hlc_pulses                          = 'OfflineIceTopHLCTankPulses'      # these are the real icetop pulses
#icetop_clean_hlc_pulses                    = 'CleanedHLCTankPulses'            # this is only a pulse mask
#icetop_clean_coinc_pulses                  = 'CleanedCoincOfflinePulses'
#icetop_clean_trigger_hierarchy             = 'CleanedIceTopTriggerHierarchy'
icetop_shower_cog                          = 'ShowerCOG'
icetop_shower_plane                        = 'ShowerPlane'
icetop_shower_laputop                      = 'LaputopStandard'
icetop_small_shower_decision               = filter_globals.IsSmallShower#'IsSmallShower'
icetop_small_shower_nstation_name          = 'SmallShowerNStations'
icetop_small_shower_laputop                = 'LaputopSmallShower'
