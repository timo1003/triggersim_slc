
Trigger ConfigIDs
~~~~~~~~~~~~~~~~~

Below is all the information needed to construct a TriggerKey for a 
specific trigger configuration for each season.  Shown only are
the triggers that can be used with the trigger-sim project.  Things
like calibration triggers or min bias are not implemented, so are 
not included here.

To print the full configuration there's a convenience script 
**resources/scripts/print_trigger_configuration.py**.  This will
dump the settings of each trigger as well.

2016 - 2020
^^^^^^^^^^^
=========== =========== ==================== ========
Common Name SourceID    TypeID               ConfigID
=========== =========== ==================== ========
SMT8        IN_ICE      SIMPLE_MULTIPLICITY  1006
SMT3        IN_ICE      SIMPLE_MULTIPLICITY  1011
SMT6        ICE_TOP     SIMPLE_MULTIPLICITY  102
SLOP        IN_ICE      SLOW_PARTICLE        24002
Cluster     IN_ICE      STRING               1007
Cylinder    IN_ICE      VOLUME               21001
Cylinder    ICE_TOP     VOLUME               21002
=========== =========== ==================== ========

2012-2015
^^^^^^^^^

=========== =========== ==================== ========
Common Name SourceID    TypeID               ConfigID
=========== =========== ==================== ========
SMT8        IN_ICE      SIMPLE_MULTIPLICITY  1006
SMT3        IN_ICE      SIMPLE_MULTIPLICITY  1011
SMT6        ICE_TOP     SIMPLE_MULTIPLICITY  102
SLOP        IN_ICE      SLOW_PARTICLE        24002
Cluster     IN_ICE      STRING               1007
Cylinder    IN_ICE      VOLUME               21001
=========== =========== ==================== ========

2011
^^^^

=========== =========== ==================== ========
Common Name SourceID    TypeID               ConfigID
=========== =========== ==================== ========
SMT8        IN_ICE      SIMPLE_MULTIPLICITY  1006
SMT3        IN_ICE      SIMPLE_MULTIPLICITY  1011
SMT6        ICE_TOP     SIMPLE_MULTIPLICITY  102
SLOP        IN_ICE      SLOW_PARTICLE        22005
Cluster     IN_ICE      STRING               1007
Cylinder    IN_ICE      VOLUME               21001
=========== =========== ==================== ========

IC79
^^^^

=========== =========== ==================== ========
Common Name SourceID    TypeID               ConfigID
=========== =========== ==================== ========
SMT8        IN_ICE      SIMPLE_MULTIPLICITY  1006
SMT3        IN_ICE      SIMPLE_MULTIPLICITY  1010
SMT6        ICE_TOP     SIMPLE_MULTIPLICITY  102
Cluster     IN_ICE      STRING               1007
=========== =========== ==================== ========
