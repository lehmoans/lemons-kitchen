from pathlib import Path
import ansys.fluent.core as pyfluent
import os
import psutil

#constants
from inputs import *

#updates
from updates import Updates

#misc
from misc import *
import uuid

"""
Code made using fluent api reference:
for meshing refer: 
    _datamodel = ansys.fluent.core.meshing
"""

class Mesh:

    def __init__(self,verbose=False,show_gui =True):
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

    @staticmethod
    def get_cores():
        return psutil.cpu_count(logical=False)
    def load_workflow(self, step = None):
        pass
        
        
    def initialise(self):
        #fluent setup
        self.session= pyfluent.launch_fluent(
            mode="meshing",
            precision=pyfluent.Precision.DOUBLE,
            processor_count=self.processors,
            cleanup_on_exit=False,
            ui_mode="gui" if self.show_gui else None,
            py=True
        )   
        self.workflow = self.session.watertight()
        print("workflow initiated")
        return True

    def import_geom(self):
        self.import_geom = self.workflow.import_geometry

        #params
        self.import_geom.file_name.set_state(GEOM_FILE_PATH) #scdocs only work for Windows machines
        #self.import_geom.file_format.set_state("CAD")
        self.import_geom.length_unit.set_state('mm')
        self.import_geom()

    def add_local_sizings(self):
        # Add Local Face Sizing

        """
        _datamodel.AddLocalSizingWTM
        or 
        
        self._add_local_sizing.Arguments.help()
        """
        
        self.add_local_sizing = self.workflow.add_local_sizing

        for i in range(len(FACESIZES)):

            facesize = FACESIZES[i]
            #self.append_default_values(taskObject=self._add_local_sizing,variables= facesize)
            self.add_local_sizing.add_child = "yes"
            self.add_local_sizing.boi_execution = 'Face Size' #wt.add_local_sizing.boi_execution.allowed_values() to get allowed values
            self.add_local_sizing.boi_zoneor_label = 'label'


            self.add_local_sizing.boi_control_name = facesize["Name"]
            #self.add_local_sizing.boi_growth_rate =  facesize["GrowthRate"]
            #self.add_local_sizing.boi_size =  facesize["TargetMeshSize"]
            self.add_local_sizing.boi_face_label_list =  facesize["FaceLabelList"]


            self.add_local_sizing.add_child_and_update()

        
        print("local sizings added")


    def create_surface_mesh(self):
        # Add Surface Mesh Sizing
        """
        _datamodel.AddLocalSizingWTM()
        """
        
        self.generate_surface_mesh = self.workflow.create_surface_mesh
        self.surf_mesh_controls =  self.generate_surface_mesh.cfd_surface_mesh_controls
        #ASSIGNS DEFAULT VALUES TO THE PARAMS
        self.surf_mesh_controls.min_size.default_value()
        self.surf_mesh_controls.max_size.default_value()
        self.surf_mesh_controls.growth_rate()                                                                           #check
        self.surf_mesh_controls.size_functions.default_value()
        self.surf_mesh_controls.curvature_normal_angle.default_value()
        self.surf_mesh_controls.cells_per_gap.default_value()
        self.surf_mesh_controls.scope_proximity_to.default_value()

        sim_params = self.surf_mesh_controls.get_state()

        write_sim_params(self.create_surface_mesh, sim_params)


        self.generate_surface_mesh()
        return True

   
    def describe_geom(self):
            """
            _datamodel.GeometrySetup()
            """
            
            self.describe_geom=self.workflow.describe_geometry

            self.describe_geom.setup_type = "The geometry consists of only fluid regions with no voids"
            self.describe_geom.capping_required = "No"
            self.describe_geom.wall_to_internal = "Yes"
            self.describe_geom.invoke_share_topology = "No"
            self.describe_geom.multizone = "No"

            self.describe_geom()
            return True
            
            

    def invoke_share_topology(self):
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
    """
        if not self.describe_geom.invoke_share_topology:
            return False
        
        self.share_topology = self.workflow.apply_share_topology
        self.share_topology.gap_distance.default_value()

        sim_params = self.share_topology.get_state() #get default values from here then adjust according to 
        self.share_topology()
        return True


    def update_boundaries_and_regions(self):
        #update boundaries
        """
        allowed boundary types: 
            velocity-inlet, pressure-outlet, pressure-inlet, pressure-far-field, mass-flow-inlet, mass-flow-outlet, 
            outflow, symmetry, wall, internal, interface, overset, outlet-vent, intake-fan, inlet-vent, exhaust-fan, 
            porous-jump, fan, radiator, multiple-types
        """
        self.update_boundaries = self.workflow.update_boundaries

        self.update_boundaries()
        self.update_boundaries.revert()

        boundaries_args = self.update_boundaries.arguments()

        boundary_list = self.update_boundaries.boundary_current_list()
        boundary_types = self.update_boundaries.boundary_current_type_list()

        new_boundary_types = boundary_types

        for i, (name, _) in enumerate(zip(boundary_list, boundary_types)):
            if name == "inlet":
                new_boundary_types[i] ='pressure-inlet'
            elif name == 'outlet':
                new_boundary_types[i] ='mass-flow-outlet'
        
        boundary_list = [i for i in boundary_list]
        boundary_types = [i for i in boundary_types]
        new_boundary_types = [i for i in new_boundary_types]

        #self.update_boundaries

        """
        _datamodel.UpdateRegions()
        """

        self.update_regions = self.workflow.update_regions
        self.update_regions()

        self.update_regions.region_current_list.default_value()
        self.update_regions.region_current_type_list.default_value()

        region_list = self.update_regions.region_current_list()
        region_types = self.update_regions.region_current_type_list()

        #iterate through and weed out non-fluid regions. should only be two fluid regions 
        
    def update_boundaries(self):
        pass
           
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
        self.initialise()
        self.import_geom()
        self.add_local_sizings()
        self.create_surface_mesh()
        self.describe_geom()
        self.invoke_share_topology()
        self.update_regions()
        self.update_boundaries()
        self.add_BL()
        self.generate_volume_mesh()
        self.save_mesh()
        self.session.exit()      


if __name__ =="__main__":

    #root_path= "D://ANSYS_V241/'Ansys Inc'/v241"#"Path(r"D://ANSYS_V241/'Ansys Inc'/v241")
    #set the "ANSYS_FLUENT_PATH" environment variable in computer, might have to set it to .profile in uni computer:  echo 'export "ANSYS_FLUENT_PATH"="D://ANSYS_V241/'Ansys Inc'/v241"' >>~/.profile
    #or set the inputs for pyfluent(fluent_path = "")

    os.environ["ANSYS_FLUENT_PATH"] = "D:/'ANSYS Inc'/v241/fluent"
    
    #cleanup exiting fluent threads
    cleanup_fluent()


    myMesh=Mesh()
    myMesh.run_meshing()

    
            

