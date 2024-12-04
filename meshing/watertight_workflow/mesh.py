from pathlib import Path
import ansys.fluent.core as pyfluent
import os
import psutil

#constants
from inputs import *

#updates
from updates import Updates

#admin privilege
import pyuac

class Mesh:

    def __init__(self,verbose=False):
        self.save_dir  = SAVE_DIR
        self.scdoc_file_path= GEOM_FILE_PATH
        self.file_name_noext = os.path.basename(self.scdoc_file_path)
        head, tail = os.path.split(self.scdoc_file_path)
        self.dir_name = head
        self.save_path = Path(self.save_dir)
        self.processors = self.get_cores()
        self.verbose =verbose
        self.updates = Updates(self.verbose)


    def __exit__(self):
        if self.session:
            self.session.exit()

    @staticmethod
    def get_cores():
        return psutil.cpu_count(logical=False)

        
    def initialise(self):
        #fluent setup
        self.session = pyfluent.launch_fluent(mode="meshing",processor_count=self.processors, precision="double", show_gui = True)
        print("fluent meshing initiated")

    def start_workflow(self):

        # Meshing Workflow
        self.workflow =  self.session.workflow
        self.workflow.InitializeWorkflow(WorkflowType="Watertight Geometry")


        self.workflow.TaskObject['Import Geometry'].Arguments = {
            'FileFormat': 'CAD', #[CAD, Mesh]
            'ImportType': 'Single File', # ['Single File', 'Multiple Files']
            'LengthUnit': 'mm', # ['mm', 'm', 'cm', 'in', 'ft', 'um', 'nm'] 
            'UseBodyLabels': 'No', # ['No', 'Yes']
            'FileName': self.scdoc_file_path
        }

        self.workflow.TaskObject["Import Geometry"].Execute()

    def add_local_sizings(self):
        # Add Local Face Sizing
        
        self.add_local_sizing = self.workflow.TaskObject["Add Local Sizing"]

        for i in range(len(FACESIZES)):
            facesize = FACESIZES[i]
            self.add_local_sizing.Arguments = dict(
                {
                    "AddChild": "yes",
                    "SizeControlType": "FaceSize",
                    "Name": facesize["Name"],
                    "GrowthRate": facesize["GrowthRate"],
                    "TargetMeshSize":facesize["TargetMeshSize"], #mm
                    "FaceLabelList": facesize["BOIFaceLabelList"],
                }
             )
            self.add_local_sizing.Execute()


    def add_BOI(self):
        # Add BOI (Body of Influence) Sizing 
        #dummy function, not needed for MHH sims
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

    def create_surface_mesh(self):
        # Add Surface Mesh Sizing
        
        self.generate_surface_mesh = self.workflow.TaskObject["Generate the Surface Mesh"]
        self.generate_surface_mesh.Arguments = dict(
            {
                "CFDSurfaceMeshControls": {
                    "CurvatureNormalAngle": SURFACE_MESH_PARAMS["CurvatureNormalAngle"], 
                    "GrowthRate": SURFACE_MESH_PARAMS["GrowthRate"],
                    "MaxSize": SURFACE_MESH_PARAMS["MaxSize"],
                    "MinSize": SURFACE_MESH_PARAMS[ "MinSize"],
                    "SizeFunctions": SURFACE_MESH_PARAMS["SizeFunctions"],
                }
            }
        )
        self.generate_surface_mesh.Execute()

        #surface mesh improvement
        self.generate_surface_mesh.InsertNextTask(CommandName="ImproveSurfaceMesh")
        self.improve_surface_mesh = self.workflow.TaskObject["Improve Surface Mesh"]
        self.improve_surface_mesh.Arguments.update_dict({"FaceQualityLimit": MESH_FACE_QUALITY_LIMIT})
        self.improve_surface_mesh.Execute()

   
    def describe_geom(self):
            self.workflow.TaskObject["Describe Geometry"].Arguments = dict(
                CappingRequired="No",
                SetupType="The geometry consists of only fluid regions with no voids",
                ShareTopolgy="Yes"
            )
            self.workflow.TaskObject["Describe Geometry"].Execute()
            self.workflow.TaskObject["Create Regions"].Execute()
            

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
            self.updates.send_update("meshing","meshing error")
        else:
             self.updates.send_update("meshing","meshing successful")            


if __name__ =="__main__":

    #root_path= "D://ANSYS_V241/'Ansys Inc'/v241"#"Path(r"D://ANSYS_V241/'Ansys Inc'/v241")
    #set the "ANSYS_FLUENT_PATH" environment variable in computer, might have to set it to .profile in uni computer:  echo 'export "ANSYS_FLUENT_PATH"="D://ANSYS_V241/'Ansys Inc'/v241"' >>~/.profile
    #or set the inputs for pyfluent(fluent_path = "")

    #os.environ["ANSYS_FLUENT_PATH"] = "D://ANSYS_V241/'Ansys Inc'/v241/fluent"
    myMesh=Mesh()
    myMesh.run_meshing()

    
            

