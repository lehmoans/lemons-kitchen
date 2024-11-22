from pathlib import Path

import ansys.fluent.core as pyfluent
from ansys.fluent.core import examples
from ansys.fluent.visualization import set_config
import ansys.fluent.visualization.pyvista as pv
import os
import psutil

#constants
from inputs import *

#updates
from meshing.updates import send_update

class Mesh:

    def __init__(self):
        self.save_dir  = SAVE_DIR
        self.scdoc_file_path= GEOM_FILE_PATH
        self.file_name_noext = os.path.basename(self.scdoc_file_path)
        self.dir_name = os.cwd(self.scdoc_file_path)
        self.save_path = Path(self.save_dir)
        self.processors = self.get_cores()

    @staticmethod
    def get_cores():
        return psutil.cpu_count(logical=False)

        
    def initialise(self):
        set_config(blocking=True, set_view_on_display="isometric")

        #fluent setup
        self.session = pyfluent.launch_fluent(mode="meshing",processor_count=self.processors, cleanup_on_exit=True)
        print(self.session.get_fluent_version())

    def start_workflow(self):

        # Meshing Workflow
        self.workflow = self.session.workflow
        self.geometry_filename = examples.download_file(
            self.scdoc_file_path,
            self.dir_name,
            save_path=self.save_dir,
        )
        self.workflow.InitializeWorkflow(WorkflowType="Watertight Geometry")
        self.workflow.TaskObject["Import Geometry"].Arguments = dict(FileName=self.geometry_filename)
        self.workflow.TaskObject["Import Geometry"].Execute()

    def add_local_sizings(self):
        # Add Local Face Sizing
        
        self.add_local_sizing = self.workflow.TaskObject["Add Local Sizing"]
        self.add_local_sizing.Arguments = dict(
            {
                "AddChild": "yes",
                "BOIControlName": "facesize_front",
                "BOIFaceLabelList": ["wall_ahmed_body_front"],
                "BOIGrowthRate": 1.15,
                "BOISize": 8,
            }
    )
        self.add_local_sizing.Execute()

        self.add_local_sizing.InsertCompoundChildTask()
        self.workflow.TaskObject["Add Local Sizing"].Execute()
        self.add_local_sizing =self.workflow.TaskObject["Add Local Sizing"]
        self.add_local_sizing.Arguments = dict(
            {
                "AddChild": "yes",
                "BOIControlName": "facesize_rear",
                "BOIFaceLabelList": ["wall_ahmed_body_rear"],
                "BOIGrowthRate": 1.15,
                "BOISize": 5,
            }
        )
        self.add_local_sizing.Execute()

        self.add_local_sizing.InsertCompoundChildTask()
        self.workflow.TaskObject["Add Local Sizing"].Execute()
        self.add_local_sizing = self.workflow.TaskObject["Add Local Sizing"]
        self.add_local_sizing.Arguments = dict(
            {
                "AddChild": "yes",
                "BOIControlName": "facesize_main",
                "BOIFaceLabelList": ["wall_ahmed_body_main"],
                "BOIGrowthRate": 1.15,
                "BOISize": 12,
            }
        )
        self.add_local_sizing.Execute()

        # Add BOI (Body of Influence) Sizing
        add_boi_sizing = self.workflow.TaskObject["Add Local Sizing"]
        add_boi_sizing.InsertCompoundChildTask()
        add_boi_sizing.Arguments = dict(
            {
                "AddChild": "yes",
                "BOIControlName": "boi_1",
                "BOIExecution": "Body Of Influence",
                "BOIFaceLabelList": ["ahmed_body_20_0degree_boi_half-boi"],
                "BOISize": 20,
            }
        )
        add_boi_sizing.Execute()
        add_boi_sizing.InsertCompoundChildTask()


    def create_surface_mesh(self):
        # Add Surface Mesh Sizing
        
        self.generate_surface_mesh = self.workflow.TaskObject["Generate the Surface Mesh"]
        self.generate_surface_mesh.Arguments = dict(
            {
                "CFDSurfaceMeshControls": {
                    "CurvatureNormalAngle": 12,
                    "GrowthRate": 1.15,
                    "MaxSize": 50,
                    "MinSize": 1,
                    "SizeFunctions": "Curvature",
                }
            }
        )

        self.generate_surface_mesh.Execute()
        self.generate_surface_mesh.InsertNextTask(CommandName="ImproveSurfaceMesh")
        self.improve_surface_mesh = self.workflow.TaskObject["Improve Surface Mesh"]
        self.improve_surface_mesh.Arguments.update_dict({"FaceQualityLimit": 0.4})
        self.improve_surface_mesh.Execute()

   
    def describe_geom(self):
            self.workflow.TaskObject["Describe Geometry"].Arguments = dict(
                CappingRequired="Yes",
                SetupType="The geometry consists of only fluid regions with no voids",
            )
            self.workflow.TaskObject["Describe Geometry"].Execute()
            self.workflow.TaskObject["Update Boundaries"].Execute()
            self.workflow.TaskObject["Update Regions"].Execute()

    def add_BL(self):
        # Add Boundary Layers
    
        self.add_boundary_layers = self.workflow.TaskObject["Add Boundary Layers"]
        self.add_boundary_layers.AddChildToTask()
        self.add_boundary_layers.InsertCompoundChildTask()
        self.workflow.TaskObject["smooth-transition_1"].Arguments.update_dict(
            {
                "BLControlName": "smooth-transition_1",
                "NumberOfLayers": NUMBER_OF_LAYERS,
                "Rate": GROWTH_RATE,
                "TransitionRatio": TRANSITION_RATIO,
            }
        )
        self.add_boundary_layers.Execute()


    def generate_volume_mesh(self):
    # Generate the Volume Mesh
    
        self.generate_volume_mesh = self.workflow.TaskObject["Generate the Volume Mesh"]
        self.generate_volume_mesh.Arguments.update_dict({"VolumeFill": "poly-hexcore"})
        self.generate_volume_mesh.Execute()

    def save_mesh(self):
        pass
    
    def mesh_to_solver(self):
        # Switch to the Solver Mode
        self.session = self.session.switch_to_solver()

    def run_meshing(self):
        try:
            self.initialise()
            self.start_workflow()
            self.add_local_sizings()
            self.create_surface_mesh()
            self.describe_geom()
            self.add_BL()
            self.generate_volume_mesh()
            self.save_mesh()
            self.session.exit()
        except:
            send_update("meshing","meshing error")
        else:
            send_update("meshing","meshing successful")            

    
