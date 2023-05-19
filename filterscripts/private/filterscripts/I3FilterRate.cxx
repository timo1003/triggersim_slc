#include <filterscripts/I3FilterRate.h>

I3_MODULE(I3FilterRate);

#include <dataclasses/physics/I3EventHeader.h>
#include <icetray/I3Bool.h>
#include <dataclasses/physics/I3FilterResult.h>

using std::ofstream;
using std::endl;

I3FilterRate::I3FilterRate(const I3Context& context) :
  I3Module(context),
  filename_("FilterRate.xml"),
  filtermaskname_("filterMask"),
  nevents_(10000),
  counter(0),
  firstsec(0),
  lastsec(0),
  filterinit(false),
  ntuplefn_("filter-ntuple.txt"),
  ntupledo_(false)
{
  AddParameter("XMLFileName",
	       "The name of the resultant xml file.",
	       filename_);

  AddParameter("FilterMaskName",
	       "The name of the I3FilterResultMap in the frame.",
	       filtermaskname_);

  AddParameter("NEvents",
	       "Number of frames to process before dumping the rate xml "
	       "file and clearing the history. (0 for no resultant file).",
	       nevents_);

  AddParameter("DoNTuple",
	       "Bool indicating whether the ntuple "
	       "text file should be outputted.",
	       ntupledo_);

  AddParameter("NTupleFileName",
	       "File where the ntuple text file should be saved.",
	       ntuplefn_);

  filterlist_.resize(0);
  AddParameter("FilterList",
	       "A list of the filter decisions in the frame that should be studied. "
	       "These will only be used if the filtermask is not availale.",
	       filterlist_);

  AddOutBox("OutBox");
}

void I3FilterRate::Configure()
{
  GetParameter("XMLFileName",filename_);
  GetParameter("FilterMaskName",filtermaskname_);
  GetParameter("NEvents",nevents_);
  GetParameter("DoNTuple",ntupledo_);
  GetParameter("NTupleFileName",ntuplefn_);
  GetParameter("FilterList",filterlist_);
  filters["Total"] = 0;
  filterlist_.push_back("Total");

  if(ntupledo_) ntuple.open(ntuplefn_.c_str(),ofstream::out);
}

void I3FilterRate::Physics(I3FramePtr frame)
{
  log_trace("Entering FilterRate Physics()");
  ++counter;

  I3EventHeaderConstPtr header = frame->Get<I3EventHeaderConstPtr>();
  if(header)
    {
      if(firstsec == 0) firstsec = header->GetStartTime().GetUTCSec();
      else lastsec = header->GetStartTime().GetUTCSec();
    }

  bool eventKept = false;
  I3FilterResultMapConstPtr fmap = 
    frame->Get<I3FilterResultMapConstPtr>(filtermaskname_);
  if(fmap)
    {
      for(I3FilterResultMap::const_iterator fiter = fmap->begin();
	  fiter != fmap->end();
	  ++fiter)
	{
	  // Load all the filters into our result map
	  if(!filterinit)
	    {
	      filters[fiter->first] = 0;
	      fpassed[fiter->first] = false;
	    }

	  // Increment any satisfied filter in our result map
	  if(fiter->second.conditionPassed &&
	     fiter->second.prescalePassed)
	    {
	      fpassed[fiter->first] = true;
	      ++filters[fiter->first];
	      eventKept = true;
	    }
	}
    }
  else
    {
      for(std::vector<std::string>::const_iterator fiter = filterlist_.begin();
	  fiter != filterlist_.end();
	  ++fiter)
	{
	  if(!filterinit)
	    {
	      filters[*fiter] = 0;
	      fpassed[*fiter] = false;
	    }

	  I3BoolConstPtr thebool = frame->Get<I3BoolConstPtr>(*fiter);
	  if(thebool && thebool->value)
	    {
	      fpassed[*fiter] = true;
	      ++filters[*fiter];
	      eventKept = true;
	    }
	}
    }
  if(eventKept)
    {
      ++filters["Total"];
      fpassed["Total"] = true;
    }

  if(ntupledo_)
    {
      if(!filterinit)
	{
	  for(std::map<std::string,bool>::const_iterator fiter = fpassed.begin();
	      fiter != fpassed.end();
	      ++fiter)
	    {
	      ntuple << fiter->first << " ";
	    }
	  ntuple << endl;
	}

      for(std::map<std::string,bool>::iterator fiter = fpassed.begin();
	  fiter != fpassed.end();
	  ++fiter)
	{
	  ntuple << fiter->second << " ";
	  fiter->second = false;
	}
      ntuple << endl;
    }

  if(counter >= nevents_ && nevents_ != 0)
    {
      unsigned int livetime = lastsec - firstsec;
      ofstream ofile;
      ofile.open(filename_.c_str(),ofstream::out);
      ofile << "<physics-filters>" << endl;
      for(std::map<std::string,unsigned int>::const_iterator fiter = filters.begin();
	  fiter != filters.end();
	  ++fiter)
	{
	  float rate = fiter->second / static_cast<float>(livetime);
	  ofile << "  <" << fiter->first << ">" << rate;
	  ofile << "</" << fiter->first << ">" << endl;
	}
      ofile << "</physics-filters>" << endl;
      ofile.close();
      log_info("Wrote xml file %s",filename_.c_str());
      counter = 0;
      firstsec = 0;
      lastsec = 0;
      for(std::map<std::string, unsigned int>::iterator iter = filters.begin(); 
	  iter != filters.end(); ++iter)
	iter->second = 0;
    }

  if(!filterinit && fmap) filterinit = true;
  PushFrame(frame,"OutBox");
}

void I3FilterRate::Finish()
{
}
