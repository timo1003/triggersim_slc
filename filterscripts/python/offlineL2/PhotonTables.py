### Photonics Tables ###
import os

from icecube import icetray
from icecube import photonics_service
from icecube.filterscripts.offlineL2 import Globals

@icetray.traysegment
def InstallTables(tray, name, PhotonicsDir = "/cvmfs/icecube.opensciencegrid.org/data/photon-tables"):

    # table locations #

    PhotonicsFiniteRecoTabledir   = os.path.join(PhotonicsDir,'SPICEMie')
    PhotonicsFiniteRecoDriverdir  =  os.path.join(PhotonicsFiniteRecoTabledir,'driverfiles')
    PhotonicsFiniteRecoDriverfile =  'finitereco_photorec.list'

    # WIMP
    # FiniteReco #NOTE copied from std-processing 2011
    tray.AddService('I3PhotonicsServiceFactory', 'FiniteRecoPhotonicsService',
        PhotonicsTopLevelDirectory =    PhotonicsFiniteRecoTabledir, 
        DriverFileDirectory =           PhotonicsFiniteRecoDriverdir, 
        PhotonicsLevel2DriverFile =     PhotonicsFiniteRecoDriverfile,
        PhotonicsTableSelection =       2,
        UseDummyService =               False,
        serviceName =                   Globals.PhotonicsServiceFiniteReco,)

