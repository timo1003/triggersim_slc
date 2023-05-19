#ifndef I3CASCADEFILTER_13_H
#define I3CASCADEFILTER_13_H

#include <filterscripts/I3JEBFilter.h>


class I3CascadeFilter_13 : public I3JEBFilter
{
	public:
    	I3CascadeFilter_13(const I3Context&);
    	void Configure();
    	bool KeepEvent(I3Frame& frame);
    	void Finish();
    
    	SET_LOGGER("I3CascadeFilter_13");
    
	private:
    	// input keys
	std::string hitMultKey_;
    	std::string llhParticleKey_;
    	std::string cscdllhparamskey_;
    	std::string toiparamskey_;
    	std::string lfkey_;
	// cut values
	unsigned int minNString_;
    	double cosThetaMax_;
    	double CscdrLlh1_;
    	double CscdrLlh2_;
    	double toievalratio_;
    	double lfvelocity_;
    	// output keys
    	std::string cscdllhkey_;
    	std::string eratiokey_;
    	std::string lfvelkey_;
};


#endif
