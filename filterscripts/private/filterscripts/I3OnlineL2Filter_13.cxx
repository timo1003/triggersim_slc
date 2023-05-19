#include "filterscripts/I3OnlineL2Filter_13.h"

#include <cmath>

#include "filterscripts/I3FilterModule.h"
#include "dataclasses/physics/I3Particle.h"
#include "recclasses/I3DirectHitsValues.h"
#include "recclasses/I3HitMultiplicityValues.h"
#include "recclasses/I3HitStatisticsValues.h"
#include "gulliver/I3LogLikelihoodFitParams.h"
#include "dataclasses/I3Constants.h"

I3_MODULE(I3FilterModule<I3OnlineL2Filter_13>);

I3OnlineL2Filter_13::I3OnlineL2Filter_13(const I3Context& context) : I3JEBFilter(context) {

    pri_particlekey_ = "OnlineL2_BestFit";
    AddParameter("PriParticleKey",
            "Name of the I3Particle in the frame (source for zenith angle).",
            pri_particlekey_);

    direct_hit_values_ = "OnlineL2_BestFitDirectHitsC";
    AddParameter("DirectHitValues",
                "Name of the I3DirectHitsValues calculated with CommonVariables (source for NDir and LDir).",
                direct_hit_values_);

    hit_multiplicity_values_ = "OnlineL2_HitMultiplicityValues";
    AddParameter("HitMultiplicityValues",
                "Name of the I3HitMultiplicityValues calculated with CommonVariables (source for NCh).",
                hit_multiplicity_values_);

    hit_statistics_values_ = "OnlineL2_HitStatisticsValues";
    AddParameter("HitStatisticsValues",
                "Name of the I3HitMultiplicityValues calculated with CommonVariables (source for NCh).",
                hit_statistics_values_);

    llh_paramskey_ = "PoleMuonLlhFitFitParams";
    AddParameter("LLHFitParamsKey",
            "Name of the LLH Fit Params key in the frame (source for logl).",
            llh_paramskey_);

    cos_zenith_zone1_.push_back(-1.);
    cos_zenith_zone1_.push_back(std::cos(82.*I3Constants::pi/180.));

    cos_zenith_zone2_.push_back(std::cos(82.*I3Constants::pi/180.));
    cos_zenith_zone2_.push_back(std::cos(66.*I3Constants::pi/180.));

    cos_zenith_zone3_.push_back(std::cos(66.*I3Constants::pi/180.));
    cos_zenith_zone3_.push_back(1.);

    AddParameter("CosZenithZone1",
            "Vector with minimum and maximum cos zenith angle of Zone 1 where the PLogL || NDirC || LDirC || QTot cut is applied.",
            cos_zenith_zone1_);

    AddParameter("CosZenithZone2",
            "Vector with minimum and maximum cos zenith angle of Zone 2 where the first QTot || (PLogL && QTot) cut is applied.",
            cos_zenith_zone2_);

    AddParameter("CosZenithZone3",
            "Vector with minimum and maximum cos zenith angle of Zone 3 where the second QTot || (PLogL && QTot) cut is applied.",
            cos_zenith_zone3_);

    // cut values:
    ldirc_zone1_ = 160.;
    AddParameter("LDirCZone1",
            "Denominator for LDirC for ellipsis cut in Zone 1.",
            ldirc_zone1_);

    ndirc_zone1_ = 9;
    AddParameter("NDirCZone1",
            "Denominator for NDirC for ellipsis cut in Zone 1.",
            ndirc_zone1_);

    plogl_param_zone1_ = 4.5;
    AddParameter("PLogLParamZone1",
            "Number subtracted from NCh in plogl for Zone 1.",
            plogl_param_zone1_);

    plogl_zone1_ = 8.3;
    AddParameter("PLogLZone1",
            "Max value of plogl = loglikelihood/(nch - ploglparam) for Zone 1.",
            plogl_zone1_);

    qtot_zone1_ = 2.7;
    AddParameter("QTotZone1",
            "Min value of log10(QTot) for Zone 1.",
            qtot_zone1_);    

    qtot_slope_zone2_ = 3.3;
    AddParameter("QTotSlopeZone2",
                "Slope of cos(Zenith) dependent QTot cut for Zone 2 (before kink).",
                qtot_slope_zone2_);

    qtot_intercept_zone2_ = 1.05 + 0.08;
    AddParameter("QTotInterceptZone2",
                "Intercept of cos(Zenith) dependent QTot cut for Zone 2.",
                qtot_intercept_zone2_);

    plogl_param_zone2_ = 4.5;
    AddParameter("PLogLParamZone2",
            "Number subtracted from NCh in plogl for Zone 2.",
            plogl_param_zone2_);

    plogl_zone2_ = 8.3;
    AddParameter("PLogLZone2",
            "Max value of plogl = loglikelihood/(nch - ploglparam) for Zone 2.",
            plogl_zone2_);

    qtot_or_cut_zone2_ = 2.5;
    AddParameter("QTotOrCutZone2",
            "Min value of log10(QTot) for Zone 2.",
            qtot_or_cut_zone2_);

    qtot_kink_zone3_ = 0.5;
    AddParameter("QTotKinkZone3",
            "Value of cos(Zenith) where (in Zone 3) there is a kink in the QTot cut.",
            qtot_kink_zone3_);

    qtot_slope_zone3_ = 0.6;
    AddParameter("QTotSlopeZone3",
            "Slope of cos(Zenith) dependent QTot cut for Zone 3 (after kink).",
            qtot_slope_zone3_);

    qtot_intercept_zone3_ = 2.4 + 0.13;
    AddParameter("QTotInterceptZone3",
            "Intercept of cos(Zenith) dependent QTot cut for Zone 3.",
            qtot_slope_zone3_);

    plogl_param_zone3_ = 4.5;
    AddParameter("PLogLParamZone3",
            "Number subtracted from NCh in plogl for Zone 3.",
            plogl_param_zone3_);

    plogl_zone3_ = 10.5;
    AddParameter("PLogLZone3",
            "Max value of plogl = loglikelihood/(nch - ploglparam) for Zone 3.",
            plogl_zone3_);

    qtot_or_cut_zone3_ = 3.0;
    AddParameter("QTotOrCutZone3",
            "Min value of log10(QTot) for Zone 3.",
            qtot_or_cut_zone3_);

}

void I3OnlineL2Filter_13::Configure() {
    // stuff to get from frame
    GetParameter("PriParticleKey",pri_particlekey_);
    GetParameter("DirectHitValues",direct_hit_values_);
    GetParameter("HitMultiplicityValues",hit_multiplicity_values_);
    GetParameter("HitStatisticsValues",hit_statistics_values_);
    GetParameter("LLHFitParamsKey",llh_paramskey_);
    // cut regions:
    GetParameter("CosZenithZone1",cos_zenith_zone1_);
    GetParameter("CosZenithZone2",cos_zenith_zone2_);
    GetParameter("CosZenithZone3",cos_zenith_zone3_);
    // cut values:
    GetParameter("LDirCZone1",ldirc_zone1_);
    GetParameter("NDirCZone1",ndirc_zone1_);
    GetParameter("PLogLParamZone1",plogl_param_zone1_);
    GetParameter("PLogLZone1",plogl_zone1_);
    GetParameter("QTotZone1",qtot_zone1_);
    GetParameter("QTotSlopeZone2",qtot_slope_zone2_);
    GetParameter("QTotInterceptZone2",qtot_intercept_zone2_);
    GetParameter("PLogLParamZone2",plogl_param_zone2_);
    GetParameter("PLogLZone2",plogl_zone2_);
    GetParameter("QTotOrCutZone2",qtot_or_cut_zone2_);
    GetParameter("QTotKinkZone3",qtot_kink_zone3_);
    GetParameter("QTotSlopeZone3",qtot_slope_zone3_);
    GetParameter("QTotInterceptZone3",qtot_intercept_zone3_);
    GetParameter("PLogLParamZone3",plogl_param_zone3_);
    GetParameter("PLogLZone3",plogl_zone3_);
    GetParameter("QTotOrCutZone3",qtot_or_cut_zone3_);

    qtot_offset_zone3_ = (qtot_slope_zone3_*qtot_kink_zone3_ + qtot_intercept_zone3_) - (qtot_slope_zone2_*qtot_kink_zone3_ + qtot_intercept_zone2_);
            // how much higher/lower is the line in zone3 w.r.t. zone2 (difference of line height at kink)
}

bool I3OnlineL2Filter_13::KeepEvent(I3Frame& frame) {
    ////////////////////
    // Getting Stuff
    ////////////////////
    // check if frame has all we need, then get it:
    if ( ! frame.Has(pri_particlekey_) ) {
        log_warn("Event does not have ParticleKey %s, discarding it.", pri_particlekey_.c_str());
        return false; //reject
    }
    const I3Particle& particle = frame.Get<I3Particle>(pri_particlekey_);
    const double cosZen = std::cos(particle.GetZenith());
    if (particle.GetFitStatus() != I3Particle::OK) {
        log_warn("Primary particle fit %s did not succeed. Ignoring event.", pri_particlekey_.c_str());
        return false; // reject
    }
    log_trace("Event has cos(zenith) of %f", cosZen);
    if ( ! frame.Has(direct_hit_values_) ) {
        log_warn("Event does not have I3DirectHitsValues %s, discarding it.", direct_hit_values_.c_str());
        return false; //reject
    }
    const I3DirectHitsValues& directhitvalues = frame.Get<I3DirectHitsValues>(direct_hit_values_);
    const unsigned int ndirc = directhitvalues.GetNDirDoms();
    const double ldirc = directhitvalues.GetDirTrackLength();
    if ( ! frame.Has(hit_multiplicity_values_) ) {
        log_warn("Event does not have I3HitMultiplicityValues %s, discarding it.", hit_multiplicity_values_.c_str());
        return false; //reject
    }
    const I3HitMultiplicityValues& hitmultiplicityvalues = frame.Get<I3HitMultiplicityValues>(hit_multiplicity_values_);
    const unsigned int nch = hitmultiplicityvalues.GetNHitDoms();
    if (nch < 5) { // this would make problems in plogl
        log_debug("Event has only %d hits (less than 5), rejecting event.", nch);
        return false; //reject
    }
    if ( ! frame.Has(hit_statistics_values_) ) {
        log_warn("Event does not have I3HitStatisticsValues %s, discarding it.", hit_statistics_values_.c_str());
        return false; //reject
    }
    const I3HitStatisticsValues& hitstatisticsvalues = frame.Get<I3HitStatisticsValues>(hit_statistics_values_);
    const double qtot = hitstatisticsvalues.GetQTotPulses();
    const double logqtot = std::log10(qtot);
    log_trace("Event has %d hit channels and a log10 total charge of %f", nch, logqtot);
    if ( ! frame.Has(llh_paramskey_) ) {
        log_warn("Event does not have FitParams %s, discarding it.", llh_paramskey_.c_str());
        return false; //reject
    }
    const I3LogLikelihoodFitParams& llhparams = frame.Get<I3LogLikelihoodFitParams>(llh_paramskey_);
    const double logl = llhparams.logl_;

    ////////////////////
    // The Cuts
    ////////////////////
    // zenith region AB:
    if ( cos_zenith_zone1_[0] <= cosZen  &&  cosZen <= cos_zenith_zone1_[1] ) {
        const double ellipsis = std::pow(ldirc/ldirc_zone1_,2) + std::pow(double(ndirc)/ndirc_zone1_,2);
        const double plogl = logl / (nch - plogl_param_zone1_);
        if ( logqtot >= qtot_zone1_ || ellipsis >= 1. || plogl <= plogl_zone1_ ) {
            log_trace("Keeping event: cos(zenith) = %f, logqtot = %f, ndirc = %i, ldirc = %f, ellipsis = %f, plogl = %f", cosZen, logqtot, ndirc, ldirc, ellipsis, plogl);
            return true;
        }
    }
    // zenith region C:
    if ( cos_zenith_zone2_[0] < cosZen  &&  cosZen <= cos_zenith_zone2_[1] ) {
        const double plogl = logl / (nch - plogl_param_zone2_);
        const double qtotcut = qtot_slope_zone2_*cosZen + qtot_intercept_zone2_;
        if ( logqtot >= qtot_or_cut_zone2_ || ( plogl <= plogl_zone2_ && logqtot >= qtotcut ) ) {
            log_trace("Keeping event: cos(zenith) = %f, plogl = %f, logqtot = %f, qtotcut = %f", cosZen, plogl, logqtot, qtotcut);
            return true;
        }
    }
    // zenith region D:
    if ( cos_zenith_zone3_[0] < cosZen  &&  cosZen <= cos_zenith_zone3_[1] ) {
        const double plogl = logl / (nch - plogl_param_zone3_);
        double qtotcut = 0.;
        if ( cosZen <= qtot_kink_zone3_ ) qtotcut = qtot_slope_zone2_*cosZen + qtot_intercept_zone2_ + qtot_offset_zone3_; // still slope from zone 2 (before kink)
        else if ( cosZen > qtot_kink_zone3_ ) qtotcut = qtot_slope_zone3_*cosZen + qtot_intercept_zone3_; // slope from zone 3 (after kink)
        if ( logqtot >= qtot_or_cut_zone3_ || ( plogl <= plogl_zone3_ && logqtot >= qtotcut ) ) {
            log_trace("Keeping event: cos(zenith) = %f, plogl = %f, logqtot = %f, qtotcut = %f", cosZen, plogl, logqtot, qtotcut);
            return true;
        }
    }
    // if control reaches end of function, then event didn't pass the cuts -> discard event
    return false;
}

void I3OnlineL2Filter_13::Finish() {
}
