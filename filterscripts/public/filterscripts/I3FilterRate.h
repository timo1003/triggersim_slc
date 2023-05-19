#ifndef JEB_FILTER_I3FILTERRATE_H
#define JEB_FILTER_I3FILTERRATE_H

#include <icetray/I3Module.h>
#include <icetray/I3Frame.h>

#include <fstream>

class I3FilterRate : public I3Module
{
 public:

  I3FilterRate(const I3Context&);
  void Configure();
  void Physics(I3FramePtr);
  void Finish();

  SET_LOGGER("I3FilterRate");

 private:
  std::string filename_;
  std::string filtermaskname_;
  unsigned int nevents_;

  unsigned int counter;
  unsigned int firstsec;
  unsigned int lastsec;
  bool filterinit;
  std::vector<std::string> filterlist_;
  std::map<std::string, unsigned int> filters;
  std::map<std::string, bool> fpassed;;

  std::string ntuplefn_;
  bool ntupledo_;
  std::ofstream ntuple;
};

#endif
