#
# modules used for the Gamma-Ray Follow-Up filtering
#
# For questions or comments regarding this module, please contact:
# Thomas Kintscher <thomas.kintscher@desy.de>
# Konstancja Satalecka <konstancja.satalecka@desy.de>
#

import json
import math
import os.path

import numpy as np
import scipy.interpolate

from icecube import icetray, dataclasses
from icecube.phys_services import I3Calculator
from icecube.icetray import logging



class I3TimeResidualBooker(icetray.I3ConditionalModule):
    '''
    This module stores the time residuals of a pulsemap with respect to a given fit.

    Initially written by Stefan Coenders for the 7-year PS sample.
    '''
    def __init__(self, context):
        super(I3TimeResidualBooker, self).__init__(context)
        # Parameters
        self.AddParameter("Geometry",   "Name of geometry to use",                       "I3Geometry")
        self.AddParameter("Particle",   "Particle to calculate Time Residuals for",      "OnlineL2_SplineMPE")
        self.AddParameter("Pulsemap",   "Pulsemap to use for time residual calculation", "CleanedMuonPulsesIC")
        self.AddParameter("MaxDist",    "Maximal Distance of OM to track",               200.*icetray.I3Units.m)
        self.AddParameter("TimeWindow", "Time Window for residuals",                     [-500.*icetray.I3Units.ns, 500.*icetray.I3Units.ns])
        self.AddOutBox("OutBox")

    def Configure(self):
        self.geometry   = self.GetParameter("Geometry")
        self.i3particle = self.GetParameter("Particle")
        self.pulsemap   = self.GetParameter("Pulsemap")
        self.max_dist   = self.GetParameter("MaxDist")
        self.tw         = self.GetParameter("TimeWindow")

    def Geometry(self, frame):
        # keep the geometry; needed later to calculate distance of closest approach between track and DOMs
        self.geo = frame[self.geometry].omgeo
        self.PushFrame(frame)

    def Physics(self, frame):
        if not frame.Has(self.i3particle):
            logging.log_info("Could not find {0:s} in frame".format(self.i3particle))
            self.PushFrame(frame)
            return
        if not frame.Has(self.pulsemap):
            logging.log_info("Could not find {0:s} in frame".format(self.pulsemap))
            self.PushFrame(frame)
            return

        track    = frame[self.i3particle]
        pulsemap = dataclasses.I3RecoPulseSeriesMap.from_frame(frame, self.pulsemap)

        # calculate track-to-DOM distances and time residuals
        dist = np.array( [ I3Calculator.closest_approach_distance(track, self.geo[om].position)
                             for om, pulses in pulsemap.items() if len(pulses) > 0 ])
        tres = np.array( [ I3Calculator.time_residual(track, self.geo[om].position, pulses[0].time)
                             for om, pulses in pulsemap.items() if len(pulses) > 0 ])

        # return only finite values in the given cylinder and time interval
        mask = (  (dist < self.max_dist)
                & (tres > self.tw[0]) & (tres < self.tw[1])
                & np.isfinite(dist) & np.isfinite(tres) )

        # put result into frame
        frame[self.i3particle + '_TRes_dT'] = dataclasses.I3VectorDouble(tres[mask])
        frame[self.i3particle + '_TRes_dX'] = dataclasses.I3VectorDouble(dist[mask])
        self.PushFrame(frame)


class I3Vectorize(icetray.I3ConditionalModule):
    '''
    Extend a given frame object to match the length of another vector-like object.

    Written by Stefan Coenders for the 7-year PS sample.
    '''
    def __init__(self, context):
        super(I3Vectorize, self).__init__(context)
        self.AddParameter("Input",  "Name of the input object",                    "")
        self.AddParameter("Func",   "Optional function to apply on input values",  lambda x: x)
        self.AddParameter("Vector", "Corresponding vector object to match length", "")
        self.AddParameter("Output", "Name of the output object",                   "")
        self.AddOutBox("OutBox")

    def Configure(self):
        self.input  = self.GetParameter("Input")
        self.func   = self.GetParameter("Func")
        self.vector = self.GetParameter("Vector")
        self.output = self.GetParameter("Output")

    def Physics(self, frame):
        if (not frame.Has(self.input)) or (not frame.Has(self.vector)):
            self.PushFrame(frame)
            return
        # create output vector with the same
        vec = np.repeat(self.func(frame[self.input]), len(frame[self.vector]))
        frame[self.output] = dataclasses.I3VectorDouble(vec)
        self.PushFrame(frame)



# import needed for RegularGridInterpolator (see explanation below)
import itertools

class RegularGridInterpolator(object):
    """
    Interpolation on a regular grid in arbitrary dimensions.

    This code is copy-and-pasted directly from SciPy 0.16.1.

    The version of SciPy at SPS is 0.7.2, which doesn't provide n-dimensional
    interpolation. Should the version of Scipy at SPS be updated to at least
    0.14 this code can be imported directly from the scipy.interpolate module.
    """

    def __init__(self, points, values, method="linear", bounds_error=True,
                 fill_value=np.nan):
        if method not in ["linear", "nearest"]:
            raise ValueError("Method '%s' is not defined" % method)
        self.method = method
        self.bounds_error = bounds_error

        if not hasattr(values, 'ndim'):
            # allow reasonable duck-typed values
            values = np.asarray(values)

        if len(points) > values.ndim:
            raise ValueError("There are %d point arrays, but values has %d "
                             "dimensions" % (len(points), values.ndim))

        if hasattr(values, 'dtype') and hasattr(values, 'astype'):
            if not np.issubdtype(values.dtype, np.inexact):
                values = values.astype(float)

        self.fill_value = fill_value
        if fill_value is not None:
            fill_value_dtype = np.asarray(fill_value).dtype
            if (hasattr(values, 'dtype')
                    and not np.can_cast(fill_value_dtype, values.dtype,
                                        casting='same_kind')):
                raise ValueError("fill_value must be either 'None' or "
                                 "of a type compatible with values")

        for i, p in enumerate(points):
            if not np.all(np.diff(p) > 0.):
                raise ValueError("The points in dimension %d must be strictly "
                                 "ascending" % i)
            if not np.asarray(p).ndim == 1:
                raise ValueError("The points in dimension %d must be "
                                 "1-dimensional" % i)
            if not values.shape[i] == len(p):
                raise ValueError("There are %d points and %d values in "
                                 "dimension %d" % (len(p), values.shape[i], i))
        self.grid = tuple([np.asarray(p) for p in points])
        self.values = values

    def __call__(self, xi, method=None):
        """
        Interpolation at coordinates
        Parameters
        ----------
        xi : ndarray of shape (..., ndim)
            The coordinates to sample the gridded data at
        method : str
            The method of interpolation to perform. Supported are "linear" and
            "nearest".
        """
        method = self.method if method is None else method
        if method not in ["linear", "nearest"]:
            raise ValueError("Method '%s' is not defined" % method)

        ndim = len(self.grid)
        xi = self._ndim_coords_from_arrays(xi, ndim=ndim)
        if xi.shape[-1] != len(self.grid):
            raise ValueError("The requested sample points xi have dimension "
                             "%d, but this RegularGridInterpolator has "
                             "dimension %d" % (xi.shape[1], ndim))

        xi_shape = xi.shape
        xi = xi.reshape(-1, xi_shape[-1])

        if self.bounds_error:
            for i, p in enumerate(xi.T):
                if not np.logical_and(np.all(self.grid[i][0] <= p),
                                      np.all(p <= self.grid[i][-1])):
                    raise ValueError("One of the requested xi is out of bounds "
                                     "in dimension %d" % i)

        indices, norm_distances, out_of_bounds = self._find_indices(xi.T)
        if method == "linear":
            result = self._evaluate_linear(indices, norm_distances, out_of_bounds)
        elif method == "nearest":
            result = self._evaluate_nearest(indices, norm_distances, out_of_bounds)
        if not self.bounds_error and self.fill_value is not None:
            result[out_of_bounds] = self.fill_value

        return result.reshape(xi_shape[:-1] + self.values.shape[ndim:])

    def _ndim_coords_from_arrays(self, points, ndim=None):
        """
        Convert a tuple of coordinate arrays to a (..., ndim)-shaped array.
        """
        if isinstance(points, tuple) and len(points) == 1:
            # handle argument tuple
            points = points[0]
        if isinstance(points, tuple):
            p = np.broadcast_arrays(*points)
            for j in range(1, len(p)):
                if p[j].shape != p[0].shape:
                    raise ValueError("coordinate arrays do not have the same shape")
            points = np.empty(p[0].shape + (len(points),), dtype=float)
            for j, item in enumerate(p):
                points[...,j] = item
        else:
            points = np.asanyarray(points)
            if points.ndim == 1:
                if ndim is None:
                    points = points.reshape(-1, 1)
                else:
                    points = points.reshape(-1, ndim)
        return points

    def _evaluate_linear(self, indices, norm_distances, out_of_bounds):
        # slice for broadcasting over trailing dimensions in self.values
        vslice = (slice(None),) + (None,)*(self.values.ndim - len(indices))

        # find relevant values
        # each i and i+1 represents a edge
        edges = itertools.product(*[[i, i + 1] for i in indices])
        values = 0.
        for edge_indices in edges:
            weight = 1.
            for ei, i, yi in zip(edge_indices, indices, norm_distances):
                weight *= np.where(ei == i, 1 - yi, yi)
            values += np.asarray(self.values[edge_indices]) * weight[vslice]
        return values

    def _evaluate_nearest(self, indices, norm_distances, out_of_bounds):
        idx_res = []
        for i, yi in zip(indices, norm_distances):
            idx_res.append(np.where(yi <= .5, i, i + 1))
        return self.values[idx_res]

    def _find_indices(self, xi):
        # find relevant edges between which xi are situated
        indices = []
        # compute distance to lower edge in unity units
        norm_distances = []
        # check for out of bounds xi
        out_of_bounds = np.zeros((xi.shape[1]), dtype=bool)
        # iterate through dimensions
        for x, grid in zip(xi, self.grid):
            i = np.searchsorted(grid, x) - 1
            i[i < 0] = 0
            i[i > grid.size - 2] = grid.size - 2
            indices.append(i)
            norm_distances.append((x - grid[i]) /
                                  (grid[i + 1] - grid[i]))
            if not self.bounds_error:
                out_of_bounds += x < grid[0]
                out_of_bounds += x > grid[-1]
        return indices, norm_distances, out_of_bounds


class I3HistogramLLH(icetray.I3ConditionalModule):
    '''
    Use a precalcuated S/B-likelihood histogram to calculate the likelihood ratio
    for each event.
    '''
    def __init__(self, context):
        super(I3HistogramLLH, self).__init__(context)
        # Parameters
        self.AddParameter("HistFile",   "Filename containing the histograms",      "")
        self.AddParameter("VarNames",   "Name of the object(s) with x/y/z values", [])
        self.AddParameter("OutputName", "Where to store the result",               "")
        self.AddOutBox("OutBox")

    def Configure(self):
        self.output      = self.GetParameter('OutputName')
        self.var_names   = self.GetParameter('VarNames')

        # load the histograms from a JSON file
        with open(self.GetParameter('HistFile')) as f:
            hist = json.load(f)

        self.points = [ b[:-1] + 0.5*np.diff(b) for b in hist['bins'] ]
        if 'bounds' in hist:
            self.bounds = [ (float(b[0]), float(b[1])) for b in hist['bounds'] ]
        else:
            self.bounds = [ (min(b), max(b)) for b in hist['bins'] ]
        self.values = hist['ratios']
        self.spline = RegularGridInterpolator(self.points, self.values,
                                              bounds_error=False, fill_value=None)

    def Physics(self, frame):
        # get X/Y/Z variables
        values = []
        for name in self.var_names:
            if not frame.Has(name):
                logging.log_info('Could not find {0:s} in frame! Skipping LLH evaluation.'.format(name))
                self.PushFrame(frame)
                return
            values.append(np.asarray(frame[name]))

        if len(np.unique([ len(arr) for arr in values ])) != 1:
            logging.log_error('X/Y values are not of same length!')
            self.PushFrame(frame)
            return

        values = np.vstack(values)

        # remove out-ouf-bounds values
        if values.shape[1] > 0:
            mask = np.ones(values.shape[1], dtype=np.bool)
            for i, (lo, hi) in enumerate(self.bounds):
                mask &= (lo <= values[i]) & (values[i] <= hi)
            values = values[:,mask]

        # remove non-finite input
        if values.shape[1] > 0:
            m_finite = np.all(np.isfinite(values), axis=0)
            values = values[:, m_finite]

        # evaluate sum of log-likelihoods
        if values.shape[1] > 0:
            llh = self.spline(values.T)
            llh = llh[np.isfinite(llh)]
        else:
            llh = np.asarray([ 0. ])

        # store result in frame
        frame[self.output] = dataclasses.I3MapStringDouble( \
                                {'llh': llh.sum(), 'ndof': float(len(llh))})
        self.PushFrame(frame)



@icetray.traysegment
def GammaFollowUp(tray, name,
        OnlineL2SegmentName = 'OnlineL2',
        BDTUpFile     = None,
        BDTDownFile   = None,
        KeepDetails   = False,
        pulses        = 'CleanedMuonPulses',
        angular_error = True,
        If = lambda f: True):
    """
    This tray segment does the 2017 Gamma-Ray Follow-Up filtering.

    OnlineL2SegmentName is the prefix of the variable names from the OnlineL2
    filter.

    angular_error: Run improved error estimators like Paraboloid or Bootstrapping.
    """

    from icecube import dataclasses
    from icecube import photonics_service, ddddr, paraboloid
    from icecube.filterscripts import filter_globals

    splineMPE_name = OnlineL2SegmentName+'_SplineMPE'
    muex_name      = OnlineL2SegmentName+'_SplineMPE_MuEx'



    def EventHasBasicReco(frame):
        '''
        Decides whether the precuts are passed.
        '''

        # OnlineL2 passed
        if (filter_globals.OnlineL2Filter not in frame) or (not frame[filter_globals.OnlineL2Filter].value):
            return False
        # SplineMPE exists and fit is ok
        if (splineMPE_name not in frame) or (frame[splineMPE_name].fit_status != 0):
            return False
        # MuEx exists and result is ok
        if (muex_name not in frame) or (not np.isfinite(frame[muex_name].energy)) or (frame[muex_name].energy < 10.):
            return False

        return True
    
    def EventIsDowngoing(frame, zenith_cut=math.radians(82.)):
        '''
        Downgoing events passing basic cuts get additional reco using DDDDR and time-residuals.
        '''
        return frame.Has(splineMPE_name) and (frame[splineMPE_name].dir.zenith <= zenith_cut)

    ########################
    # Calculate BDT inputs #
    ########################


    #########
    # DDDDR #
    #########

    def ModifyDDDDROutput(frame, prefix):
        # adjust the slant such that the first bin is always at zero
        slant = prefix+'Slantbinned'
        if slant in frame:
            frame[prefix+'dXbinned'] = dataclasses.I3VectorDouble(frame[slant] - np.amin(frame[slant]))
        return True

    tray.Add('I3MuonEnergy', 'GFU_SplineMPE_DDDDR_150',
            BinWidth       = 50.,
            InputPulses    = pulses,
            MaxImpact      = 150.,
            Method         = -1, # fit not required
            Seed           = splineMPE_name,
            Prefix         = splineMPE_name+'_DDDDR_150_',
            SaveDomResults = True,
            If = lambda f: If(f) and EventHasBasicReco(f) and EventIsDowngoing(f) )

    tray.Add(ModifyDDDDROutput, 'GFU_FixDDDDR_DDDDR_150',
             prefix = splineMPE_name+'_DDDDR_150_',
             If = lambda f: If(f) and EventHasBasicReco(f) and EventIsDowngoing(f) )

    tray.Add(I3Vectorize, 'GFU_SplineMPE_DDDDR_150_vecE',
            Input  = splineMPE_name+'_MuEx',
            Func   = lambda x: np.log10(x.energy),
            Vector = splineMPE_name+'_DDDDR_150_dEdXbinned',
            Output = splineMPE_name+'_DDDDR_150_logE',
            If = lambda f: If(f) and EventHasBasicReco(f) and EventIsDowngoing(f) )

    ##################
    # Time Residuals #
    ##################

    tray.Add(I3TimeResidualBooker, 'GFU_SplineMPE_TResBooker',
            Particle = splineMPE_name,
            Pulsemap = pulses+'IC',
            If = lambda f: If(f) and EventHasBasicReco(f) and EventIsDowngoing(f) )

    tray.Add(I3Vectorize, 'GFU_SplineMPE_TRes_vecE',
            Input  = splineMPE_name+'_MuEx',
            Func   = lambda x: np.log10(x.energy),
            Vector = splineMPE_name+'_TRes_dX',
            Output = splineMPE_name+'_TRes_logE',
            If = lambda f: If(f) and EventHasBasicReco(f) and EventIsDowngoing(f) )

    ###########################
    # Evaluate LLH Histograms #
    ###########################

    tray.Add(I3HistogramLLH, 'GFU_SplineMPE_TResLLH',
            HistFile        = os.path.expandvars("$I3_BUILD/filterscripts/resources/data/hist_tres.json"),
            VarNames        = [ splineMPE_name+'_TRes_dT',
                                splineMPE_name+'_TRes_dX',
                                splineMPE_name+'_TRes_logE' ],
            OutputName      = splineMPE_name+'_TRes_LLH',
            If = lambda f: If(f) and EventHasBasicReco(f) and EventIsDowngoing(f) )

    tray.Add(I3HistogramLLH, 'GFU_SplineMPE_DDDDR_150_LLH',
            HistFile        = os.path.expandvars("$I3_BUILD/filterscripts/resources/data/hist_ddddr150.json"),
            VarNames        = [ splineMPE_name+'_DDDDR_150_dXbinned',
                                splineMPE_name+'_DDDDR_150_dEdXbinned',
                                splineMPE_name+'_DDDDR_150_logE' ],
            OutputName      = splineMPE_name+'_DDDDR_150_LLH',
            If = lambda f: If(f) and EventHasBasicReco(f) and EventIsDowngoing(f) )

    #######
    # BDT #
    #######

    from icecube.pybdtmodule import PyBDTModule
    from os.path import expandvars

    # BDT files
    if (BDTUpFile is None) or (BDTDownFile is None):
        # try to guess the paths
        domain = filter_globals.getDomain()
        if domain == filter_globals.Domain.SPS or domain == filter_globals.Domain.SPTS:
            BDTUpFile   = "/usr/local/pnf/jeb/filterscripts/resources/data/bdt_gfu_up_IC86_2017.bdt"
            BDTDownFile = "/usr/local/pnf/jeb/filterscripts/resources/data/bdt_gfu_down_IC86_2017.bdt"
        else:
            BDTUpFile   = expandvars("$I3_BUILD/filterscripts/resources/data/bdt_gfu_up_IC86_2017.bdt")
            BDTDownFile = expandvars("$I3_BUILD/filterscripts/resources/data/bdt_gfu_down_IC86_2017.bdt")

    def replace_nan(x, val):
        return val if (math.isinf(x) or math.isnan(x)) else x

    def clip(x, low=float('-inf'), high=float('inf')):
        return min(max(x, low), high)        

    def safe_divide(x, y, err_val):
        return replace_nan(x/y, err_val) if (y != 0.) else err_val

    def get_bdt_vars_up(frame):
        var = dict(
                CoG_rhoIC             = replace_nan(
                                          np.sqrt(frame['OnlineL2_HitStatisticsValuesIC'].cog.x**2. \
                                                + frame['OnlineL2_HitStatisticsValuesIC'].cog.y**2.), 600.),
                CoG_zIC               = replace_nan(frame['OnlineL2_HitStatisticsValuesIC'].cog.z, 600.),
                LSepIC                = replace_nan(clip(frame['OnlineL2_SplineMPE_CharacteristicsIC'].track_hits_separation_length, 0., 1500.), 0.),
                BayesLlhDiff          = replace_nan(clip(frame['OnlineL2_BayesianFitFitParams'].logl - frame['OnlineL2_SPE2itFitFitParams'].logl, -100.), -100.),
                cosZen                = math.cos(frame['OnlineL2_SplineMPE'].dir.zenith),
                Plogl3p5              = replace_nan(frame['OnlineL2_SplineMPEFitParams'].logl / \
                                                     (frame['OnlineL2_HitMultiplicityValues'].n_hit_doms - 3.5), 999.),
                LDirCIC               = replace_nan(clip(frame['OnlineL2_SplineMPE_DirectHitsICC'].dir_track_length, 0.), 0.),
                NDirEIC               = frame['OnlineL2_SplineMPE_DirectHitsICE'].n_dir_doms,
                sigma_CramerRao_deg   = replace_nan(clip(math.degrees(
                                            math.sqrt(0.5*(math.pow(frame['OnlineL2_SplineMPE_CramerRaoParams'].cramer_rao_theta, 2.) \
                                                           + math.pow(frame['OnlineL2_SplineMPE_CramerRaoParams'].cramer_rao_phi, 2.) \
                                                            * math.pow(math.sin(frame['OnlineL2_SplineMPE'].dir.zenith), 2.)))), 0., 180.), 180.),
                AbsSmoothnessEIC      = replace_nan(math.fabs(frame['OnlineL2_SplineMPE_DirectHitsICE'].dir_track_hit_distribution_smoothness), 1.),
                AvgDistQtotDomNoCutIC = replace_nan(clip(frame['OnlineL2_SplineMPE_CharacteristicsNoRCutIC'].avg_dom_dist_q_tot_dom, 0., 500.), 500.),
                LEmptyIC              = replace_nan(clip(frame['OnlineL2_SplineMPE_CharacteristicsIC'].empty_hits_track_length, 0., 1500.), 1500.),
                cos_SplineMPE_LF      = math.cos(I3Calculator.angle(frame['OnlineL2_SplineMPE'], frame['PoleMuonLinefit'])),
                Linefit_Speed         = frame['PoleMuonLinefit'].speed,
                logNChIC              = math.log10(clip(frame['OnlineL2_HitMultiplicityValuesIC'].n_hit_doms, 0.1)),
                DiffCosMinSplitZenith = math.cos(np.nanmin([frame['OnlineL2_SplitGeo1_SPE2itFit'].dir.zenith,
                                                            frame['OnlineL2_SplitGeo2_SPE2itFit'].dir.zenith,
                                                            frame['OnlineL2_SplitTime1_SPE2itFit'].dir.zenith,
                                                            frame['OnlineL2_SplitTime2_SPE2itFit'].dir.zenith,
                                                            2.*np.pi])) \
                                         - math.cos(frame['OnlineL2_SplineMPE'].dir.zenith),
            )
        return var


    def get_bdt_vars_down(frame):
        var = dict(
                tres_llh              = frame['OnlineL2_SplineMPE_TRes_LLH']['llh'],
                ddddr150_rllh         = replace_nan(frame['OnlineL2_SplineMPE_DDDDR_150_LLH']['llh'] / frame['OnlineL2_SplineMPE_DDDDR_150_LLH']['ndof'], -30.),
                CoG_rhoIC             = replace_nan(
                                          np.sqrt(frame['OnlineL2_HitStatisticsValuesIC'].cog.x**2. \
                                                + frame['OnlineL2_HitStatisticsValuesIC'].cog.y**2.), 600.),
                CoG_zIC               = replace_nan(frame['OnlineL2_HitStatisticsValuesIC'].cog.z, 600.),
                LDirDIC               = replace_nan(clip(frame['OnlineL2_SplineMPE_DirectHitsICD'].dir_track_length, 0.), 0.),
                NDirEIC               = frame['OnlineL2_SplineMPE_DirectHitsICE'].n_dir_doms,
                sigma_CramerRao_deg   = replace_nan(clip(math.degrees(
                                            math.sqrt(0.5*(math.pow(frame['OnlineL2_SplineMPE_CramerRaoParams'].cramer_rao_theta, 2.) \
                                                           + math.pow(frame['OnlineL2_SplineMPE_CramerRaoParams'].cramer_rao_phi, 2.) \
                                                            * math.pow(math.sin(frame['OnlineL2_SplineMPE'].dir.zenith), 2.)))), 0., 180.), 180.),
                SplineMPE_rlogl       = replace_nan(frame['OnlineL2_SplineMPEFitParams'].rlogl, 999.),
                LSepIC                = replace_nan(clip(frame['OnlineL2_SplineMPE_CharacteristicsIC'].track_hits_separation_length, 0., 1500.), 0.),
                q_early_dirA_ratio    = safe_divide(frame['OnlineL2_SplineMPE_DirectHitsA'].q_early_pulses, frame['OnlineL2_SplineMPE_DirectHitsA'].q_dir_pulses, 1.),
                q_max_tot_ratioIC     = math.log10(safe_divide(frame['OnlineL2_HitStatisticsValuesIC'].q_max_doms, frame['OnlineL2_HitStatisticsValuesIC'].q_tot_pulses, 1.)),
                MuEx_r                = frame['OnlineL2_SplineMPE_MuEx_r'].value,
                cosZen                = math.cos(frame['OnlineL2_SplineMPE'].dir.zenith),
                DiffCosMaxSplitZenith = math.cos(frame['OnlineL2_SplineMPE'].dir.zenith) - \
                                        math.cos(np.nanmax([frame['OnlineL2_SplitGeo1_SPE2itFit'].dir.zenith,
                                                            frame['OnlineL2_SplitGeo2_SPE2itFit'].dir.zenith,
                                                            frame['OnlineL2_SplitTime1_SPE2itFit'].dir.zenith,
                                                            frame['OnlineL2_SplitTime2_SPE2itFit'].dir.zenith,
                                                            -np.pi])),
            )
        return var


    def EventPassesUpgoingPrecuts(frame):

        if ('OnlineL2_SplineMPE_CramerRaoParams' not in frame) or (frame['OnlineL2_SplineMPE_CramerRaoParams'].status != 0):
            return False
        if ('OnlineL2_BayesianFitFitParams' not in frame):
            return False

        var = get_bdt_vars_up(frame)
        if frame['OnlineL2_SplineMPE_MuEx'].energy                                   <= 10.:  return False
        if var['BayesLlhDiff']                                                       <= 20.:  return False
        if var['Plogl3p5']                                                           >= 10.:  return False
        if var['AvgDistQtotDomNoCutIC']                                              >= 250.: return False
        if frame['OnlineL2_HitMultiplicityValuesIC'].n_hit_doms                      <  6:    return False
        if var['NDirEIC']                                                            <  6:    return False
        if np.fabs(replace_nan(frame['OnlineL2_HitStatisticsValuesIC'].cog.z, 600.)) >= 500.: return False
        if var['sigma_CramerRao_deg']                                                >= 25.:  return False
        if var['Linefit_Speed']                                                      >= 3.:   return False
        if var['LSepIC']                                                             <= 50.:  return False
        if var['LDirCIC']                                                            <= 75.:  return False
        if var['LEmptyIC']                                                           >= 600.: return False
        if var['cos_SplineMPE_LF']                                                   <= 0.5:  return False

        return True


    def EventPassesDowngoingPrecuts(frame):

        if ('OnlineL2_SplineMPE_CramerRaoParams' not in frame) or (frame['OnlineL2_SplineMPE_CramerRaoParams'].status != 0):
            return False
        if ('OnlineL2_SplineMPE_DDDDR_150_LLH' not in frame):
            return False
        if ('OnlineL2_SplineMPE_TRes_LLH' not in frame):
            return False

        var = get_bdt_vars_down(frame)
        if math.log10(frame['OnlineL2_SplineMPE_MuEx'].energy)                                                 <= 2.5:   return False
        if replace_nan(clip(frame['OnlineL2_HitMultiplicityValuesIC'].n_hit_strings,    low=0.), 0)            <  7:     return False
        if replace_nan(clip(frame['OnlineL2_SplineMPE_DirectHitsICE'].dir_track_length, low=0.), 0.)           <= 250.:  return False
        if var['NDirEIC']                                                                                      <  12:    return False
        if var['SplineMPE_rlogl']                                                                              >= 10.:   return False
        if var['sigma_CramerRao_deg']                                                                          >= 10.:   return False
        if var['CoG_rhoIC']                                                                                    >= 540.:  return False
        if math.fabs(replace_nan(frame['OnlineL2_HitStatisticsValuesIC'].cog.z, 600.))                         >  480.:  return False
        if var['LSepIC']                                                                                       <= 75.:   return False
        if var['q_max_tot_ratioIC']                                                                            >= -0.2:  return False
        if math.cos(I3Calculator.angle(frame['OnlineL2_SplineMPE'], frame['PoleMuonLinefit']))                 <= 0.73:  return False
        if ('OnlineL2_SplineMPE_DDDDR_150_LLH' not in frame) or (frame['OnlineL2_SplineMPE_DDDDR_150_LLH']['ndof'] < 2): return False
        if var['ddddr150_rllh']                                                                                <= -0.14: return False
        if ('OnlineL2_SplineMPE_TRes_LLH' not in frame) or (frame['OnlineL2_SplineMPE_TRes_LLH']['ndof'] < 14):          return False
        if var['tres_llh']                                                                                     <= -11.:  return False
        if math.fabs(frame['OnlineL2_SplineMPE_MuEx_r'].value - 1.)                                            >= 0.5:   return False

        return True


    # run upgoing BDT
    tray.AddModule(PyBDTModule, name+"_BDT_Up",
            BDTFilename = BDTUpFile,
            varsfunc    = get_bdt_vars_up,
            OutputName  = name+'_BDT_Score_Up',
            UsePurity   = True,
            If          = lambda f: If(f) and EventHasBasicReco(f) and (not EventIsDowngoing(f)) and EventPassesUpgoingPrecuts(f)
        )

    # run downgoing BDT
    tray.AddModule(PyBDTModule, name+"_BDT_Down",
            BDTFilename = BDTDownFile,
            varsfunc    = get_bdt_vars_down,
            OutputName  = name+'_BDT_Score_Down',
            UsePurity   = False,
            If          = lambda f: If(f) and EventHasBasicReco(f) and EventIsDowngoing(f) and EventPassesDowngoingPrecuts(f)
        )


    def ApplyBDTCut(frame):
        """
        Select events based on the BDT score.
        """
        if frame.Has(name+'_BDT_Score_Up'):
            score  = frame[name+'_BDT_Score_Up'].value
            coszen = math.cos(frame['OnlineL2_SplineMPE'].dir.zenith)
            if coszen < 0.:
                cut = -0.125
            elif coszen < 0.1:
                cut = np.interp(coszen, [0.0, 0.1],  [-0.125, -0.161])
            else:
                cut = np.interp(coszen, [0.1, 0.14], [-0.161, -0.161])

        elif frame.Has(name+'_BDT_Score_Down'):
            score  = frame[name+'_BDT_Score_Down'].value
            coszen = math.cos(frame['OnlineL2_SplineMPE'].dir.zenith)
            if coszen > 0.39:
                cut = -0.7
            elif coszen > 0.22:
                cut = np.interp(coszen, [0.22, 0.39], [-0.6723, -0.7])
            else:
                cut = np.polyval([ -7101.97681, 13756.69027, -10824.05662, 4418.69708, -984.41389, 112.85935, -5.83447 ], coszen)
        else:
            score = 0.
            cut   = 1.

        frame[name+'_Passed'] = icetray.I3Bool(score > float(cut))


    tray.Add(ApplyBDTCut, If = lambda f: If(f) and EventHasBasicReco(f))


    def EventPassedGFUFilter(frame):
        """
        Returns True, if the BDT cut was passed.
        """
        if frame.Has(name+'_Passed'):
            return frame[name+'_Passed'].value
        else:
            return False

    def EventIsLowNChannel(frame, nchCut=300):
        hitMultName = OnlineL2SegmentName+'_HitMultiplicityValues'
        return frame.Has(hitMultName) and (frame[hitMultName].n_hit_doms < nchCut)

    def EventIsLowEnergetic(frame, energyCut=4000.):
        muexName = OnlineL2SegmentName+'_BestFit_MuEx'
        return frame.Has(muexName) and (frame[muexName].energy < energyCut)

    def RunParaboloid(frame):
        return EventPassedGFUFilter(frame) and EventIsLowEnergetic(frame)

    def RunBootstrapping(frame):
        return EventPassedGFUFilter(frame) and (not EventIsLowEnergetic(frame)) \
                                           and EventIsLowNChannel(frame)


    # actual filter decision
    tray.AddModule("I3FilterModule<I3BoolFilter>", name+"_GFUFilter2017",
            DiscardEvents = False,
            Boolkey       = name+'_Passed',
            DecisionName  = filter_globals.GFUFilter,
            If = lambda f: If(f) and EventHasBasicReco(f)
        )

    # better error estimation
    if angular_error:
        from icecube import lilliput
        from icecube.filterscripts.onlinel2filter import SplineMPEParaboloid, SplineMPEBootstrapping

        mininame = lilliput.segments.add_minuit_simplex_minimizer_service(tray)
        paraname = lilliput.segments.add_simple_track_parametrization_service(tray)

        tray.AddSegment(SplineMPEParaboloid, OnlineL2SegmentName,
                pulses=pulses, MinimizerName=mininame,
                If = lambda f: If(f) and RunParaboloid(f))

        tray.AddSegment(SplineMPEBootstrapping, OnlineL2SegmentName,
                pulses=pulses, ParametrizationName=paraname,
                MinimizerName=mininame,
                If = lambda f: If(f) and RunBootstrapping(f))

    
    tray.AddModule("Delete", name+"_Delete_GFU_Leftovers",
            Keys = [ name+'_Passed',
                     splineMPE_name+'_DDDDR_150_Depthbinned',
                     splineMPE_name+'_DDDDR_150_Slantbinned',
                     splineMPE_name+'_DDDDR_150_logE',
                     splineMPE_name+'_DDDDR_150_dXbinned',
                     splineMPE_name+'_DDDDR_150_dEdXbinned',
                     splineMPE_name+'_DDDDR_150_dEdX_errbinned',
                     splineMPE_name+'_DDDDR_150_CascadeParams',
                     splineMPE_name+'_DDDDR_150_Params',
                     splineMPE_name+'_TRes_dT',
                     splineMPE_name+'_TRes_dX',
                     splineMPE_name+'_TRes_logE',
                     splineMPE_name+'_DDDDR_150_LLH',
                     splineMPE_name+'_TRes_LLH',
                   ],
            If = lambda f: If(f) and EventHasBasicReco(f) and (not EventPassedGFUFilter(f))
        )

    filter_globals.gfufilter_keeps += [
            filter_globals.GFUFilter,
            name+'_BDT_Score_Up',
            name+'_BDT_Score_Down',
        ]

    if angular_error:
        filter_globals.gfufilter_keeps += [
                splineMPE_name+"_Bootstrap",
                splineMPE_name+"_BootstrapFitParams",
                splineMPE_name+"_BootstrapVect",
                splineMPE_name+"_Bootstrap_Angular",
                splineMPE_name+"_Paraboloid",
                splineMPE_name+"_ParaboloidFitParams",
                ]


    filter_globals.gfufilter_keeps += [
        splineMPE_name+'_DDDDR_150_CascadeParams',
        splineMPE_name+'_DDDDR_150_Params',
        splineMPE_name+'_DDDDR_150_LLH',
        splineMPE_name+'_TRes_LLH',
    ]

    if KeepDetails:
        filter_globals.gfufilter_keeps += [
            #splineMPE_name+'_DDDDR_150_Depthbinned',
            #splineMPE_name+'_DDDDR_150_Slantbinned',
            splineMPE_name+'_DDDDR_150_logE',
            splineMPE_name+'_DDDDR_150_dXbinned',
            splineMPE_name+'_DDDDR_150_dEdXbinned',
            #splineMPE_name+'_DDDDR_150_dEdX_errbinned',
            splineMPE_name+'_TRes_dT',
            splineMPE_name+'_TRes_dX',
            splineMPE_name+'_TRes_logE',
        ]

