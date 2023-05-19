#ifndef I3COSMICRAYFILTER_13_H
#define I3COSMICRAYFILTER_13_H

#include <filterscripts/I3JEBFilter.h>
#include <dataclasses/physics/I3RecoPulse.h>
#include <dataclasses/I3MapOMKeyMask.h>

class I3CosmicRayFilter_13: public I3JEBFilter
{
public:
    I3CosmicRayFilter_13(const I3Context&);
    void Configure();
    bool KeepEvent(I3Frame& frame);
    void Finish() {};
    
    SET_LOGGER("I3CosmicRayFilter_13");

private:
    std::string triggerName_;
    std::string itPulseMaskName_;    
};

#endif
