import ansys.fluent.core as pyfluent

# launch meshing
meshing = pyfluent.launch_fluent(
    mode="meshing",
    precision=pyfluent.Precision.DOUBLE,
    processor_count=4,
    cleanup_on_exit=False,
    ui_mode="gui",
    py=True
)
wt=meshing.watertight()
# =============================================================================
# Import geometry
# =============================================================================
# probably need full path here
wt.import_geometry.file_name.set_state("diffuser.scdoc") #scdocs only work for Windows machines
wt.import_geometry.length_unit.set_state('m')
wt.import_geometry()

# =============================================================================
# Local Sizing: 2 different ways to add sizing - method 2 preferred
# =============================================================================

# sizing 1
# wt.add_local_sizing.boi_control_name.default_value() # to get default values
wt.add_local_sizing.add_child = "yes"
wt.add_local_sizing.boi_control_name = 'face_size_1'
wt.add_local_sizing.boi_growth_rate = 1.2
wt.add_local_sizing.boi_execution = 'Face Size' #wt.add_local_sizing.boi_execution.allowed_values() to get allowed values
wt.add_local_sizing.boi_size = 0.01
wt.add_local_sizing.boi_zoneor_label = 'label'
wt.add_local_sizing.boi_face_label_list = ["sa_1.1","sa_1.2","sa_1.3","sa_1.4"]
wt.add_local_sizing.add_child_and_update()

# sizing 2 - using state
added_sizing_2 = wt.add_local_sizing.add_child_and_update(
    state={
        "boi_control_name":'face_size_3',
        "boi_growth_rate": 1.2,
        "boi_execution": 'Face Size',
        "boi_size": 0.02,
        "boi_zoneor_label": 'label',
        "boi_face_label_list": ["diff-1-wall", "diff-2-wall"], 
    }
)
# modify and execute sizing to change name
added_sizing_2.boi_control_name = "face_size_2"
added_sizing_2.execute()

# =============================================================================
# Surface Mesh
# =============================================================================
surf_mesh = wt.create_surface_mesh

# default values for surface mesh with .default_value() method
surf_mesh.cfd_surface_mesh_controls.min_size.default_value()
surf_mesh.cfd_surface_mesh_controls.max_size.default_value()
surf_mesh.cfd_surface_mesh_controls.growth_rate()
surf_mesh.cfd_surface_mesh_controls.size_functions.default_value()
surf_mesh.cfd_surface_mesh_controls.curvature_normal_angle.default_value()
surf_mesh.cfd_surface_mesh_controls.cells_per_gap.default_value()
surf_mesh.cfd_surface_mesh_controls.scope_proximity_to.default_value()

# actual sizings that are implemented
surf_mesh.cfd_surface_mesh_controls = {
    'min_size': 0.002,
    'max_size': 0.35,
    'growth_rate': 1.2,
    'size_functions': 'Curvature & Proximity',
    'curvature_normal_angle': 18,
    'cells_per_gap': 3,
    'scope_proximity_to': 'edges'
}
wt.create_surface_mesh()

# =============================================================================
# Describe geometry
# =============================================================================
# check for allowed values with the .allowed_values() method
wt.describe_geometry.setup_type.allowed_values()
# default values with .default_value()
wt.describe_geometry.setup_type.default_value()
wt.describe_geometry.capping_required.default_value()
wt.describe_geometry.wall_to_internal.default_value()
wt.describe_geometry.invoke_share_topology.default_value()
wt.describe_geometry.multizone.default_value()

# actual values
wt.describe_geometry.setup_type = 'The geometry consists of only fluid regions with no voids'
wt.describe_geometry.wall_to_internal = 'Yes'
wt.describe_geometry.invoke_share_topology = 'No'
wt.describe_geometry.multizone = 'Yes'
wt.describe_geometry()



# =============================================================================
# Update boundaries
# =============================================================================
# This update and revert is needed to populate the default boundary_current_list and boundary_current_type_list variables.
wt.update_boundaries()
wt.update_boundaries.revert()
# Use wt.update_boundaries.arguments() to list available arguments
boundary_names= wt.update_boundaries.boundary_current_list() # lists names of current boundaries
boundary_types = wt.update_boundaries.boundary_current_type_list() # list boundary types (same order as above boundary_current_list)
# wt.update_boundaries.boundary_current_type_list.default_value() # for default values similar to the above
########## have to update the full state
new_boundary_types = boundary_types
# change all supply air boundaries to vel-inlets
for i, (name, _) in enumerate(zip(boundary_names, boundary_types)):
    # Check if the name starts with "sa" 
    if name.startswith("sa"):
        # Update the corresponding boundary type
        new_boundary_types[i] = 'velocity-inlet'

# need to convert boundary names and types into a regular list
boundary_names = [item for item in boundary_names]
boundary_types = [item for item in boundary_types]
new_boundary_types = [item for item in new_boundary_types]

# Modify boundaries
wt.update_boundaries.boundary_label_list.set_state(boundary_names)
wt.update_boundaries.boundary_label_type_list.set_state(new_boundary_types)
wt.update_boundaries.old_boundary_label_list.set_state(boundary_names)
wt.update_boundaries.old_boundary_label_type_list.set_state(boundary_types)

wt.update_boundaries()
# =============================================================================
# Update Regions
# =============================================================================
# wt.update_regions.arguments() lists out all available arguments.
# use region_current_list and region_current_list_type list them out
wt.update_regions()

# =============================================================================
# Boundary layers (2 different ways to add sizing) - method 2 preferred
# =============================================================================
# layer 1
wt.add_boundary_layer.add_child = "yes"
wt.add_boundary_layer.bl_control_name = "bl-1"
wt.add_boundary_layer.number_of_layers = 5
wt.add_boundary_layer.transition_ratio = 0.272
wt.add_boundary_layer.rate = 1.2
wt.add_boundary_layer.face_scope.regions_type = 'fluid-regions' # or use only-walls (no need bl_label_list definition if that's used)
wt.add_boundary_layer.face_scope.grow_on = 'selected-labels'
wt.add_boundary_layer.bl_label_list = ['diff-1-wall']
wt.add_boundary_layer.add_child_and_update(defer_update=False) # add the task

# layer 2
layer_2 = wt.add_boundary_layer.add_child_and_update(
    state={
        'bl_control_name': "bl-2",
        'number_of_layers': 5,
        'transition_ratio': 0.272,
        'rate': 1.2,
        'face_scope': {
            'regions_type': 'fluid-regions',
            'grow_on': 'selected-labels'
        },
        'bl_label_list': ['diff-2-wall']
    }
)

# =============================================================================
# Volume mesh 
# =============================================================================
wt.create_volume_mesh.volume_fill.set_state("polyhedra")
wt.create_volume_mesh.volume_fill_controls.max_size = 0.3
wt.create_volume_mesh()

# write out file
meshing.meshing.File.WriteMesh(FileName="room1.msh.h5")
print("End of file")