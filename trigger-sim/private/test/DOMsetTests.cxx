#include <I3Test.h>

#include <trigger-sim/utilities/DOMSetFunctions.h>
#include <icetray/OMKey.h>

#include <vector>
#include <algorithm>
#include <boost/foreach.hpp>
#include <boost/assign/std/vector.hpp>
#include <boost/assign/list_of.hpp>

using namespace std;
using namespace boost::assign;
using std::vector;

const int DOMSET_2_HIGH_STRING(78);
const int DOMSET_2_LOW_STRING(1);
const int DOMSET_2_HIGH_DOM(60);
const int DOMSET_2_LOW_DOM(1);

const int DOMSET_4_DC_HIGH_DOM(60);
const int DOMSET_4_DC_LOW_DOM(11);
const int DOMSET_4_II_HIGH_DOM(60);
const int DOMSET_4_II_LOW_DOM(41);
const std::vector<int> DOMSET_4_II_STRINGS = list_of(26)(27)(35)(36)(37)(45)(46);

const int DOMSET_5_DC_HIGH_DOM(60);
const int DOMSET_5_DC_LOW_DOM(11);
const int DOMSET_5_II_HIGH_DOM(60);
const int DOMSET_5_II_LOW_DOM(39);
const std::vector<int> DOMSET_5_II_STRINGS = list_of(26)(27)(35)(36)(37)(45)(46);

const int DOMSET_6_DC_HIGH_DOM(60);
const int DOMSET_6_DC_LOW_DOM(11);
const int DOMSET_6_II_HIGH_DOM(60);
const int DOMSET_6_II_LOW_DOM(39);
const std::vector<int> DOMSET_6_II_STRINGS = list_of(25)(26)(27)(34)(35)(36)(37)(44)(45)(46)(47)(54);

TEST_GROUP(DOMSetTests);

TEST(DOMSet2Test)
{

  // generate only DOM set 2 DOMs
  // and ensure that InDOMSet returns
  // true for all of them
  for(int str(DOMSET_2_LOW_STRING); 
      str <= DOMSET_2_HIGH_STRING;
      str++)
    for( int om(DOMSET_2_LOW_DOM);
	 om <= DOMSET_2_HIGH_DOM ;
	 om ++){
      OMKey test_om(str,om);
      ENSURE(DOMSetFunctions::InDOMSet(test_om,2,I3MapKeyVectorIntConstPtr()));
    }

}

TEST(DOMSet3Test)   // This is the IceTop (IT81) detector
{
  // Make sure all the IceTop DOM's are included...
  for(int str(1); str <= 81; str++)
    for( int om(61); om <= 64 ; om ++){
      OMKey test_om(str,om);
      ENSURE(DOMSetFunctions::InDOMSet(test_om,3,I3MapKeyVectorIntConstPtr()));
    }
  // ...and that all of the InIce DOM's are not.
  for(int str(0); str <= 86; str++)  // Yes, there is a "string 0" these days with special stuff on it
    for( int om(1); om <= 60 ; om ++){
      OMKey test_om(str,om);
      ENSURE(!DOMSetFunctions::InDOMSet(test_om,3,I3MapKeyVectorIntConstPtr()));
    }
}

TEST(DOMSet4_DC_Test)
{

  // generate only DOM set 4 DeepCore DOMs
  // and ensure that InDOMSet returns
  // true for all of them
  for(int str(81); str <= 90; str++)
    for( int om(DOMSET_4_DC_LOW_DOM);
	 om <= DOMSET_4_DC_HIGH_DOM ;
	 om ++){
      OMKey test_om(str,om);
      ENSURE(DOMSetFunctions::InDOMSet(test_om,4,I3MapKeyVectorIntConstPtr()));
    }

}

TEST(DOMSet4_II_Test)
{
  // generate only DOM set 4 InIce DOMs
  // and ensure that InDOMSet returns
  // true for all of them
  BOOST_FOREACH(const int& str, DOMSET_4_II_STRINGS)
    for( int om(DOMSET_4_II_LOW_DOM);
	 om <= DOMSET_4_II_HIGH_DOM ;
	 om ++){
      OMKey test_om(str,om);
      ENSURE(DOMSetFunctions::InDOMSet(test_om,4,I3MapKeyVectorIntConstPtr()));
    }

}

TEST(NotInDOMSet4_DC_Test1)
{

  // generate DOMs *NOT* in DomSet 4 
  // and ensure InDOMSet returns false
  for(int str(81); str <= 90; str++)
    for( int om(1);
	 om < DOMSET_4_DC_LOW_DOM ;
	 om ++){
      OMKey test_om(str,om);
      ENSURE(!DOMSetFunctions::InDOMSet(test_om,4,I3MapKeyVectorIntConstPtr()));
    }
}

TEST(NotInDOMSet4_II_Test1)
{
  // generate DOMs *NOT* in DomSet 4 
  // and ensure InDOMSet returns false
  BOOST_FOREACH(const int& str, DOMSET_4_II_STRINGS)
    for( int om(1);
	 om < DOMSET_4_II_LOW_DOM ;
	 om ++){
      OMKey test_om(str,om);
      ENSURE(!DOMSetFunctions::InDOMSet(test_om,4,I3MapKeyVectorIntConstPtr()));
    }

}

TEST(NotDOMSet4_II_String)
{
  // generate DOMs from strings *NOT* in DomSet 4 
  // and ensure InDOMSet returns false
  for(int test_string(1); test_string <= 78; test_string++){
    //skip strings that are not part of DeepCore
    if(count(DOMSET_4_II_STRINGS.begin(), DOMSET_4_II_STRINGS.end(),test_string))
      continue;
    for( int om(1);
	 om < 60 ;
	 om ++){
      OMKey test_om(test_string,om);
      ENSURE(!DOMSetFunctions::InDOMSet(test_om,4,I3MapKeyVectorIntConstPtr()));
    }
  }

}

TEST(DOMSet5_DC_Test)
{

  // generate only DOM set 5 DeepCore DOMs
  // and ensure that InDOMSet returns
  // true for all of them
  for(int str(81); str <= 90; str++)
    for( int om(DOMSET_5_DC_LOW_DOM);
	 om <= DOMSET_5_DC_HIGH_DOM ;
	 om ++){
      OMKey test_om(str,om);
      ENSURE(DOMSetFunctions::InDOMSet(test_om,5,I3MapKeyVectorIntConstPtr()));
    }

}

TEST(DOMSet5_II_Test)
{
  // generate only DOM set 5 InIce DOMs
  // and ensure that InDOMSet returns
  // true for all of them
  BOOST_FOREACH(const int& str, DOMSET_5_II_STRINGS)
    for( int om(DOMSET_5_II_LOW_DOM);
	 om <= DOMSET_5_II_HIGH_DOM ;
	 om ++){
      OMKey test_om(str,om);
      ENSURE(DOMSetFunctions::InDOMSet(test_om,5,I3MapKeyVectorIntConstPtr()));
    }

}

TEST(NotInDOMSet5_DC_Test1)
{

  // generate DOMs *NOT* in DomSet 5 
  // and ensure InDOMSet returns false
  for(int str(81); str <= 90; str++)
    for( int om(1);
	 om < DOMSET_5_DC_LOW_DOM ;
	 om ++){
      OMKey test_om(str,om);
      ENSURE(!DOMSetFunctions::InDOMSet(test_om,5,I3MapKeyVectorIntConstPtr()));
    }
}

TEST(NotInDOMSet5_II_Test1)
{
  // generate DOMs *NOT* in DomSet 5 
  // and ensure InDOMSet returns false
  BOOST_FOREACH(const int& str, DOMSET_5_II_STRINGS)
    for( int om(1);
	 om < DOMSET_5_II_LOW_DOM ;
	 om ++){
      OMKey test_om(str,om);
      ENSURE(!DOMSetFunctions::InDOMSet(test_om,5,I3MapKeyVectorIntConstPtr()));
    }

}

TEST(NotDOMSet5_II_String)
{
  // generate DOMs from strings *NOT* in DomSet 5 
  // and ensure InDOMSet returns false
  for(int test_string(1); test_string <= 78; test_string++){
    //skip strings that are not part of DeepCore
    if(count(DOMSET_5_II_STRINGS.begin(), DOMSET_5_II_STRINGS.end(),test_string))
      continue;
    for( int om(1);
	 om < 60 ;
	 om ++){
      OMKey test_om(test_string,om);
      ENSURE(!DOMSetFunctions::InDOMSet(test_om,5,I3MapKeyVectorIntConstPtr()));
    }
  }

}

// DOMSET 6 tests

TEST(DOMSet6_DC_Test)
{

  // generate only DOM set 6 DeepCore DOMs
  // and ensure that InDOMSet returns
  // true for all of them
  for(int str(79); str <= 86; str++)
    for( int om(DOMSET_6_DC_LOW_DOM);
	 om <= DOMSET_6_DC_HIGH_DOM ;
	 om ++){
      OMKey test_om(str,om);
      ENSURE(DOMSetFunctions::InDOMSet(test_om,6,I3MapKeyVectorIntConstPtr()));
    }

}

TEST(DOMSet6_II_Test)
{
  // generate only DOM set 6 InIce DOMs
  // and ensure that InDOMSet returns
  // true for all of them
  BOOST_FOREACH(const int& str, DOMSET_6_II_STRINGS)
    for( int om(DOMSET_6_II_LOW_DOM);
	 om <= DOMSET_6_II_HIGH_DOM ;
	 om ++){
      OMKey test_om(str,om);
      ENSURE(DOMSetFunctions::InDOMSet(test_om,6,I3MapKeyVectorIntConstPtr()));
    }

}

TEST(NotInDOMSet6_DC_Test1)
{

  // generate DOMs *NOT* in DomSet 6 
  // and ensure InDOMSet returns false
  for(int str(79); str <= 86; str++)
    for( int om(1);
	 om < DOMSET_6_DC_LOW_DOM ;
	 om ++){
      OMKey test_om(str,om);
      ENSURE(!DOMSetFunctions::InDOMSet(test_om,6,I3MapKeyVectorIntConstPtr()));
    }
}

TEST(NotInDOMSet6_II_Test1)
{
  // generate DOMs *NOT* in DomSet 6 
  // and ensure InDOMSet returns false
  BOOST_FOREACH(const int& str, DOMSET_6_II_STRINGS)
    for( int om(1);
	 om < DOMSET_6_II_LOW_DOM ;
	 om ++){
      OMKey test_om(str,om);
      ENSURE(!DOMSetFunctions::InDOMSet(test_om,6,I3MapKeyVectorIntConstPtr()));
    }

}

TEST(NotDOMSet6_II_String)
{
  // generate DOMs from strings *NOT* in DomSet 6 
  // and ensure InDOMSet returns false
  for(int test_string(1); test_string <= 78; test_string++){
    //skip strings that are not part of DeepCore
    if(count(DOMSET_6_II_STRINGS.begin(), DOMSET_6_II_STRINGS.end(),test_string))
      continue;
    for( int om(1);
	 om < 60 ;
	 om ++){
      OMKey test_om(test_string,om);
      ENSURE(!DOMSetFunctions::InDOMSet(test_om,6,I3MapKeyVectorIntConstPtr()));
    }
  }

}

TEST(DOMSet7Test)   // Scintillators: DOM 65 and 66 on strings 12 and 62 only
{
  // Make sure these are in...
  ENSURE(DOMSetFunctions::InDOMSet(OMKey(12, 65),7,I3MapKeyVectorIntConstPtr()));
  ENSURE(DOMSetFunctions::InDOMSet(OMKey(12, 66),7,I3MapKeyVectorIntConstPtr()));
  ENSURE(DOMSetFunctions::InDOMSet(OMKey(62, 65),7,I3MapKeyVectorIntConstPtr()));
  ENSURE(DOMSetFunctions::InDOMSet(OMKey(62, 66),7,I3MapKeyVectorIntConstPtr()));
  // ...and that everything else is not.
  ENSURE(!DOMSetFunctions::InDOMSet(OMKey(30, 65),7,I3MapKeyVectorIntConstPtr()));  // a fictitious DOM!
  ENSURE(!DOMSetFunctions::InDOMSet(OMKey(30, 66),7,I3MapKeyVectorIntConstPtr()));  // a fictitious DOM!
  for(int str(0); str <= 86; str++)
    for( int om(1); om <= 64 ; om ++){
      OMKey test_om(str,om);
      ENSURE(!DOMSetFunctions::InDOMSet(test_om,7,I3MapKeyVectorIntConstPtr()));
    }
}

TEST(DOMSet8Test)   // IceTop volume (2-station) infill, HG only
{
  // Here, we'll just try a few "key" tests.  These 12 DOM's are "in"
  ENSURE(DOMSetFunctions::InDOMSet(OMKey(26, 62),8,I3MapKeyVectorIntConstPtr())); // the flipped one
  ENSURE(DOMSetFunctions::InDOMSet(OMKey(26, 63),8,I3MapKeyVectorIntConstPtr()));
  ENSURE(DOMSetFunctions::InDOMSet(OMKey(36, 61),8,I3MapKeyVectorIntConstPtr()));
  ENSURE(DOMSetFunctions::InDOMSet(OMKey(36, 63),8,I3MapKeyVectorIntConstPtr()));
  ENSURE(DOMSetFunctions::InDOMSet(OMKey(46, 61),8,I3MapKeyVectorIntConstPtr()));
  ENSURE(DOMSetFunctions::InDOMSet(OMKey(46, 63),8,I3MapKeyVectorIntConstPtr()));
  ENSURE(DOMSetFunctions::InDOMSet(OMKey(79, 61),8,I3MapKeyVectorIntConstPtr()));
  ENSURE(DOMSetFunctions::InDOMSet(OMKey(79, 63),8,I3MapKeyVectorIntConstPtr()));
  ENSURE(DOMSetFunctions::InDOMSet(OMKey(80, 61),8,I3MapKeyVectorIntConstPtr()));
  ENSURE(DOMSetFunctions::InDOMSet(OMKey(80, 63),8,I3MapKeyVectorIntConstPtr()));
  ENSURE(DOMSetFunctions::InDOMSet(OMKey(81, 61),8,I3MapKeyVectorIntConstPtr()));
  ENSURE(DOMSetFunctions::InDOMSet(OMKey(81, 63),8,I3MapKeyVectorIntConstPtr()));

  // And make sure these others are "out":
  // ... all of the InIce DOM's are "out".
  for(int str(0); str <= 86; str++)
    for( int om(1); om <= 60 ; om ++){
      OMKey test_om(str,om);
      ENSURE(!DOMSetFunctions::InDOMSet(test_om,8,I3MapKeyVectorIntConstPtr()));
    }
  // ...and that all of the LowGain IceTop are also "out".
  ENSURE(!DOMSetFunctions::InDOMSet(OMKey(26, 61),8,I3MapKeyVectorIntConstPtr())); // the flipped one
  ENSURE(!DOMSetFunctions::InDOMSet(OMKey(26, 64),8,I3MapKeyVectorIntConstPtr()));
  for(int str(1); str <= 81; str++)
    for( int om(62); om <= 64 ; om = om+2){
      if (str != 26) { // not the flipped one
        OMKey test_om(str,om);
        ENSURE(!DOMSetFunctions::InDOMSet(test_om,8,I3MapKeyVectorIntConstPtr()));
      }
    }

}

TEST(DOMSet9Test)   // IceAct: Just string 0 / om 1
{
  // Make sure these are in...
  ENSURE(DOMSetFunctions::InDOMSet(OMKey(0, 1),9,I3MapKeyVectorIntConstPtr()));
  // ...and that everything else is not.
  ENSURE(!DOMSetFunctions::InDOMSet(OMKey(0, 2),9,I3MapKeyVectorIntConstPtr()));
  ENSURE(!DOMSetFunctions::InDOMSet(OMKey(0, 3),9,I3MapKeyVectorIntConstPtr()));
  ENSURE(!DOMSetFunctions::InDOMSet(OMKey(0, 4),9,I3MapKeyVectorIntConstPtr()));
  ENSURE(!DOMSetFunctions::InDOMSet(OMKey(0, 5),9,I3MapKeyVectorIntConstPtr()));
  for(int str(1); str <= 86; str++)
    for( int om(1); om <= 64 ; om ++){
      OMKey test_om(str,om);
      ENSURE(!DOMSetFunctions::InDOMSet(test_om,7,I3MapKeyVectorIntConstPtr()));
    }
}

TEST(DOMSet10Test)   // DMIce
{
  // Make sure these are in...
  ENSURE(DOMSetFunctions::InDOMSet(OMKey(0, 2),10,I3MapKeyVectorIntConstPtr()));
  ENSURE(DOMSetFunctions::InDOMSet(OMKey(0, 3),10,I3MapKeyVectorIntConstPtr()));
  ENSURE(DOMSetFunctions::InDOMSet(OMKey(0, 4),10,I3MapKeyVectorIntConstPtr()));
  ENSURE(DOMSetFunctions::InDOMSet(OMKey(0, 5),10,I3MapKeyVectorIntConstPtr()));
  // ...and that everything else is not.
  ENSURE(!DOMSetFunctions::InDOMSet(OMKey(0, 1),10,I3MapKeyVectorIntConstPtr()));
  for(int str(1); str <= 86; str++)
    for( int om(1); om <= 64 ; om ++){
      OMKey test_om(str,om);
      ENSURE(!DOMSetFunctions::InDOMSet(test_om,10,I3MapKeyVectorIntConstPtr()));
    }
}

TEST(DOMSet11Test)   // This is the InIce (IC86) detector, including all strings DOM's 1-60
 {
   // Make sure all the InIce DOM's are included...
   for(int str(1); str <= 86; str++)
     for( int om(1); om <= 60 ; om ++){
       OMKey test_om(str,om);
       ENSURE(DOMSetFunctions::InDOMSet(test_om,11,I3MapKeyVectorIntConstPtr()));
     }
   // ...and that all of the IceTop DOM's and other DOM's are not.
   for(int str(1); str <= 81; str++)
     for( int om(61); om <= 66 ; om ++){
       OMKey test_om(str,om);
       ENSURE(!DOMSetFunctions::InDOMSet(test_om,11,I3MapKeyVectorIntConstPtr()));
     }
   // Also the "string 0" these days with special stuff on it
   for( int om(0); om <= 5 ; om ++){
     OMKey test_om(0,om);
     ENSURE(!DOMSetFunctions::InDOMSet(test_om,11,I3MapKeyVectorIntConstPtr()));
   }
 }
