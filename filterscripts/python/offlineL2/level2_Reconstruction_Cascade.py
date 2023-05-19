from icecube import icetray, dataclasses
from icecube import linefit, dipolefit, clast, cscd_llh, fill_ratio, tensor_of_inertia,CascadeVariables
from icecube.icetray import I3Units


@icetray.traysegment
def OfflineCascadeReco( tray, name, If = lambda f: True, suffix = '',
                        SRTPulses = '',
                        Pulses = '',
                        TopoPulses = '',
                        CascadeLineFit = 'CascadeLineFit',
                        CascadeDipoleFit = 'CascadeDipoleFit',
                        CascadeLast = 'CascadeLast',
                        CascadeLlhVertexFit = 'CascadeLlhVertexFit',
                        CascadeLlhVertexFitSplit = 'CascadeLlhVertexFitSplit',
                        BadDOMListName = 'BadDomsList',
                        CascadeFillRatio = 'CascadeFillRatio',
                        CascadeSplitPulses = 'CascadeSplitPulses',
                        CascadeLineFitSplit = 'CascadeLineFitSplit',
                        CascadeToISplit = 'CascadeToISplit',
                        CascadeImprovedLineFit = 'CascadeImprovedLineFit',
                        CascadeContainmentTagging = 'CascadeContainmentTagging',
                        ):
    '''
    :param RawPulses:
        Name of the I3RecoPulseSeriesMap to work on. (not cleaned by cascade hit cleaning)
    :param Pulses:
        Name of the I3RecoPulseSeriesMap to work on. (pre-cleaned by cascade hit cleaning)
    :param CascadeLineFit:
        Name of the output linefit fit
    :param CascadeDipoleFit:
        Name of the output dipolefit fit
    :param CascadeLast:
        Name of the output clast fit
    :param CascadeLlhVertexFit:
        Name of the output CascadeLlh fit
    :param BadDOMListName:
        Name of the Bad DOMs list to use in the FillRatio module
        Should be the list that matches the input pulses (HLC pulses with HLC bad dom list, etc.)
    :param CascadeFillRatio:
        Name of the output FillRation fit
    :param CascadeSplitPulses:
        Basename for the average time split cascade pulses
    :param CascadeLineFitSplit:
        Basename for the linefits based on split pulses
    :param CascadeToISplit:
        Basename for the tensor-of-inertia fits based on split pulses
    :param CascadeImprovedLineFit:
        Name of the output improved linefit result based on cascade pulses
    :param suffix:
        Potential suffix to append to the end of all fits, in case of multiple instances
    :param If:
        Python function or module for conditional execution of all fits
    '''

    tray.AddModule( 'I3LineFit', name + '_CascadeLinefit' + suffix,
                    Name = CascadeLineFit + suffix, # ! Name of fit
                    InputRecoPulses = Pulses,
                    LeadingEdge = 'FLE', # ! Use only first leading edge, for Cascades especially
                    If = If,
                    )


    tray.AddModule( 'I3DipoleFit', name + '_CascadeDipolefit' + suffix,
                    AmpWeightPower = 0,
                    DipoleStep = 0,
                    InputRecoPulses = Pulses,
                    MinHits =  5,
                    Name = CascadeDipoleFit + suffix,
                    If = If,
                    )

    tray.AddModule('I3CLastModule', name + '_CascadeLast' + suffix,
                   Name = CascadeLast + suffix,
                   InputReadout = Pulses,
                   If = If,
                   )

    tray.AddModule( 'I3CscdLlhModule', name + '_CascadeLlh' + suffix,
                    InputType = 'RecoPulse', # ! Use reco pulses
                    RecoSeries = Pulses, # ! Name of input pulse series
                    FirstLE = True, # Default
                    SeedWithOrigin = False, # Default
                    SeedKey = CascadeLast + suffix, # ! Seed fit - CLast reco
                    MinHits = 8, # ! Require 8 hits
                    AmpWeightPower = 0.0, # Default
                    ResultName = CascadeLlhVertexFit + suffix, # ! Name of fit result
                    Minimizer = 'Powell', # ! Set the minimizer to use
                    PDF = 'UPandel', # ! Set the pdf to use
                    ParamT = '1.0, 0.0, 0.0, false',   # ! Setup parameters
                    ParamX = '1.0, 0.0, 0.0, false',   # ! Setup parameters
                    ParamY = '1.0, 0.0, 0.0, false',   # ! Setup parameters
                    ParamZ = '1.0, 0.0, 0.0, false',   # ! Setup parameters
                    If = If,
                    )


    tray.AddModule('I3FillRatioModule', name + '_CascadeFillRatio' + suffix,
                   AmplitudeWeightingPower = 0,
                   BadDOMList = BadDOMListName, #! Get the list of Bad DOMs from the frame
                   RecoPulseName = Pulses,
                   ResultName = CascadeFillRatio + suffix,
                   SphericalRadiusMean = 1.0,
                   SphericalRadiusRMS = 1.0,
                   SphericalRadiusMeanPlusRMS = 1.0,
                   SphericalRadiusNCh = 1.0,
                   VertexName = CascadeLlhVertexFit + suffix,
                   If = If,
                   )


    tray.AddModule('I3ResponseMapSplitter', CascadeSplitPulses + suffix, #! Needs non-standard name as output split pulses are based on instance name
                   DoBrightSt = False,
                   DoTRes = False,
                   InputPulseMap = Pulses,
                   InputTrackName = '', #! This means ave time splitting
                   maxDBrightSt = 150,
                   MaxTRes = 1000,
                   MinimumNch = 2,
                   MinTRes = 0,
                   If = If,
                   )

    splitpulses1  = CascadeSplitPulses + suffix + '1'
    splitpulses2  = CascadeSplitPulses + suffix + '2'

    tray.AddModule( 'I3LineFit', name + '_CascadeLinefitSplit1' + suffix,
                    Name = CascadeLineFitSplit + '1' + suffix, # ! Name of fit
                    InputRecoPulses = splitpulses1,
                    LeadingEdge = 'FLE', # ! Use only first leading edge, for Cascades especially
                    If = If,
                    )

    tray.AddModule( 'I3LineFit', name + '_CascadeLinefitSplit2' + suffix,
                    Name = CascadeLineFitSplit + '2' + suffix, # ! Name of fit
                    InputRecoPulses = splitpulses2,
                    LeadingEdge = 'FLE', # ! Use only first leading edge, for Cascades especially
                    If = If,
                    )

    tray.AddModule('I3TensorOfInertia', name + '_CascadeToISplit1' + suffix,
                   AmplitudeOption = 1,
                   AmplitudeWeight =1,
                   InputReadout = splitpulses1,
                   InputSelection = '',
                   MinHits = 3,
                   Name =  CascadeToISplit + '1' + suffix,
                   If = If,
                   )

    tray.AddModule('I3TensorOfInertia', name + '_CascadeToISplit2' + suffix,
                   AmplitudeOption = 1,
                   AmplitudeWeight =1,
                   InputReadout = splitpulses2,
                   InputSelection = '',
                   MinHits = 3,
                   Name =  CascadeToISplit + '2' + suffix,
                   If = If,
                   )

    tray.AddModule( 'I3CscdLlhModule', name + '_CascadeLlhSplit1' + suffix,
                    InputType = 'RecoPulse', # ! Use reco pulses
                    RecoSeries = splitpulses1, # ! Name of input pulse series
                    FirstLE = True, # Default
                    SeedWithOrigin = False, # Default
                    SeedKey = CascadeToISplit + '1' + suffix, # ! Seed fit - ToI split1 reco
                    MinHits = 6, # ! Require 6 hits
                    AmpWeightPower = 0.0, # Default
                    ResultName = CascadeLlhVertexFitSplit +'1' + suffix, # ! Name of fit result
                    Minimizer = 'Powell', # ! Set the minimizer to use
                    PDF = 'UPandel', # ! Set the pdf to use
                    ParamT = '1.0, 0.0, 0.0, false',   # ! Setup parameters
                    ParamX = '1.0, 0.0, 0.0, false',   # ! Setup parameters
                    ParamY = '1.0, 0.0, 0.0, false',   # ! Setup parameters
                    ParamZ = '1.0, 0.0, 0.0, false',   # ! Setup parameters
                    If = If,
                    )
    tray.AddModule( 'I3CscdLlhModule', name + '_CascadeLlhSplit2' + suffix,
                    InputType = 'RecoPulse', # ! Use reco pulses
                    RecoSeries = splitpulses2, # ! Name of input pulse series
                    FirstLE = True, # Default
                    SeedWithOrigin = False, # Default
                    SeedKey = CascadeToISplit + '2' + suffix, # ! Seed fit - ToI split2 reco
                    MinHits = 6, # ! Require 6 hits
                    AmpWeightPower = 0.0, # Default
                    ResultName = CascadeLlhVertexFitSplit +'2' + suffix, # ! Name of fit result
                    Minimizer = 'Powell', # ! Set the minimizer to use
                    PDF = 'UPandel', # ! Set the pdf to use
                    ParamT = '1.0, 0.0, 0.0, false',   # ! Setup parameters
                    ParamX = '1.0, 0.0, 0.0, false',   # ! Setup parameters
                    ParamY = '1.0, 0.0, 0.0, false',   # ! Setup parameters
                    ParamZ = '1.0, 0.0, 0.0, false',   # ! Setup parameters
                    If = If,
                    )

    tray.AddSegment( linefit.simple, CascadeImprovedLineFit+suffix, inputResponse = Pulses, fitName = CascadeImprovedLineFit+suffix, If = If )

    # Containment Tagging
    tray.AddModule('I3VetoModule', 'ContainmentTag'+suffix,
                   HitmapName=Pulses,
                   OutputName=CascadeContainmentTagging + suffix,
                   DetectorGeometry=86,
                   useAMANDA=False,
                   FullOutput=True,
                   If = If,
                   )

    
    # nk: made this part of segment now that tft approved this
    icetray.load("TopologicalSplitter")
    #------ TTrigger requires first pulses as input - MLB 21Apr2014
    #common name for TTrigger input pulses - MLB 29Apr2014
    FirstPulses = 'CscdL2_Topo_HLCFirstPulses'

    def FirstPulseCleaning(frame, InputName, OutputName, If_=lambda f: True):
        """Select the first pulse in each DOM"""
        if not If_(frame):
            return

        pulsemap = dataclasses.I3RecoPulseSeriesMap.from_frame(frame, InputName)
        mask = dataclasses.I3RecoPulseSeriesMapMask(frame, InputName)
        mask.set_none()
        for om, pulse in pulsemap.items():
            if len(pulse) > 0:
                mask.set(om, 0, True)
        frame[OutputName] = mask

    tray.AddModule(FirstPulseCleaning, name + '_FirstPulseCleaning' + suffix,
        InputName = TopoPulses,
        OutputName = FirstPulses,
        If_ = If)

    #common names for TTrigger outputs (MLB 29Apr2014):
    #       number of splits: CscdL2_Topo1stPulse_HLCSplitCount
    #       name of sub-event pulse map: CscdL2_Topo1stPulse_HLC0, CscdL2_Topo1stPulse_HLC1 etc
    tray.AddModule("ttrigger<I3RecoPulse>", "CscdL2_Topo1stPulse_HLC",
                   TimeWindow= 4000*I3Units.ns,
                   XYDist= 400.*I3Units.m,
                   ZDomDist= 30,
                   TimeCone= 1000.*I3Units.ns,
                   OutputName= 'CscdL2_Topo1stPulse_HLC',
                   InputNames= [FirstPulses],
                   SaveSplitCount=True,
                   If = If,
                   )

    tray.AddModule("Delete",name+"_deleteCscdObject1"+suffix,
                   Keys = [
                   "CascadeL2Reco_CascadeDipolefit_L2_rusage",
                   "CascadeL2Reco_CascadeLinefitSplit1_L2_rusage",
                   "CascadeL2Reco_CascadeLinefitSplit2_L2_rusage",
                   "CascadeL2Reco_CascadeLinefit_L2_rusage",
                   "CascadeToISplit1_L2Eval2",
                   "CascadeToISplit1_L2Eval3",
                   "CascadeToISplit2_L2Eval2",
                   "CascadeToISplit2_L2Eval3",
                   ])

    #### new in 2013:
    # in case topological splitter found exactly 1 split:
    tray.AddSegment(TopoSplitFits_Singles, name+'CscdSingles',
                    suffix=suffix,
                    SRTPulses=SRTPulses,
                    If = lambda f: If(f) and f["CscdL2_Topo1stPulse_HLCSplitCount"].value==1,
                    )
    # in case topological splitter found exactly 2 splits:
    tray.AddSegment(TopoSplitFits_Doubles, name+'CscdDoubles',
                    suffix=suffix,
                    If = lambda f: If(f) and f["CscdL2_Topo1stPulse_HLCSplitCount"].value==2,
    )


#### new in 2013:
@icetray.traysegment
def TopoSplitFits_Singles(tray, name, SRTPulses='SRTInIcePulses', suffix='', If = lambda frame: True):

    tray.AddModule("I3VetoModule", name+"Veto_Singles"+suffix,
                   HitmapName=SRTPulses,
                   OutputName="CascadeContainmentTagging_Singles"+suffix,
                   DetectorGeometry=86,
                   useAMANDA=False,
                   FullOutput=True,
                   If = If,
                   )
    tray.AddModule("I3OMSelection<I3RecoPulseSeries>",name+"omselection"+suffix,
                   InputResponse =SRTPulses,
                   OmittedStrings = [79,80,81,82,83,84,85,86],
                   OutputOMSelection =SRTPulses+"_BadOMSelectionString"+suffix,
                   OutputResponse =SRTPulses+'_IC_Singles'+suffix,
                   If = If,
                   )

    tray.AddModule('I3CLastModule', name + '_CascadeLast_IC',
                   Name = 'CascadeLast_IC_Singles'+suffix,
                   InputReadout = SRTPulses+'_IC_Singles'+suffix,
                   If = If,
                   )

    tray.AddModule('I3CscdLlhModule', name + '_CascadeLlh_IC',
                   InputType = 'RecoPulse', # ! Use reco pulses
                   RecoSeries = SRTPulses+'_IC_Singles'+suffix, # ! Name of input pulse series
                   FirstLE = True, # Default
                   SeedWithOrigin = False, # Default
                   SeedKey = 'CascadeLast_IC_Singles'+suffix, # ! Seed fit - CLast reco
                   MinHits = 8, # ! Require 8 hits
                   AmpWeightPower = 0.0, # Default
                   ResultName = 'CascadeLlhVertexFit_IC_Singles'+suffix, # ! Name of fit result
                   Minimizer = 'Powell', # ! Set the minimizer to use
                   PDF = 'UPandel', # ! Set the pdf to use
                   ParamT = '1.0, 0.0, 0.0, false',   # ! Setup parameters
                   ParamX = '1.0, 0.0, 0.0, false',   # ! Setup parameters
                   ParamY = '1.0, 0.0, 0.0, false',   # ! Setup parameters
                   ParamZ = '1.0, 0.0, 0.0, false',   # ! Setup parameters
                   If = If,
                   )

    tray.AddModule("Delete", name+"deleteCscdObject_Singles"+suffix,
        Keys = [
                SRTPulses+"_BadOMSelectionString"+suffix,
                SRTPulses+"_IC_Singles"+suffix,
                ])

#### new in 2013:
@icetray.traysegment
def TopoSplitFits_Doubles(tray, name, suffix='', If = lambda frame: True):

    for i in range(2):
        tray.AddModule("I3VetoModule", name+("Veto_Doubles_%d" % i)+suffix,
                       HitmapName='CscdL2_Topo1stPulse_HLC%d' % i,
                       OutputName=('CascadeContainmentTagging_Doubles%d' % i)+suffix,
                       DetectorGeometry=86,
                       useAMANDA=False,
                       FullOutput=True,
                       If = If,
                       )

        tray.AddModule("I3OMSelection<I3RecoPulseSeries>", ("%s%d" % (name,i))+suffix,
                       InputResponse = 'CscdL2_Topo1stPulse_HLC%d' % i,
                       OmittedStrings = [79,80,81,82,83,84,85,86],
                       OutputOMSelection = 'CscdL2_Topo1stPulse_HLC_BadOMSelectionString%d' % i,
                       OutputResponse = 'CscdL2_Topo1stPulse_HLCPulses_Doubles_IC%d' % i,
                       If = If,
                       )

        tray.AddModule('I3CLastModule', ('%s_CascadeLast_IC%d' % (name,i))+suffix,
                       Name = 'CascadeLast_TopoSplit_IC%d' % i,
                       InputReadout = 'CscdL2_Topo1stPulse_HLCPulses_Doubles_IC%d' % i,
                       If = If,
                       )

        tray.AddModule( 'I3CscdLlhModule', ('%s_CascadeLlh_IC%d' % (name,i))+suffix,
                        InputType = 'RecoPulse', # ! Use reco pulses
                        RecoSeries = 'CscdL2_Topo1stPulse_HLCPulses_Doubles_IC%d' % i,
                        FirstLE = True, # Default
                        SeedWithOrigin = False, # Default
                        SeedKey = 'CascadeLast_TopoSplit_IC%d' % i, # ! Seed fit - CLast reco
                        MinHits = 8, # ! Require 8 hits
                        AmpWeightPower = 0.0, # Default
                        ResultName = 'CascadeLlh_TopoSplit_IC%d' % i, # ! Name of fit result
                        Minimizer = 'Powell', # ! Set the minimizer to use
                        PDF = 'UPandel', # ! Set the pdf to use
                        ParamT = '1.0, 0.0, 0.0, false',   # ! Setup parameters
                        ParamX = '1.0, 0.0, 0.0, false',   # ! Setup parameters
                        ParamY = '1.0, 0.0, 0.0, false',   # ! Setup parameters
                        ParamZ = '1.0, 0.0, 0.0, false',   # ! Setup parameters
                        If = If,
                        )

        tray.AddModule("Delete", name+("deleteCscdObject%d" % i)+suffix,
            Keys = [
                    'CscdL2_Topo1stPulse_HLC_BadOMSelectionString%d' % i,
                    'CscdL2_Topo1stPulse_HLCPulses_Doubles_IC%d' % i,
                    ])
