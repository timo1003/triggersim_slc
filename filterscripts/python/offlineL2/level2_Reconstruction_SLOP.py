import I3Tray
from icecube import icetray, dataclasses
from icecube.SLOPtools import TupleTagger, MPCleaner
from icecube.KalmanFilter import MyKalman, MyKalmanSeed

@icetray.traysegment
def SLOPLevel2(tray, name, If = lambda f: True):
        # this is generated online and should not have been
        # cleaned away online. It was cleaned for the the 2013
        # 24h test run, so restore it if it's missing:
        tray.AddModule(TupleTagger, name+"WholeCar",
            PulseMapName="SLOPPulseMask",
            If=lambda frame: If(frame) and ("SLOPLaunchMapTuples" not in frame),
            )

        # this is the rest of the offline SLOP processing:
        # commented at request of BSM WG for 2019 runstart
        # tray.AddModule(MPCleaner, name+"Tide",
        #     PulseMapName="SLOPPulseMask",
        #     If=If,
        #     )

        # this should run if there are lunchTuples in the frame
        tray.AddModule(MyKalmanSeed, name+"Seed_launches",
            InputMapName="SLOPLaunchMapTuples",
            OutputTrack="SLOPTuples_LineFit",
            If=lambda frame: If(frame) and ("SLOPLaunchMapTuples" in frame),
            )

        # if there were not, we just generated PulseTuples. use them instead.
        # this is to work around the missing launchTuples for the 2013 24h test run,
        # or for L2 where launches generally do not exist.
        tray.AddModule(MyKalmanSeed, name+"Seed_pulses",
            InputMapName="SLOPPulseMaskTuples",
            OutputTrack="SLOPTuples_LineFit",
            If=lambda frame: If(frame) and ("SLOPLaunchMapTuples" not in frame),
            )
        def generateReadme(frame, name="README", text=""):
            frame[name] = dataclasses.I3String(text)
            print(text)
        tray.AddModule(generateReadme, name+"generateReadme",
            name = "SLOPTuples_LineFit_README",
            text = "No SLOPLaunchMapTuples object was found in the incoming P-frame. This should only happen for the 2013 24h test runs and not in any other data. If you are seeing this in other data, something is wrong in PnF SLOP processing.",
            Streams=[icetray.I3Frame.Physics],
            If=lambda frame: If(frame) and ("SLOPLaunchMapTuples" not in frame) and ("SLOPPulseMaskTuples" not in frame),
            )
        
        # commented at request of BSM WG for 2019 runstart
        # tray.AddModule(MyKalman, name+"MyKalman",
        #     InputTrack="SLOPTuples_LineFit",
        #     OutputTrack="SLOPKalman",
        #     InputMapName="SLOPPulseMaskHyperClean",
        #     IgnoreDC=True,
        #     IterationMethod=2,
        #     CutRadius=200,
        #     Iterations=3,
        #     NoiseQ=1e-10,
        #     NoiseR=60**2,
        #     If=If,
        #     )
