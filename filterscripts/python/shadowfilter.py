# 
#  copyright  (C) 2012
#  the icecube collaboration
#  $Id: shadowfilter.py 124816 2014-10-20 16:01:56Z david.schultz $
#
#  @file
#  @version $Revision: 124816 $
#  @date $Date: 2014-10-20 12:01:56 -0400 (Mon, 20 Oct 2014) $
#  @author David Boersma <boersma@icecube.wisc.edu>
#  @author Marcos Santander <santander@icecube.wisc.edu>
# 

from icecube import icetray

@icetray.traysegment
def ShadowFilter(tray, name, mcseed=0, If=lambda f: True):
    """
    Sun and moon filters for 2013-2014 online filter season
    (and probably also later).  Almost identical to the 2012-2013 season.
    This segment takes only one configuration parameter, namely the "mcseed",
    which is the seed for the random number generator used for picking a
    relevant MJD in corsika simulated data (the simulation does not provide
    useful event times).
    - DO NOT SET THIS PARAMETER TO A NONZERO VALUE FOR EXPERIMENTAL DATA! 
    - IF YOU DO SET IT, MAKE SURE TO *KEEP* THE GENERATED FAKE MJD TIMES
    """
    from icecube import dataclasses
    from icecube.filterscripts import filter_globals
    icetray.load("filterscripts",False)

    triglist=[filter_globals.inicesmttriggered]
    deg=icetray.I3Units.degree
    max_moon_zenith=90.*deg
    max_sun_zenith=90.*deg
    
    def have_trackfit(frame):
        if frame.Stop != icetray.I3Frame.Physics:
            # this track check only applies to Physics frames
            # icetray checks "If" checks for *all* frames including DAQ
            # maybe non-Physics frames are still relevant for I3FilterModule?
            return True
        trackfit=filter_globals.muon_llhfit
        if trackfit in frame:
            fitstatus = frame[filter_globals.muon_llhfit].fit_status
            if fitstatus == dataclasses.I3Particle.OK:
                # print("SUCCESS found fit %s in frame with status OK" % trackfit)
                return True
            # else:
                # print("FAILFIT found fit %s in frame with status NOT OK: %d" % (trackfit,fitstatus))
        # else:
            # print("MISSINGFIT: fit %s not found in frame" % trackfit)
        return False

    mc=(mcseed>0)
    mcrng=""
    if mc:
        mcrng="CorsikaRandService"
        tray.AddService("I3GSLRandomServiceFactory","moonfilter_rng")(
            ("Seed",mcseed),
            ("InstallServiceAs", mcrng),
        )
    

    # djb: adding shadow filters (default values: DST ROI for Moon)
    def add_shadowfilter(the_tray,label,name,**kwargs):
        mjdstart = kwargs.pop("CorsikaMJDStart",0.)
        mjdend = kwargs.pop("CorsikaMJDEnd",0.)
        if (mjdstart <= 0. and mjdend <= 0.):
            mjdarglist = []
        else:
            mjdarglist = [mjdstart,mjdend]
        the_tray.AddModule("I3FilterModule<I3ShadowFilter_13>",label,
            IcePickServiceKey="",
            If=lambda f: If(f) and have_trackfit(f),
            TriggerEvalList=triglist,
            DecisionName=name,
            DiscardEvents=False,
            AzimuthRange=kwargs.pop("AzimuthRange",[-180*deg,+180*deg]),
            ZenithRange=kwargs.pop("ZenithRange",[-10*deg,+10*deg]),
            CorrectSolidAngle=True,
            CorsikaMJDName=kwargs.pop("CorsikaMJDName",""),
            CorsikaMJDRange=mjdarglist,
            CorsikaRandService=mcrng,
            EventHeaderName="I3EventHeader", # filter_globals.eventheader,
            MaximumZenith=kwargs.pop("MaximumZenith",75*deg),
            RecoPulsesName=filter_globals.CleanedMuonPulses,
            NChannelCut=kwargs.pop("NChannelCut",8),
            NStringCut=kwargs.pop("NStrCut",3),
            ParticleName=filter_globals.muon_llhfit,
            WhichShadow=kwargs.pop("WhichShadow","Moon")
        )
        if len(kwargs)>0:
            print(("Unknown shadowfilter options: %s " % kwargs))
            raise RuntimeError("Unknown shadowfilter options")

    if mc:
        MCmonths=[
            ("Jan14", (56678.14583, 56690.47917)),
            ("Feb14", (56705.42361, 56717.95833)),
            ("Mar14", (56732.70139, 56745.37500)),
            ("Apr14", (56760.02083, 56772.69444)),
            ("May14", (56787.38889, 56799.94444)),
            ("Jun14", (56814.77778, 56827.21528)),
            ("Jul14", (56842.14583, 56854.55556)),
            ("EndOfJul14", (56869.46528, 56881.97222)),
            ("Aug14", (56896.73611, 56909.43056)),
            ("Sep14", (56923.99306, 56936.86111)),
            ("Oct14", (56951.29167, 56964.22222)),
            ("Nov14", (56978.65278, 56991.50000)),
            ("Dec14", (57006.05556, 57018.77778)), 
        ]
        
        imonth=mcseed%len(MCmonths)
        monthname=MCmonths[imonth][0]
        (cstart,cend)=MCmonths[imonth][1]
        print(("simulated month for the Moon shadow filter: %s (mjd %f-%f" % (monthname,cstart,cend)))
        if abs(max_moon_zenith-90.*deg)>0.1:
            print("WARNING: unsupported MaximumZenith for the Moon in corsika mode")
        add_shadowfilter(tray,label=filter_globals.MoonFilter,
                              name=filter_globals.MoonFilter,
                              WhichShadow="Moon",
                              MaximumZenith=max_moon_zenith,
                              CorsikaMJDName="CorsikaMoon",
                              CorsikaMJDStart=cstart,
                              CorsikaMJDEnd=cend)
        add_shadowfilter(tray,label=filter_globals.SunFilter,
                              name=filter_globals.SunFilter,
                              WhichShadow="Sun",
                              MaximumZenith=max_sun_zenith,
                              CorsikaMJDName="CorsikaSun",
                              CorsikaMJDStart=56923.1083, # Sunrise 23 September 2014, 02:36.01h
                              CorsikaMJDEnd=57101.9422)   # Sunset  20 March 2015, 22:36.44h
        #                     CorsikaMJDStart=56557.8692, # Sunrise 22 September 2013, 20:51.40h
        #                     CorsikaMJDEnd=56736.7007)   # Sunset  20 March 2014, 16:48.57h
        #                     CorsikaMJDStart=56192.6238, # Sunrise 22 September 2012, 14:58.14h
        #                     CorsikaMJDEnd=56371.4548    # Sunset  20 March     2013, 10:54.52h 
    else:
        add_shadowfilter(tray,label=filter_globals.MoonFilter,
                              name=filter_globals.MoonFilter,
                              WhichShadow="Moon",
                              MaximumZenith=max_moon_zenith)
        add_shadowfilter(tray,label=filter_globals.SunFilter,
                              name=filter_globals.SunFilter,
                              WhichShadow="Sun",
                              MaximumZenith=max_sun_zenith)
