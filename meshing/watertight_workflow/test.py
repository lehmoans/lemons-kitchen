from inputs import *

import ansys.fluent.core as pyfluent

session = pyfluent.launch_fluent(mode="meshing",processor_count=2, precision="double")

workflow =  session.watertight()

import_geom = workflow.TaskObject['Import Geometry']
print("lol")
