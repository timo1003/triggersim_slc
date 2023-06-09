#ifndef TRIGGERCONTAINER_H_
#define TRIGGERCONTAINER_H_

#include<dataclasses/physics/I3Trigger.h>
#include<dataclasses/physics/I3Particle.h>

/*
 * TriggerContainer.h
 *
 *  Created on: Apr 7, 2011
 *      Author: Emanuel Jacobi jacobi@icecube.wisc.edu
 *      container class for slow-mp trigger objects
 */

class TriggerContainer
{
 public:
	TriggerContainer() : ntuples(0){}
	TriggerContainer(I3TriggerPtr aSlowmptrigger) : slowmptrigger(aSlowmptrigger), ntuples(1) {}
	TriggerContainer(I3TriggerPtr aSlowmptrigger, int aNtuples) : slowmptrigger(aSlowmptrigger), ntuples(aNtuples) {}

  // FIXME: Note for Sebastian and Jakob
  // For the most part this class is a behavior-less data aggregate.
  // Consider a simple struct instead.
  // As far as I can tell you might gain from this encapsulation only
  // by fixed trigger at construction ever increasing (never decreasing) tuples.
  // Maybe that's a desired feature, dunno.  I'm also guessing that I3Particle
  // is over-kill here and an internal home grown structure might be more appropriate.
  // struct TriggerContainer{
  //            I3TriggerPtr trigger;
  //            int ntuples;
  //            vector<I3ParticlePtr> pos1;
  //            vector<I3ParticlePtr> pos2;
  //            vector<I3ParticlePtr> pos3;
  //  };
  
	I3TriggerPtr GetTrigger()
 	{
	 	 return slowmptrigger;
 	}
	int GetNTuples()
	{
		return ntuples;
	}
	void IncreaseNTuples()
	{
		ntuples++;
	}


	I3ParticlePtr GetPos1(int tuple_nr)
	{
		return pos1.at(tuple_nr);
	}
	I3ParticlePtr GetPos2(int tuple_nr)
	{
		return pos2.at(tuple_nr);
	}
	I3ParticlePtr GetPos3(int tuple_nr)
	{
		return pos3.at(tuple_nr);
	}
	void SetPos1(I3ParticlePtr tupel)
	{
		pos1.push_back(tupel);
	}
	void SetPos2(I3ParticlePtr tupel)
	{
		pos2.push_back(tupel);
	}
	void SetPos3(I3ParticlePtr tupel)
	{
		pos3.push_back(tupel);
	}


 private:
	I3TriggerPtr slowmptrigger;

	int ntuples;

	std::vector<I3ParticlePtr> pos1;
	std::vector<I3ParticlePtr> pos2;
	std::vector<I3ParticlePtr> pos3;

};

typedef std::vector<TriggerContainer> TriggerContainerVector;

I3_POINTER_TYPEDEFS(TriggerContainer);
I3_POINTER_TYPEDEFS(TriggerContainerVector);


#endif /* TRIGGERCONTAINER_H_ */
