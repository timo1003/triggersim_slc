
i3_project(trigger-sim
        PYTHON_DEST icecube/trigger_sim
        PYTHON_DIR python
        DOCS_DIR resources/docs
        )

i3_add_library(trigger-sim
  # The I3Modules
  private/trigger-sim/modules/ClusterTrigger.cxx
  private/trigger-sim/modules/I3GlobalTriggerSim.cxx
  private/trigger-sim/modules/SimpleMajorityTrigger.cxx
  private/trigger-sim/modules/CylinderTrigger.cxx
  private/trigger-sim/modules/I3Pruner.cxx
  private/trigger-sim/modules/SlowMonopoleTrigger.cxx
  private/trigger-sim/modules/SlcTrigger.cxx
  # The algorithms
  private/trigger-sim/algorithms/ClusterTriggerAlgorithm.cxx
  private/trigger-sim/algorithms/GlobalTriggerSim.cxx
  private/trigger-sim/algorithms/SimpleMajorityTriggerAlgorithm.cxx
  private/trigger-sim/algorithms/CylinderTriggerAlgorithm.cxx
  private/trigger-sim/algorithms/SlcTriggerAlgorithm.cxx
  private/trigger-sim/algorithms/TimeWindow.cxx
  private/trigger-sim/algorithms/SlcTimeWindow.cxx
  # The utilities
  private/trigger-sim/utilities/DOMSetFunctions.cxx
  private/trigger-sim/utilities/GTSUtils.cxx
  private/trigger-sim/utilities/ReadoutWindowUtil.cxx
  private/trigger-sim/utilities/TimeShifterUtils.cxx

  USE_TOOLS python boost 

  USE_PROJECTS
  serialization
  icetray
  dataclasses
  phys-services
  simclasses
)

i3_test_executable(test
  private/test/*.cxx
  USE_TOOLS boost python gsl
  USE_PROJECTS
  icetray
  trigger-sim
  dataclasses
  phys-services
)

i3_add_pybindings(trigger_sim
  private/pybindings/module.cxx
  private/pybindings/GlobalTriggerSim.cxx
  USE_TOOLS boost python
  USE_PROJECTS trigger-sim
  )

i3_test_scripts(resources/test/*.py)
set_tests_properties(trigger-sim::test PROPERTIES LABELS RUN_LONG)
