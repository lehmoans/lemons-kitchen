from pathlib import Path
import ansys.fluent.core as pyfluent
import os
import psutil

#constants
from inputs import *

#updates
from updates import Updates

#misc
from misc import cleanup_fluent,_delete_exiting_threads
import uuid

"""
Code made using fluent api reference:
for meshing refer: 
    _datamodel = ansys.fluent.core.meshing
"""

class Mesh:

    def __init__(self,verbose=False,show_gui =False):
        self.save_dir  = SAVE_DIR
        self.scdoc_file_path= GEOM_FILE_PATH
        self.file_name_noext = os.path.basename(self.scdoc_file_path)
        head, tail = os.path.split(self.scdoc_file_path)
        self.dir_name = head
        self.save_path = Path(self.save_dir)
        self.processors = self.get_cores()
        self.verbose =verbose
        self.updates = Updates(self.verbose)
        self.show_gui = show_gui
        self.uuid=  uuid.uuid4()
        self.cleanup()

    def __exit__(self):
        pass
        self.cleanup()

    def cleanup(self):
        """
        cancels all threads/session when script is exited
        """

        #if self.session and self.session.
        try:
            if self.session:
                self.session.exit()
        except:
            print("no sessions to exit")


    @staticmethod
    def get_cores():
        return psutil.cpu_count(logical=False)
    
    def append_default_values(self, taskObject,variables:dict, write_txt = True):
        default_val_appended_dict = {}
        for key, value in variables.items():
            default_val = taskObject.Arguments.default_value(key)
            default_val_appended_dict[f"key"] = {"value": value, "default":default_val}

        if write_txt:
           file_path = f"default_values_appended_{self.uuid[-4:]}.txt"
           
           with open(file_path,"a") as file:
               file.write(default_val_appended_dict)
               file.close()

        
    def initialise(self):
        #fluent setup
        self.session = pyfluent.launch_fluent(mode="meshing",processor_count=self.processors, precision="double", show_gui = self.show_gui)
        print("fluent meshing initiated")

        
        # Meshing Workflow
        self.workflow =  self.session.workflow
        self.workflow.InitializeWorkflow(WorkflowType="Watertight Geometry")
        print("workflow initiated")

    def import_geom(self):

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

        """
        _datamodel.AddLocalSizingWTM
        or 
        
        self._add_local_sizing.Arguments.help()
        """
        
        self._add_local_sizing = self.workflow.TaskObject["Add Local Sizing"]

        for i in range(len(FACESIZES)):

            facesize = FACESIZES[i]
            #self.append_default_values(taskObject=self._add_local_sizing,variables= facesize)

            self._add_local_sizing.Arguments.set_state(
                {
                    "AddChild": "yes",
                    #"BOIExecution": "Face Size",
                    "BOIControlName": facesize["Name"],
                    "BOIGrowthRate": facesize["GrowthRate"],
                    #"BOISize":facesize["TargetMeshSize"], #mm
                    "BOIFaceLabelList": facesize["FaceLabelList"],
                }
             )
            self._add_local_sizing.AddChildAndUpdate()
        
        print("local sizings added")


    def create_surface_mesh(self):
        # Add Surface Mesh Sizing
        """
        _datamodel.AddLocalSizingWTM()
        """
        
        self.generate_surface_mesh = self.workflow.TaskObject["Generate the Surface Mesh"]
        self.generate_surface_mesh.Arguments = dict(
            {
                "CFDSurfaceMeshControls": {
                    "CurvatureNormalAngle": SURFACE_MESH_PARAMS["CurvatureNormalAngle"], 
                    "GrowthRate": SURFACE_MESH_PARAMS["GrowthRate"],
                    #"MaxSize": SURFACE_MESH_PARAMS["MaxSize"],
                    #"MinSize": SURFACE_MESH_PARAMS[ "MinSize"],
                    "SizeFunctions": SURFACE_MESH_PARAMS["SizeFunctions"],
                }
            }
        )
        self.generate_surface_mesh.Execute()
    def improve_sruface_mesh(self):

        #surface mesh improvement
        self.generate_surface_mesh.InsertNextTask(CommandName="ImproveSurfaceMesh")
        self.improve_surface_mesh = self.workflow.TaskObject["Improve Surface Mesh"]
        self.improve_surface_mesh.Arguments.update_dict({"FaceQualityLimit": MESH_FACE_QUALITY_LIMIT})
        self.improve_surface_mesh.Execute()

   
    def describe_geom(self):
            """
            _datamodel.GeometrySetup()
            """
            
            self.describe_geom=self.workflow.TaskObject["Describe Geometry"]

            self.describe_geom.Arguments = dict(
                CappingRequired="No",
                SetupType="The geometry consists of only fluid regions with no voids",
                InvokeShareTopology="Yes"
            )
            self.workflow.TaskObject["Describe Geometry"].Execute()

    def share_topology(self):
        """
        _datamodel.ShareTopology()
             self.s_topology.Arguments = dict(
            "GapDistance": ,#float
            "GapDistanceConnect":,#float
            "STMinSize":,#float
            "InterfaceSelect":,#str
            "EdgeLabelslist":,#[str]
            "ShareTopologyPreferences":,#dict[str, Any]
            "SMImprovePreferences":,#dict[str, Any]
            "SurfaceMeshPreferences":,#dict[str, Any]
        )
        """
        self.s_topology = self.workflow.TaskObject["Apply Share Topology"]
        self.gap_distance = self.s_topology.Arguments().default_value("GapDistance")*0.1

        self.s_topology.Arguments.updateDict({ "GapDistance":self.gap_distance})

        self.s_topology.Execute()
   
            
    def create_and_update_regions(self):
            self.workflow.TaskObject["Create Regions"].updateDict({"NumberOfFlowVolumes":2}).Execute()
            self.update_regions = self.workflow.TaskObject["Update Boundaries"]

            self.update_regions.Arguments()

            """
            _datamodel.UpdateRegions()
            """

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
            self.import_geom()
            self.add_local_sizings()
            self.create_surface_mesh()
            self.describe_geom()
            self.share_topology()
            self.create_and_update_regions()
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
    
    #cleanup exiting fluent threads
    cleanup_fluent()


    myMesh=Mesh()
    myMesh.run_meshing()

    
            

