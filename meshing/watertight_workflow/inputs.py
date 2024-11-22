##mesh inputs
GEOM_FILE_PATH=""
SAVE_DIR=""

#groups set in spaceclaim
BLADE_GRP=""
VOLUTE_WALL_GRP=""
INLET_NAME=""
OUTLET_NAME=""


#local sizing
LOCAL_SIZING_DICT=\
{"localsize1": 
        {"AddChild": "yes",
        "BOIControlName": "facesize_front",
        "BOIFaceLabelList": [BLADE_GRP, VOLUTE_WALL_GRP],
        "BOIGrowthRate": 1.15,
        "BOISize": 8,
            },
"localsize2":{}}

#mesh dets
MESH_CELL_TYPE=""


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




