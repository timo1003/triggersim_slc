//
//   Copyright (c) 2004, 2005, 2006, 2007   Troy D. Straszheim  
//   
//   $Id$
//
//   This file is part of IceTray.
//
//   Redistribution and use in source and binary forms, with or without
//   modification, are permitted provided that the following conditions
//   are met:
//   1. Redistributions of source code must retain the above copyright
//      notice, this list of conditions and the following disclaimer.
//   2. Redistributions in binary form must reproduce the above copyright
//      notice, this list of conditions and the following disclaimer in the
//      documentation and/or other materials provided with the distribution.
//   
//   THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
//   ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
//   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
//   ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
//   FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
//   DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
//   OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
//   HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
//   LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
//   OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
//   SUCH DAMAGE.
//   
//   SPDX-License-Identifier: BSD-2-Clause
//   
//

#include <vector>

#include <dataclasses/physics/I3Waveform.h>

#include <icetray/python/dataclass_suite.hpp>
#include <dataclasses/ostream_overloads.hpp>

using namespace boost::python;

void register_I3WaveformSeriesMap()
{
  class_<I3WaveformSeriesMap, bases<I3FrameObject>, I3WaveformSeriesMapPtr>("I3WaveformSeriesMap")
    .def(dataclass_suite<I3WaveformSeriesMap>())
    ;

  register_pointer_conversions<I3WaveformSeriesMap>();
}

void register_I3ScintWaveformSeriesMap()
{
  class_<I3ScintWaveformSeriesMap, bases<I3FrameObject>, I3ScintWaveformSeriesMapPtr>("I3ScintWaveformSeriesMap")
    .def(dataclass_suite<I3ScintWaveformSeriesMap>())
    ;

  register_pointer_conversions<I3ScintWaveformSeriesMap>();
}