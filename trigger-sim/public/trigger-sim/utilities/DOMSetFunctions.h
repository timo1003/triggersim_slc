/**
 * copyright  (C) 2004
 * the icecube collaboration
 *  $Id: DOMSetFunctions.h 2009/08/04 21: olivas Exp $
 *
 * @file DOMSetFunctions.h
 * @version $Revision: 1.1.1.1 $
 * @date $Date: 2004/11/06 21:00:46 $
 * @author olivas
 */

#ifndef DOMSETFUNCTIONS_H
#define DOMSETFUNCTIONS_H

#include <icetray/OMKey.h>
#include <dataclasses/I3Map.h>
#include <boost/assign/list_of.hpp>

/**
 * @brief Contains functions useful for handling DOMsets.
 */
namespace DOMSetFunctions{

  /**
   * The DomSets are defined by an XML file that lives with the pDAQ trigger definitions, here:
   *     http://code.icecube.wisc.edu/daq/projects/config/trunk/trigger/domset-definitions.xml
   * As of August 2022, this includes:
   *    (0) and (1): AMANDA sets not used anymore
   *    (2) InIce strings 1-78
   *    (3) IceTop IT81
   *    (4), (5), and (6) Different versions of DeepCore
   *    (7) Scintillators
   *    (8) IceTop Infill (HG only) for the 2-station (Volume) trigger
   *    (9) IceAct
   *    (10) DMIce
   *    (11) InIce IC86
   * See DOMSetFunctions::InDOMSet_orig for details.  Or the XML file. (Hopefully they match!)
   */
  const std::vector<unsigned> DOMSETS = boost::assign::list_of(2)(3)(4)(5)(6)(7)(8)(9)(10)(11);
  bool InDOMSet(const OMKey& dom, const unsigned& domSet,
                const I3MapKeyVectorIntConstPtr &domSets);
    
  I3MapKeyVectorIntPtr GetDefaultDOMSets();

}; 

#endif //DOMSETFUNCTIONS_H
