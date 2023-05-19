#!/usr/bin/env python3

#1;2305;0c
#  Updated Feb 2012:  For 2012 filter tuneup. 
#    Major newness:  SuperDST for all events, limited I3DAQData.  No more SDST in filter tags.
#

import sys
import math, glob

from icecube import icetray, dataclasses, dataio,  gulliver, superdst
#bring in the filter pairs from shared definition file.
from icecube.filterscripts import filter_globals

# Set the streams to the new list for 2012.
allStreams = filter_globals.filter_streams + filter_globals.sdst_streams
daqdataStreams = filter_globals.filters_keeping_allraw
daqdataStreams2 = ['IceTopSTA3_12','IceTopSTA5_12','IceTop_InFill_STA3_12','InIceSMT_IceTopCoincidence_12','EHEFilter_12','FilterMinBias_12']
frtStream = 'FixedRateFilter_12'
sdstStreams = filter_globals.sdst_streams

#filelist = glob.glob('/data/i3store0/users/blaufuss/data/IC86/Run119982_PFFilt/PFFilt_TestData_PhysicsFiltering_Run00119982_Subrun00000000_00000000.i3')
#filelist = glob.glob('/data/i3store0/users/blaufuss/data/IC86/Run119982_PFFilt/PFFilt_TestData_PhysicsFiltering_Run00119982_Subrun00000000_000000[0-1]*.i3')
#filelist = glob.glob('./testclient.i3')

#filelist = glob.glob('/data/i3store0/users/blaufuss/data/newstuff/Filt_IC86_MinBias_June_*.i3')
#filelist = glob.glob('/data/i3store0/users/blaufuss/data/IC86/24hr_testrun_PFFilt/PFFilt_TestData_PhysicsFiltering_Run00120030_Subrun00000000_000001[0-2]?.tar.bz2')
#filelist = glob.glob('/data/i3store0/users/blaufuss/data/IC86/24hr_testrun_PFFilt/PFFilt_TestData_PhysicsFiltering_Run00120030_Subrun00000000_00000100.tar.bz2')
filelist = glob.glob('/data/i3store0/users/blaufuss/data/newstuff/Filt_IC86_Run119431_2_??.i3')

filelist.sort()
print('Infiles:',filelist)
##
## Day frac that this data represents:
##
#day_frac = 674.44    ### 1 file of Run 119431: 128.11 sec
#day_frac = 134.63    ### 5 files of Run 119431: 641.75 sece
#day_frac = 58.58         ## 20 files of run 119982:  1474.91 sec
#day_frac = 39.05         ## 30 files from 120030:  2212 sec
#day_frac = 84.19         # 119431 8 files 1026.2 sec
day_frac = 96.22         # 119431 7 files 1026.2 sec
#day_frac = 1171.6
#day_frac = 333.29    ### MinBias June data: 259.23 seconds

gzip_frac = 12.00     ## <- just the "filter extras", recos, FilterMasks, etc, derated a bit
                       ## since I measured them in isolation and bzip2 optimal there
dst_gzip_frac = 3.42 ## factor applies to 4 SuperDST objects, right now with I3EventHeader and SuperDST
daq_gzip_frac = 1.53 ## compression ratio of I3DAQData+I3DAQDataTrimmed


fmk = filter_globals.qfilter_mask


#TODO: include regular DST foo
#dst_keys = ('I3DST11Header','I3DST11')
dst_keys = (filter_globals.smalltriggerhierarchy,
            filter_globals.eventheader,
            filter_globals.superdst,
            filter_globals.qfilter_mask,
            filter_globals.dst,
            filter_globals.dstheader,
            'I3DST12Reco_InIceSplit0') ##since it gets remapped from filter_globals.dstreco
daq_keys = (filter_globals.rawdaqdata,
            filter_globals.seatbeltdata)

file_ignore = ('PFContinuity','DrivingTime','PassedConventional','PassedAnyFilter','PassedKeepSuperDSTOnly', 'I3EventHeader')
#('PassedConventional','PassedAnyFilter', 'PassedSuperDST',
#               filter_globals.qtriggerhierarchy)

filter_passing_events = dict([(name,0) for name in allStreams])
filter_overlap_events = dict([(name,0) for name in allStreams])
filter_passing_bytes = dict([(name,0.0) for name in allStreams])

sec_per_day = 60.0 * 60.0 * 24.0

nframes = 0
file_size = 0
dst_file_size = 0
daq_file_size = 0
for file in filelist:
    openfile = dataio.I3File(file)
    while openfile.more():
#        frame = openfile.pop_daq()
        frame = openfile.pop_physics()
        nframes += 1

        ####
        ####  Calculate the cost of this frame from FrameObjects
        ####
        frame_size = 0
        dst_frame_size = 0
        daq_frame_size = 0
        for item in frame.keys():
            # Note: ignoring the PassedConventional/PassedAnyFilter flags, since it goes away
            if item not in file_ignore:      
                ### Frame cost: size of obj + 12b overhead + size(name) + size(type)
                if item in daq_keys:
                    daq_frame_size += frame.size(item)+ 12 + len(item) + len(frame.type_name(item))
                elif item not in dst_keys:
                    frame_size += frame.size(item)+ 12 + len(item) + len(frame.type_name(item))
                else:
                    dst_frame_size += frame.size(item)+ 12 + len(item) + len(frame.type_name(item))
                    #print item, frame.size(item), '12 ', len(item), len(frame.type_name(item)), frame.size(item)+12+len(item)+len(frame.type_name(item))
        #print frame,
        #print 'size: ',frame_size,'dst size: ', dst_frame_size, 'daq_size: ',daq_frame_size 
        ## There is a small per-frame overhead.  19 b
        frame_size += 19
        file_size += frame_size + dst_frame_size + daq_frame_size
        dst_file_size += dst_frame_size/dst_gzip_frac
        frame_accounted = False

        if not nframes%10000:
            print('Mark : ',nframes)


        ####
        ####  Take a look at the contents of the std FilterMask
        ####    These are the few events selecting to keep I3DAQData
        # Using the presence of the bool: PassedAnyFilter as tag
        if frame.Has(fmk):
            filt_mask = frame.Get(fmk)
        else:
            #print 'YIKES no QFilterMask'
            continue
        # Quick sping thru mask, see how many filters passing.
        #print "Assign blame"
        npass = 0
        #Check the FRT first
        if filt_mask[frtStream].prescale_passed:
            npass = 1
        else:
            for key in filt_mask.keys():
                if key in daqdataStreams2:
                    if filt_mask[key].prescale_passed:
                        npass += 1
        #print 'Num Filters selected this event:', npass
        if npass > 0:
            bw_charge = float(frame_size)/(npass*gzip_frac) + float(daq_frame_size)/(npass*daq_gzip_frac)
            frame_accounted = True
         # Now loop over the fm again, and assign blame.
        if filt_mask[frtStream].prescale_passed:
            filter_passing_events[frtStream] += 1
            filter_passing_bytes[frtStream] += bw_charge
            print('FRT event', npass)
        for key in filt_mask.keys():
            if key in daqdataStreams2:
                if filt_mask[key].prescale_passed:
                    filter_passing_events[key] += 1
                    filter_passing_bytes[key] += bw_charge
                    if npass > 1:
                        filter_overlap_events[key] +=1

        ####
        ####  Now repeated for Super DST events (majority)
        ####
        # Quick sping thru mask, see how many filters passing.
        npass_dst = 0
        for key in filt_mask.keys():
            if key not in daqdataStreams:
                if key not in sdstStreams:
                    if filt_mask[key].prescale_passed:
                        npass_dst += 1
        #print 'Num Filters selected this event:', npass_dst
        if npass_dst > 0:
            bw_charge = float(frame_size)/(npass_dst*gzip_frac) + float(daq_frame_size)/(npass_dst*daq_gzip_frac)
        # Now loop over the fm again, and assign blame.
        for key in filt_mask.keys():
            if key not in daqdataStreams:
                if key not in sdstStreams:
                    if filt_mask[key].prescale_passed:
                        filter_passing_events[key] += 1
                        if npass_dst > 1:
                            filter_overlap_events[key] +=1
                        if not frame_accounted:
                            filter_passing_bytes[key] += bw_charge

        # now count SDST
        for key in filt_mask.keys():
            if key in sdstStreams:
                if filt_mask[key].prescale_passed:
                    filter_passing_events[key] += 1
                    # No charge for BW


print('NFrames proceesed = ', nframes)
print('Total file size: ', file_size, ' DST file size:', dst_file_size)
print(filter_passing_events)
print(filter_passing_bytes)
end_sum =0.0
for key in filter_passing_bytes.keys():
    end_sum += filter_passing_bytes[key]
print('end sum:', end_sum)
##
## Pretty print city
##
for key in filter_passing_events.keys():
    if key in daqdataStreams:
        mykey = key + ' **I3DAQDATA'
    else:
        mykey = key
    this_rate = filter_passing_events[key]/sec_per_day*day_frac
    overlap_rate = filter_overlap_events[key]/sec_per_day*day_frac
    if filter_passing_events[key] > 0:
        overlap_frac = float(filter_overlap_events[key])/float(filter_passing_events[key])*100.00
    else:
        overlap_frac = 0.0
    print('Rate for ', mykey.ljust(30), ' is %7.2f Hz, with overlap %7.2f Hz ( %7.2f pct) ' %(this_rate,overlap_rate,overlap_frac))

total_mb_day  = 0.0
print('This data is said to be from %7.2f fraction of day.' %day_frac)
for key in filter_passing_bytes.keys():
    if key in daqdataStreams:
        mykey = key + ' **I3DAQDATA'
    else:
        mykey = key
    this_bw = filter_passing_bytes[key]*day_frac/(1000000.0)
    print(' BW for ', mykey.ljust(30), ' used %15i bytes (%10.2f MB/day, gzipped)' \
        %(filter_passing_bytes[key],this_bw))
    total_mb_day += this_bw

print('Total filters BW is %10.2f MB/day.... %10.4f GB/day.' %(total_mb_day,total_mb_day/1000.0))

dst_mb_day = dst_file_size*day_frac/(1000000.0)
print('DST uses %10.2f  MB/day' %dst_mb_day)

total_mb_day += dst_mb_day
print('Total filters+dst BW is %10.2f MB/day.... %10.4f GB/day.' %(total_mb_day,total_mb_day/1000.0))
