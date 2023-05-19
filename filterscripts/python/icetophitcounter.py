import numpy as np

from icecube import icetray
from icecube import dataclasses

from . import filter_globals

#
# IceTray Module to calculate the in-time icetop hits matching an in-ice track at surface impact
#     In time here defined to be 0 <=  (IceTopPulseTime - Expected time from track) <=1000 ns
#
#   Inputs:
#     IT_hlc_pulses, IT_slc_pulses - IceTop SLC,HLC TankPulse series from Q frame
#     InIceRreco - InIceReco to use to anchor surface time and position
#
#   Outputs to frame:
#      Count_HLC_InTime - I3Int number of HLC hits In time.
#      Count_SLC_InTime - I3Int number of SLC hits in time.
#

## Calculate the number of hits in-time with InIce track
def CountIceTopInTime(frame,
                      InIceReco = 'OnlineL2_SplineMPE', 
                      IT_hlc_pulses = 'ITHLCTankPulses', 
                      IT_slc_pulses = 'ITSLCTankPulses',
                      Count_HLC_InTime = 'IT_HLC_InTime',
                      Count_SLC_InTime = 'IT_SLC_InTime',):
  if (InIceReco in frame):
      geo = frame["I3Geometry"]
      particle=frame[InIceReco]
      hlc = dataclasses.I3RecoPulseSeriesMap.from_frame(frame, IT_hlc_pulses)
      slc = dataclasses.I3RecoPulseSeriesMap.from_frame(frame, IT_slc_pulses)

      vz = dataclasses.I3Constants.c * particle.dir.z
      delta_t= (particle.pos.z - dataclasses.I3Constants.zIceTop) /(vz)

      n_intimehlc = 0
      for om, pulse_series in hlc:
          x_om = geo.omgeo[om].position.x
          y_om = geo.omgeo[om].position.y
          z_om = geo.omgeo[om].position.z
          t_om = particle.time + (particle.dir.x * (x_om - particle.pos.x) + \
                                  particle.dir.y * (y_om - particle.pos.y) + \
                                  particle.dir.z * (z_om - particle.pos.z))/dataclasses.I3Constants.c
          for pulses in pulse_series:
              delt=pulses.time - t_om
              if (delt<=1000 and delt>=0):
                  n_intimehlc += 1

      n_intimeslc = 0
      for om, pulse_series in slc:
          x_om = geo.omgeo[om].position.x
          y_om = geo.omgeo[om].position.y
          z_om = geo.omgeo[om].position.z
          t_om = particle.time + (particle.dir.x * (x_om - particle.pos.x) + \
                                  particle.dir.y * (y_om - particle.pos.y) + \
                                  particle.dir.z * (z_om - particle.pos.z))/dataclasses.I3Constants.c
          for pulses in pulse_series:
              delt=pulses.time - t_om
              if (delt<=1000 and delt>=0):
                  n_intimeslc += 1

      #print('SLCs in time:', n_intimeslc, '; HLCs in time', n_intimehlc)
      frame[Count_HLC_InTime] = icetray.I3Int(n_intimehlc)
      frame[Count_SLC_InTime] = icetray.I3Int(n_intimeslc)
