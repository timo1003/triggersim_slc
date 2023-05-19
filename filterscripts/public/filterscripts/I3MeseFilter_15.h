#ifndef I3MESEFILTER_15_H
#define I3MESEFILTER_15_H

#include <filterscripts/I3JEBFilter.h>


class I3MeseFilter_15: public I3JEBFilter
{
	public:
    	I3MeseFilter_15(const I3Context&);
    	void Configure();
    	bool KeepEvent(I3Frame& frame);
    	void Finish();
    
    	SET_LOGGER("I3MeseFilter_15");
    
	private:

};


#endif
