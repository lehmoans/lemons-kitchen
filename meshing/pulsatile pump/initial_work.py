import ansys.fluent.core as pyfluent
import ansys.fluent.watertight as watertight
import os

# --- DEFINE GEOMETRY PARAMETERS ---
cylinder_radius = 0.02  # 20 mm
cylinder_height = 0.1  # 100 mm
mesh_filename = "heart_pump_mesh.msh"

# --- CREATE GEOMETRY & MESH USING WATERTIGHT WORKFLOW ---
print("🚀 Creating cylinder geometry and meshing...")

workflow = watertight.Workflow()
workflow.new_geometry()

# Create a simple cylinder (fluid domain)
geometry = workflow.geometry
cylinder = geometry.add_cylinder(
    base=(0, 0, 0),
    axis=(0, 0, 1),
    radius=cylinder_radius,
    height=cylinder_height,
    name="HeartPumpCylinder"
)

# Set meshing properties
workflow.mesh.automesh()
workflow.mesh.set_size(max_size=0.002)  # 2 mm mesh size
workflow.mesh.generate()

# Export the mesh
workflow.mesh.export_mesh(mesh_filename)
print(f"✅ Mesh saved as '{mesh_filename}'.")

# --- GENERATE UDF FOR PISTON MOTION ---
udf_code = """\
#include "udf.h"
#define FREQ 2.0  /* Piston frequency in Hz */
#define STROKE 0.02  /* Stroke length in meters */

DEFINE_CG_MOTION(piston_motion, dt, vel, omega, time, dtime)
{
    vel[1] = STROKE * 2.0 * M_PI * FREQ * cos(2.0 * M_PI * FREQ * time);
    omega[0] = 0.0; 
    omega[1] = 0.0;
    omega[2] = 0.0;
}
"""

udf_filename = "piston_motion.c"
with open(udf_filename, "w") as udf_file:
    udf_file.write(udf_code)

print("✅ UDF file 'piston_motion.c' has been generated.")

# --- FLUENT SIMULATION SETUP ---
print("🚀 Launching Fluent with GUI...")
fluent_session = pyfluent.launch_fluent(mode="solver", show_gui=True)
solver = fluent_session.solver

# Load mesh
solver.file.read(mesh_filename)

# Define materials
solver.setup.materials.create_fluid(name="Water", density=1000, viscosity=0.001)

# Set boundary conditions
solver.setup.boundary_conditions.set_velocity_inlet("inlet", velocity=0.0)
solver.setup.boundary_conditions.set_pressure_outlet("outlet", gauge_pressure=0)

# Enable dynamic mesh
solver.setup.dynamic_mesh.enable()
solver.setup.dynamic_mesh.set_smoothing_remeshing(smoothing="spring", remeshing=True)

# Compile and load UDF
print("⚙️ Compiling UDF...")
solver.file.compile_udf(udf_filename, output_directory="udf_compiled")
solver.setup.dynamic_mesh.set_cg_motion("piston", udf="piston_motion")

# Set time-stepping
solver.solution.set_time_step(0.001)
solver.solution.number_of_time_steps(500)
solver.solution.methods.set_piso_scheme()
solver.solution.controls.set_under_relaxation_factors(pressure=0.3, momentum=0.7)

# Run the simulation
print("🎬 Running simulation...")
solver.solution.run_calculation()

# Save results
solver.file.write_case_data("heart_pump_simulation.cas")
print("✅ Simulation complete. Case and data saved.")
