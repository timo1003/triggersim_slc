from icecube import icetray, dataclasses, phys_services
from I3Tray import I3Tray

from icecube.gcdserver.GCDGeneratorModule import GCDGenerator



@icetray.traysegment
def generate(tray, name, run_id):
    from icecube.BadDomList.BadDomListTraySegment import BadDomList

    live_info = get_i3live_info(run_id)

    tray.Add(GCDGenerator, "GCDGenerator", RunId=run_id)

    tray.Add(set_production_information, "set_production_information",
             good_start_time = live_info['start_i3time'],
             good_stop_time = live_info['stop_i3time'],
             production_version = -1,
             snapshot_id = live_info['latest_snapshot']['id'],
             Streams = [icetray.I3Frame.DetectorStatus])

    tray.Add(BadDomList, "baddomlist", RunId = run_id)

@icetray.traysegment
def audit(tray, name, run_id):
    live_info = get_i3live_info(run_id)

    tray.Add(adjust_dst_time, "adjust_dst_time",
             run_start_time = live_info['start_i3time'],
             run_stop_time = live_info['stop_i3time'],
             Streams = [icetray.I3Frame.DetectorStatus])
    tray.Add('I3GCDAuditor', 'GCDAuditor', MaximumParanoia=True)



# ~ def get_latest_transaction_of_gcd_db(db_host = 'mongodb-live'):
    # ~ import pymongo
    # ~ from icecube.gcdserver.OptionParser import DEFAULT_DB_PASS, DEFAULT_DB_USER

    # ~ client = pymongo.MongoClient(db_host)

    # ~ try:
        # ~ client.omdb.collection_names()
        # ~ # We have all privileges on db
    # ~ except:
        # ~ # We need to authenticate
        # ~ client.omdb.authenticate(DEFAULT_DB_USER, DEFAULT_DB_PASS)

    # ~ collection = client.omdb.transaction

    # ~ transactions = collection.find().sort('transaction', pymongo.DESCENDING)

    # ~ if not transactions.count():
        # ~ logger.critical('No transaction found')
        # ~ raise Exception('No transaction found')

    # ~ return transactions[0]

def get_i3live_info(run_id, i3live_host='https://live.icecube.wisc.edu'):
    from datetime import datetime
    import requests

    if run_id in get_i3live_info.history:
        return get_i3live_info.history[run_id]

    data = {'user': 'icecube', 'pass': 'skua', 'run_number': run_id}
    r = requests.request('POST', i3live_host+'/run_info/', data=data)
    r.raise_for_status()
    j = r.json()

    if j['grl_start']:
        start = datetime.strptime(j['grl_start'], '%Y-%m-%d %H:%M:%S')
        start_frac = j['grl_start_frac']
    else:
        start = datetime.strptime(j['start'], '%Y-%m-%d %H:%M:%S')
        start_frac = j['start_frac']
    if j['grl_stop']:
        stop = datetime.strptime(j['grl_stop'], '%Y-%m-%d %H:%M:%S')
        stop_frac = j['grl_stop_frac']
    else:
        stop = datetime.strptime(j['stop'], '%Y-%m-%d %H:%M:%S')
        stop_frac = j['stop_frac']

    start_t = dataclasses.I3Time()
    start_t.set_utc_cal_date(start.year, start.month, start.day, start.hour,
                             start.minute, start.second, start_frac/10)
    stop_t = dataclasses.I3Time()
    stop_t.set_utc_cal_date(stop.year, stop.month, stop.day, stop.hour,
                            stop.minute, stop.second, stop_frac/10)

    j['start_i3time'] = start_t
    j['stop_i3time'] = stop_t
    get_i3live_info.history[run_id] = j
    return j
get_i3live_info.history = {}

def set_production_information(frame, production_version, snapshot_id, good_start_time, good_stop_time):
    frame["OfflineProductionVersion"] = dataclasses.I3Double(production_version)
    frame["GRLSnapshotId"] = dataclasses.I3Double(snapshot_id)
    frame["GoodRunStartTime"] = good_start_time
    frame["GoodRunEndTime"] = good_stop_time


def adjust_dst_time(frame, run_start_time, run_stop_time):
    """
    Adjust DetectorStatus times when they are way off from the actual start time because of a bug.

    Args:
        frame (I3Frame): The frame
        run_start_time (I3Time): The run start time
        run_stop_time (I3Time): The run stop time
    """

    if abs((frame['I3DetectorStatus'].start_time.date_time - run_start_time.date_time).total_seconds()) > 100:
        logger.warning("DS Start Time Needs Adjustment")
        logger.warning("Original Start Time is: {0}".format(frame['I3DetectorStatus'].start_time.date_time))
        logger.warning("Start Time from i3live: {0}".format(run_start_time.date_time))
        raise Exception('bad I3DetectorStatus start time')
        #frame['I3DetectorStatus'].start_time = run_start_time
        
        
    if abs((frame['I3DetectorStatus'].end_time.date_time - run_stop_time.date_time).total_seconds()) > 100:
        logger.warning("DS End Time Needs Adjustment")
        logger.warning("Original End Time is: {0}".format(frame['I3DetectorStatus'].end_time.date_time))
        logger.warning("End Time from i3live: {0}".format(run_stop_time.date_time))
        raise Exception('bad I3DetectorStatus stop time')
        #frame['I3DetectorStatus'].end_time = run_stop_time

def parse_gcd_audit_output(path, logger):
    """
    Helper method to parse the gcd audit log and return `True` if everything
    is OK, otherwise `False`.

    Args:
        path (str): Path of the logfile
        logger (Logger): The logger of the script

    Returns:
        boolean: `True` if everything is OK, otherwise `False`.
    """

    with open(path, 'r') as f:
        l = str(f.read())
        l = l.split("\n")

        logger.info("====Start GCDAudit Log===")
        for line in l:
            logger.info(line)
        logger.info("===End GCDAudit Log====")

        h = [n for n in l if("GCDAuditor" in n \
                          and "ERROR" in n \
                          and "OMOMKey(19,60,0)" not in n)
                        ]

        if not len(h):   
            logger.info("GCD Audit for OK")
            return True
        else:
            logger.error("GCD audit failed")
            logger.info("====== GCD output after filtering ====")
            for line in h:
                logger.info(line)
            logger.info("====== End GCD output after filtering ====")
            return False
