from pathlib import Path

import ansys.fluent.core as pyfluent
from ansys.fluent.core import examples
from ansys.fluent.visualization import set_config
import ansys.fluent.visualization.pyvista as pv

#internal modules
from mesh import Mesh

#constants
from inputs import *

#updates
from meshing.updates import send_update

class Solver(Mesh):
        def __init__(self):
            super().__init__() #inherit variables/methods set in mesh
            # Define Constants class variables
            self.density = DENSITY
            self.inlet_pressure = INLET_PRESSURE 
            self.inlet_area = INLET_AREA

        def start_solver(self):
            self.session = pyfluent.launch_fluent(mode="solution",
                                              precision=self.precision,
                                              processor_count=self.processors,
                                              show_gui=self.show_gui)

        def set_materials(self):
            # Define Materials
            
            self.session.tui.define.materials.change_create("air", "air", "yes", "constant", self.density)
            self.session.settings.setup.models.viscous.model = "k-epsilon"
            self.session.settings.setup.models.viscous.k_epsilon_model = "realizable"
            self.session.settings.setup.models.viscous.options.curvature_correction = True


        def set_BCs(self):
            # Define Boundary Conditions
            
            self.inlet = self.session.settings.setup.boundary_conditions.velocity_inlet["inlet"]
            self.inlet.turbulence.turb_intensity = TURB_INTENSITY_INLET
            #self.inlet.momentum.velocity.value = self.inlet_velocity
            self.inlet.turbulence.turb_viscosity_ratio = TURB_VISCOCITY_RATIO

            self.outlet = self.session.settings.setup.boundary_conditions.pressure_outlet["outlet"]
            self.outlet.turbulence.turb_intensity = TURB_INTENSITY_OUTLET

        def set_RVs(self):
            # Define Reference Values
            
            self.session.settings.setup.reference_values.area = self.inlet_area
            self.session.settings.setup.reference_values.density = self.density
            #self.session.settings.setup.reference_values.velocity = self.inlet_velocity

        def set_solver_settings(self):
            # Define Solver Settings
            self.session.tui.solve.set.p_v_coupling(24)

            self.session.tui.solve.set.discretization_scheme("pressure", 12)
            self.session.tui.solve.set.discretization_scheme("k", 1)
            self.session.tui.solve.set.discretization_scheme("epsilon", 1)
            self.session.tui.solve.initialize.set_defaults("k", 0.000001)

            self.session.settings.solution.monitor.residual.equations["continuity"].absolute_criteria = (
                RESIDUAL_CRITERIA
            )
            self.session.settings.solution.monitor.residual.equations["x-velocity"].absolute_criteria = (
                RESIDUAL_CRITERIA
            )
            self.session.settings.solution.monitor.residual.equations["y-velocity"].absolute_criteria = (
                RESIDUAL_CRITERIA
            )
            self.session.settings.solution.monitor.residual.equations["z-velocity"].absolute_criteria = (
                RESIDUAL_CRITERIA
            )
            self.session.settings.solution.monitor.residual.equations["k"].absolute_criteria = RESIDUAL_CRITERIA
            self.session.settings.solution.monitor.residual.equations["epsilon"].absolute_criteria = (
                RESIDUAL_CRITERIA
            )

        def set_report_defs(self):
        
            # Define Report Definitions
        

            self.session.settings.solution.report_definitions.drag["cd-mon1"] = {}
            self.session.settings.solution.report_definitions.drag["cd-mon1"] = {
                "zones": ["wall_ahmed_body_main", "wall_ahmed_body_front", "wall_ahmed_body_rear"],
                "force_vector": [0, 0, 1],
            }
            self.session.parameters.output_parameters.report_definitions.create(name="parameter-1")
            self.session.parameters.output_parameters.report_definitions["parameter-1"] = {
                "report_definition": "cd-mon1"
            }

            self.session.settings.solution.monitor.report_plots.create(name="cd-mon1")
            self.session.settings.solution.monitor.report_plots["cd-mon1"] = {"report_defs": ["cd-mon1"]}

        def run_solver(self):
        # Initialize and Run Solver

            self.session.settings.solution.run_calculation.iter_count = 5
            self.session.settings.solution.initialization.initialization_type = "standard"
            self.session.settings.solution.initialization.standard_initialize()
            self.session.settings.solution.run_calculation.iterate(iter_count=5)

        def post_process(self):
            # Post-Processing Workflow
            self.session.results.surfaces.iso_surface.create(name="xmid")
            self.session.results.surfaces.iso_surface["xmid"].field = "x-coordinate"
            self.session.results.surfaces.iso_surface["xmid"] = {"iso_values": [0]}

            self.graphics_session1 = pv.Graphics(self.session)
            self.contour1 = self.graphics_session1.Contours["contour-1"]
            self.contour1.field = "velocity-magnitude"
            self.contour1.surfaces_list = ["xmid"]
            self.contour1.display("window-1")

            contour2 = graphics_session1.Contours["contour-2"]
            contour2.field.allowed_values
            contour2.field = "pressure-coefficient"
            contour2.surfaces_list = ["xmid"]
            contour2.display("window-2")

        def save_case_files(self):

            
            # Save the case file
        
            save_case_data_as = Path(self.save_path) / "{self.di}.cas.h5"
            self.session.settings.file.write(file_type="case-data", file_name=str(save_case_data_as))

            self.session.exit()

        def run_solver(self):
            try:    
                self.start_solver()
                self.set_materials()
                self.set_BCs()
                self.set_RVs()
                self.set_solver_settings()
                self.set_report_defs()
                self.run_solver()
                self.save_case_files()
            except:
                send_update("meshing","meshing error")
            else:
                send_update("meshing","meshing successful")          


            
