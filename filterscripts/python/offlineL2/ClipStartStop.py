
from icecube import icetray

class ClipStartStop(icetray.I3Module):
    """
    Run startup is complicated, and data may be recorded before it is complete.
    As a result, we need to listen to what the DAQ says was the range of times
    when everything was really up and running, and discard events outside.

    It only does something if the `GoodRunStartTime` and the `GoodRunEndTime` are specified.
    They are usually available in D frames of GCD files for seasons >= 2013.
    """

    def __init__(self, context):
        icetray.I3Module.__init__(self, context)
        self.AddOutBox('OutBox')

    def Configure(self):
        # Can have three states:
        # ----------------------
        # None: unknown
        # -1: Before good time range
        #  0: In good time range
        # +1: Not in good time range anymore (all pending frames are outside of the good time range)
        # ----------------------
        # Note: If the state is `unknown` the frame will be kept! Better keep a frame than lose a frame.
        self._in_good_time_range = None

    def Process(self):
        frame = self.PopFrame()

        # Not in good time range anymore?
        if self._in_good_time_range == 1:
            return

        if frame.Has("I3EventHeader"):
            header = frame["I3EventHeader"]
            if frame.Has("GoodRunStartTime"):
                if frame["GoodRunStartTime"] > header.start_time:
                    self._in_good_time_range = -1
                    return # event began too early

            if frame.Has("GoodRunEndTime"):
                if frame["GoodRunEndTime"] < header.end_time:
                    self._in_good_time_range = 1
                    return # event ended too late

            # We're in the good time range
            self._in_good_time_range = 0
            # Note: We're also in the good time range if no GoodRunStartTime and no GoodRunEndTime
            # are specified. That's OK since then we want to keep everything.
        elif self._in_good_time_range == -1:
            # No Header; last header said we're not in good time range yet
            return

        self.PushFrame(frame)

