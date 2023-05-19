from icecube import icetray, dataclasses, BadDomList
from I3Tray import I3Tray

def run_bad_dom_audit(gcd_path, input_file):
    from icecube.filterscripts.offlineL2.Rehydration import Rehydration

    bad_dom_list = 'BadDomListSLC'
    logger.debug('BadDOMList = {0}'.format(bad_dom_list))

    tray = I3Tray()
    tray.Add('I3Reader', 'reader', FilenameList = [gcd_path, rehydrated_input_file])
    tray.Add(Rehydration, 'rehydrator', doNotQify = False)
    tray.Add('I3BadDOMAuditor', 'BadDOMAuditor',
             BadDOMList = bad_dom_list,
             Pulses = ['InIcePulses', 'IceTopPulses'],
             IgnoreOMs = [OMKey(12, 65), OMKey(12, 66), OMKey(62, 65), OMKey(62, 66)],
             UseGoodRunTimes = True)
    tray.Execute()

def parse_bad_dom_audit(path, logger):
    with open(path,'r') as f:
        d = str(f.read())
        d = d.split("\n")

        logger.info("====Start BadDoms Log===")
        for line in d:
            logger.info(line)
        logger.info("===End BadDoms Log====")

        b = [n for n in d if "BadDOMAuditor" in n \
                    and "ERROR" in n \
                    and "OMOMKey" in n]

        if not len(b):
            return True

        else:
            logger.error("BadDOMs audit failed")
            logger.info("====== Bad dom audit output after filtering ====")
            for line in b:
                logger.info(line)
            logger.info("====== End bad dom audit output after filtering ====")
            return False
