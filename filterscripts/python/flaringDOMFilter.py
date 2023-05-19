
from icecube import icetray, dataclasses
from icecube.filterscripts import filter_globals
from I3Tray import I3Units
import json


knownOffenders = [icetray.OMKey(9, 22),
                  icetray.OMKey(9, 56),
                  icetray.OMKey(27, 57),
                  icetray.OMKey(45, 60),
                  icetray.OMKey(47, 49),
                  icetray.OMKey(50, 52),
                  icetray.OMKey(51, 59),
                  icetray.OMKey(52, 57),
                  icetray.OMKey(57, 40),
                  icetray.OMKey(80, 24),
                  icetray.OMKey(80, 31),
                  icetray.OMKey(80, 42),
                  icetray.OMKey(80, 47),
                  icetray.OMKey(82, 51),
                  icetray.OMKey(82, 57),
                  icetray.OMKey(83, 12),
                  icetray.OMKey(83, 20),
                  icetray.OMKey(83, 22),
                  icetray.OMKey(83, 33),
                  icetray.OMKey(83, 52),
                  icetray.OMKey(83, 58),
                  icetray.OMKey(85, 18)]


CUT_OFFENDING_DOM_EVENTS = "CutOffendingDOMEvents"
CUT_ALL_EVENTS = "CutAllEvents"


class FlaringDOMFilter(icetray.I3ConditionalModule):
    def __init__(self, context):
        icetray.I3ConditionalModule.__init__(self, context)

        self.AddParameter('pulsesName',
                          'Name of pulse series to analyze',
                          'SRTInIcePulses')

        self.AddParameter('errataName',
                          'Name of LID errata object',
                          'LIDErrata')

        self.AddParameter('chargeThreshold',
                          'Minimum charge needed to select an '
                          'OM for analysis, in PE',
                          30)

        self.AddParameter('causalCut',
                          'Time cut determining whether a hit is causal',
                          -15 * I3Units.ns)

        self.AddParameter('minChargeFraction',
                          'Cut parameter: Minimum fraction of '
                          'charge on selected OM',
                          0.7)

        self.AddParameter('maxNonCausalHits',
                          'Cut parameter: Maximum number of non-causal hits '
                          'relative to first pulse in selected OM',
                          1)

        self.AddParameter('sendErrataMoni',
                          'Send Errata moni messages (for use online)',
                          True)

        self.AddParameter('mode',
                          ('Analysis Mode: "%s": Remove flaring events from '
                           'known offending DOMs; "%s": Remove flaring events '
                           'from all DOMs' %
                           (CUT_OFFENDING_DOM_EVENTS, CUT_ALL_EVENTS)),
                          CUT_OFFENDING_DOM_EVENTS)

        self.AddParameter('additionalDOMs',
                          'OMKey list to add to known offenders',
                          [])

        self.AddOutBox("OutBox")

    def Configure(self):
        self.pulsesName = self.GetParameter('pulsesName')
        self.errataName = self.GetParameter('errataName')
        self.chargeThreshold = self.GetParameter('chargeThreshold')
        self.causalCut = self.GetParameter('causalCut')
        self.minChargeFraction = self.GetParameter('minChargeFraction')
        self.maxNonCausalHits = self.GetParameter('maxNonCausalHits')
        self.sendErrataMoni = self.GetParameter('sendErrataMoni')
        self.mode = self.GetParameter('mode')
        modes = [CUT_OFFENDING_DOM_EVENTS, CUT_ALL_EVENTS]
        if self.mode not in modes:
            icetray.logging.log_fatal("Mode %s not in allowed modes: %s" %
                                                         (self.mode, modes))
        self.omKeyList = knownOffenders
        self.omKeyList.extend(self.GetParameter('additionalDOMs'))

    def addErrataMoni(self, frame, errataKeys):
        # OMKey is not serializable
        header = frame['I3EventHeader']
        keys = [{"string": k.string, "position": k.om} for k in errataKeys]
        message = {"keys": keys,
                   "run": header.run_id,
                   "event": header.event_id}
        frame_object_name = filter_globals.flaring_dom_message
        frame[frame_object_name] = dataclasses.I3String(json.dumps(message))

    def cleanPulses(self, pulses):
        # Sort in time order and remove the first 1% of charge
        sortedPulses = sorted(pulses, key=lambda p: p.time)
        qsum = sum(p.charge for p in sortedPulses)
        threshold = qsum / 100.
        qsum = 0.
        for i in range(len(sortedPulses)):
            qsum += sortedPulses[i].charge
            if qsum >= threshold:
                return sortedPulses[i:]

    def cleanAllPulses(self, pulses):
        cleanedPulses = {}
        for key in pulses.keys():
            cleanedPulses[key] = self.cleanPulses(pulses[key])
        return cleanedPulses

    def doFlaringDOMAnalysis(self, key, pulses, frame):

        geo = frame['I3Geometry']
        pos = geo.omgeo[key].position
        keyCharge = sum(p.charge for p in pulses[key])
        t0 = pulses[key][0].time
        totalCharge = keyCharge
        nprior = 0
        for omKey in pulses.keys():
            if omKey == key:
                continue
            d = (geo.omgeo[omKey].position - pos).magnitude
            totalCharge += sum(p.charge for p in pulses[omKey])
            tExp = t0 + d / dataclasses.I3Constants.c_ice
            tRes = pulses[omKey][0].time - tExp
            isNeighbor = (omKey.string == key.string and
                          abs(omKey.om - key.om) < 4)
            if tRes < self.causalCut and isNeighbor:
                nprior += 1

        return ((keyCharge / totalCharge) > self.minChargeFraction and
                nprior <= self.maxNonCausalHits)

    def Physics(self, frame):

        if self.pulsesName in frame:

            pulses = frame[self.pulsesName].apply(frame)
            chargemap = dict([(k, sum([p.charge for p in v]))
                                       for k, v in pulses.items()])
            selectedKeys = set(k for k in chargemap if
                                         chargemap[k] > self.chargeThreshold)
            if self.mode == CUT_OFFENDING_DOM_EVENTS:
                selectedKeys = selectedKeys.intersection(self.omKeyList)

            errata = dataclasses.I3VectorOMKey()
            cleanedPulses = None
            for key in selectedKeys:
                if cleanedPulses is None:
                    cleanedPulses = self.cleanAllPulses(pulses)
                if self.doFlaringDOMAnalysis(key, cleanedPulses, frame):
                    errata.append(key)
            if len(errata) > 0:
                if self.sendErrataMoni:
                    self.addErrataMoni(frame, errata)
                frame[self.errataName] = errata

        self.PushFrame(frame)
