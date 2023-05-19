#include <filterscripts/I3FSSFilter_13.h>
#include <filterscripts/I3FilterModule.h>
I3_MODULE(I3FilterModule<I3FSSFilter_13>);

#include <icetray/I3Units.h>

I3FSSFilter_13::I3FSSFilter_13(const I3Context& context) :
    I3JEBFilter(context),
    zCut_(1000.*I3Units::m),
    rCut_(700.*I3Units::m),
    usePolygonCut_(false),
    scaleAroundString36_(true),
    polygonCutScale_(1.),
    offsetX_(46.290000915527344*I3Units::m), // coordinates of string 36
    offsetY_(-34.880001068115234*I3Units::m),
    nSeen_(0),
    nKept_(0),
    rejectedBadFit_(0),
    rejectedZ_(0),
    rejectedR_(0),
    rejectedPoly_(0)
{
    AddParameter( "finiteRecoParticleName",
                 "Name of the I3Particle from the finteReco start/stop point reconstruction.",
                 finiteRecoParticleName_ );
    AddParameter( "zCut",
                 "Z-coordinate for the vertex cut [m]. Events with a reconstructed z-position below zCut are discarded.",
                 zCut_ );
    AddParameter( "rCut",
                 "Radius for the vertex cut [m].",
                 rCut_ );
    AddParameter( "usePolygonCut",
                 "Defines if a cut is applied on the radius or a polygon area, following the detector geometry",
                 usePolygonCut_ );
    AddParameter( "polygonCutScale",
                 "In case of the polygon-based cut on the x-y position, this is the scale factor "
		 "by which the polygon is scaled to smaller sizes."
		 "It should be a value ranging from 0 to 1.",
                 polygonCutScale_ );
    AddParameter( "scaleAroundString36",
                  "This bool determines, whether you scale the polygon w.r.t. the center of the coordiante system or string 36.",
                  scaleAroundString36_);
}

void I3FSSFilter_13::Configure(){

    GetParameter( "finiteRecoParticleName", finiteRecoParticleName_ );
    GetParameter( "zCut" , zCut_ );
    GetParameter( "rCut" , rCut_ );
    GetParameter( "usePolygonCut" , usePolygonCut_ );
    GetParameter( "polygonCutScale" , polygonCutScale_);
    GetParameter( "scaleAroundString36" , scaleAroundString36_);

    if( finiteRecoParticleName_.empty() ){
      log_fatal("(%s) You have to configure the name of the finiteReco particle!", GetName().c_str());
    }

    if( !usePolygonCut_ && (rCut_ > 700.*I3Units::m) ){
        log_warn("(%s) This radius cut value will not cut anything...", GetName().c_str());
    }
    if( !usePolygonCut_ && (rCut_ < 0.*I3Units::m) ){
        log_fatal("(%s) The configured cut radius should be positive!", GetName().c_str());
    }
 
    if( zCut_>= 1000*I3Units::m ){
        log_debug("(%s) Z-Cut value is set to the default value of 1000m or larger, nothing much to cut there.", GetName().c_str());
    }

    if( polygonCutScale_>1. ){
        log_debug("(%s) You are inflating the defined polygon area. Are you sure about this?", GetName().c_str());
    }
    else if( polygonCutScale_<0){
        log_fatal("(%s) You can't scale the volume with a negative number.", GetName().c_str());
	
    }
    if( !scaleAroundString36_ ){
        offsetX_=0;
        offsetY_=0;
    }
    return;
}

// Lists of corner strings for ic79 and ic86
std::vector<int> ic79Corners = std::vector<int>({2,6,50,74,72,78,75,41});
std::vector<int> ic86Corners = std::vector<int>({1,6,50,74,72,78,75,31});


// GC filter: keep or reject
bool I3FSSFilter_13::KeepEvent(I3Frame& frame){
    ++nSeen_;
    //get geometry, has to be here, because Configure() does not get a frame
    if( !geometry_ && usePolygonCut_){
        if( frame.Has(I3DefaultName<I3Geometry>::value()) ){
            geometry_ = frame.Get<I3GeometryConstPtr>();
            if( !geometry_){
                log_fatal("(%s) No geometry found", GetName().c_str());
            }
            const I3OMGeoMapConstPtr omMap = I3OMGeoMapConstPtr( new I3OMGeoMap(geometry_->omgeo) ); //sucks
            if( !omMap){
                log_fatal("(%s) I3OMGeo not found", GetName().c_str());
            }
            // We're IC86 if the geometry contains all of the ic86 corners
            std::vector<int> corners = ic86Corners;
            for (auto strPtr = corners.begin();
                      strPtr != corners.end(); ++strPtr) {
              if (omMap->find(OMKey(*strPtr, 1)) == omMap->end()) {
                // Oops, use IC79 instead
                corners = ic79Corners;
                log_debug("Using IC79 Corners");
                break;
              }
            }
            for (auto vIter = corners.begin();
                     vIter != corners.end(); ++vIter ) {
                const OMKey thisOM(*vIter, 1);
                const I3OMGeoMap::const_iterator omKeyOMGeoPair = omMap->find(thisOM);
                if( omKeyOMGeoPair != omMap->end() ){
                    polygonCornersX_.push_back( offsetX_+   polygonCutScale_*(omKeyOMGeoPair->second.position.GetX()-offsetX_) );
                    polygonCornersY_.push_back( offsetY_+   polygonCutScale_*(omKeyOMGeoPair->second.position.GetY()-offsetY_) );
                }
                else{
                    log_fatal("(%s) DOM %s not found in geometry.", GetName().c_str(), thisOM.str().c_str());
                }
            }
            polygonCornersX_.push_back(polygonCornersX_[0]); // First and last point in the vector has to be identical for isInsidePolygon()
            polygonCornersY_.push_back(polygonCornersY_[0]);
        }
        else{
            log_fatal("(%s) No Geometry found.", GetName().c_str());
        }
    }
    

    // check fit
    finiteRecoParticlePtr_ = frame.Get<I3ParticleConstPtr>( finiteRecoParticleName_ );
    bool finiteRecoFitOK = (finiteRecoParticlePtr_ && (finiteRecoParticlePtr_->GetFitStatus() == I3Particle::OK ));
    if (!finiteRecoFitOK){
        log_debug("(%s) FiniteReco particle missing or the reconstruction did not succeed", GetName().c_str());
	rejectedBadFit_ ++;
	return false;	
    }
    double vertexZ = finiteRecoParticlePtr_->GetZ();
    if ( vertexZ > zCut_ ){
	log_debug("(%s) Rejected due to too high z coordinate of the vertex.", GetName().c_str());
	rejectedZ_ ++;
	return false;
    }
    if ( usePolygonCut_ ){
	if (!IsInsidePolygon()){
            log_debug("(%s) Rejected due to vertex being outside the defined hexagon cut.", GetName().c_str());
	    rejectedPoly_ ++;
	    return false;
	}
    }
    else{
	const double vertexX = finiteRecoParticlePtr_->GetX();
	const double vertexY = finiteRecoParticlePtr_->GetY();
	const double vRadiusSqr = (vertexX-offsetX_)*(vertexX-offsetX_)+(vertexY-offsetY_)*(vertexY-offsetY_);
    	if ( vRadiusSqr > (rCut_ * rCut_) ){
	    log_debug("(%s) Rejected due to too large radius of the vertex.", GetName().c_str());
	    rejectedR_ ++;
	    return false;
	}
    }

    ++nKept_;
    //log_debug("(%s) This event has been kept. ", GetName().c_str());
    return true;
}

bool I3FSSFilter_13::IsInsidePolygon(){

    const double vertexX = finiteRecoParticlePtr_->GetX();
    const double vertexY = finiteRecoParticlePtr_->GetY();
    unsigned int isRightCounter = 0;
    for ( unsigned int i = 0; i < polygonCornersX_.size()-1; ++i){
        if (polygonCornersY_[i]==polygonCornersY_[i+1]) continue;
        //Consider only the consecutive pair of points for which the vertex lies in the horizontal band defined by these points' y-values
        if (vertexY <= polygonCornersY_[i] && vertexY <= polygonCornersY_[i+1]) continue;
        if (polygonCornersY_[i] < vertexY && polygonCornersY_[i+1] < vertexY) continue;
	//Check if the vertex is at the right side of the connecting line between point i and point i+1
        if (vertexX < polygonCornersX_[i] + (vertexY-polygonCornersY_[i])
                    *(polygonCornersX_[i+1]-polygonCornersX_[i])
                    /(polygonCornersY_[i+1]-polygonCornersY_[i])) ++isRightCounter;
    }
    if (isRightCounter%2) return true;
    return false;
}


void I3FSSFilter_13::Finish(){

    log_info("SEEN: %u", nSeen_ );
    log_info("KEPT: %u", nKept_ );
    log_info("REJECTED: %u", (nSeen_-nKept_) );
    log_info("z rejected: %u", rejectedZ_);
    log_info("r rejected: %u",rejectedR_);
    log_info("hexrejected: %u",rejectedPoly_);
    log_info("bad or missing fit: %u",rejectedBadFit_);
}
