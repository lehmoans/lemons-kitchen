##mesh inputs
GEOM_FILE_PATH="D://CFD_tui/enclosures.scdoc"
SAVE_DIR="D://CFD_tui/save_dir" 

#groups set in spaceclaim
ROT_GRP:str="rot_group"
STAT_GRP:str="stat_group"
BLADES_GRP = "blades"
WALLS:list|str = ["rot_walls","stat_walls"]
INLET_NAME:str="inlet"
OUTLET_NAME:str="outlet"
ENCLOSURES = ["stat_vol","rot_vol"]


#local sizing
#face sizing:
FACESIZES = {
        1:
        { 
            "Name": "facesize_blades",
            "GrowthRate": 1.15,
            "TargetMeshSize":-1,
             "FaceLabelList": [BLADES_GRP],
        },
}

SURFACE_MESH_PARAMS={
    "CurvatureNormalAngle": 12,
    "GrowthRate": 1.15,
    "MaxSize": 50,
    "MinSize": 1,
    "SizeFunctions": "Curvature & Proximity", #Curvature & Proximity, Curvature, Proximity
    "CellsPerGaps": 3,
    "ScopeProximityTo": "edges" #faces, faces-and-edges
}

#mesh dets
MESH_FACE_QUALITY_LIMIT=0.4
MESH_CELL_TYPE="polyhexacore"

#BL
BL_TYPE=""
NUMBER_OF_LAYERS=0
GROWTH_RATE=0
TRANSITION_RATIO=0

#material
DENSITY=2000

#Turbulence conditions:
TURB_INTENSITY_INLET=0.5
TURB_INTENSITY_OUTLET=0.5

TURB_VISCOCITY_RATIO=0.5


#BCs
## INLET
INLET_PRESSURE=0
INLET_AREA=0

##OUTLET
OUTLET_MASSRATE=0

RESIDUAL_CRITERIA=0.0001

#for discord updates:
DISCORD_WEBHOOK =  "https://discord.com/api/webhooks/1307534355232587817/V3ZqQXFCrOEoA0477lQj3-EccHeztedK2K4DiNWYFcy-2z9VEtN-l5yYvia2uGKr4QHd"




