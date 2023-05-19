/**
 * @class I3FSSFilter_13
 * $Id$
 * $Date$
 * $Revison$
 *
 * Full Sky Starting Filter (FSSFilter): finiteReco based event selection on 
 * candidate events from FSSCandidate. This module can be used to cut on the I3Position of
 * an I3Particle. The possible cuts are on the z-ccordinate (z<zCut),
 * the radius OR whether the point is inside a scalable polygon, defined
 * by a list of string numbers. In case of a scaled polygon or the radius,
 * the user can also define if the center of scaling is (0,0) or string 36.
 *
 * The IsInsidePolygon() method is kind of stolen from ROOT (TMath::IsInside() )
 * see: http://root.cern.ch/root/html526/src/TMath.h.html#vuXOW
 * Author: Rickard Strom
 * Institut IIIB
 * RWTH Aachen University
 * E-mail: rickard.strom@physics.uu.se
 */
#ifndef I3FSSFILTER13__H
#define I3FSSFILTER13__H

#include <filterscripts/I3JEBFilter.h>
#include <dataclasses/physics/I3Particle.h>
#include <dataclasses/geometry/I3Geometry.h>
#include <string>
#include <vector>

class I3FSSFilter_13 : public I3JEBFilter {

    public:

        I3FSSFilter_13(const I3Context&);
        ~I3FSSFilter_13(){}
        void Configure();
        bool KeepEvent(I3Frame& frame);
        void Finish();

        SET_LOGGER("I3FSSFilter_13");

    private:
	
	/**
	* This method checks, if the reconstructed start point is within the defined polygon.
	*/
	bool IsInsidePolygon();

        // configurable parameters
	/**
	* Name of the finite particle in the frame.
	*/
        std::string finiteRecoParticleName_;
	/**
	* Z-Value for the fiduical volume cut.
	*/
	double zCut_;
	/**
	* If useGeometryCut_ is set to false, a simple cut on the radius will be applied.
	*/
	double rCut_;
	/**
	* This bool defines, whether a simple radius cut will be performed or a polygon cut.
	*/
	bool usePolygonCut_;
	/**
	* This bool determines, whether you scale the polygon w.r.t. the center of the coordiante system or string 36.
	*/
	bool scaleAroundString36_;
	/**
	* It is possible to scale the polygon area with this parameter. Should be [0,1]
	*/
	double polygonCutScale_;
	/// X-coordinate of the point around which the polygon is scaled
	double offsetX_;
	/// Y-coordinate of the point around which the polygon is scaled
	double offsetY_;

        /// total # of events
	unsigned int nSeen_;
	/// # of kept events
        unsigned int nKept_;
	/// # of events which have been rejected due to a bad or missing fit
  	unsigned int rejectedBadFit_;
	/// # of events which have been rejected due to a too high z position
	unsigned int rejectedZ_;
	/// # of events which have been rejected because they are outside the defined radius
	unsigned int rejectedR_;
	/// # of events which did not pass the polygon-based cut
	unsigned int rejectedPoly_;
	/// X values of corner points of the polygon (calculated automatically)
	std::vector<double> polygonCornersX_;
	/// Y values of corner points of the polygon (calculated automatically)
	std::vector<double> polygonCornersY_;

	/// Name of the finite reco particle
        I3ParticleConstPtr finiteRecoParticlePtr_;
	/// Geometry Pointer
	I3GeometryConstPtr geometry_;
	/// OMGeo Pointer
	I3OMGeoMapConstPtr omMap_;
};

#endif /* I3FSSFILTER13__H */
