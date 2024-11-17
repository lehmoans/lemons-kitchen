# Auto Mesher
This script is designed to run both locally and on monarch. It will automatically mesh
a geometry for you. 

### Running
```
usage: run_auto_mesh.py [-h] [--config CONFIG] [--root ROOT]

optional arguments:
  --config CONFIG
  --root ROOT
```

- config: path to your auto mesh config.
- root: root to fluent (monarch: /usr/local/ansys/23r1/ansys_inc/v231/fluent)

### Important
You cannot run with ```scdoc``` files on monarch, instead you have to convert the geometry
on fluent locally, and import with an extra setting.

- Open the scdoc on windows fluent meshing.
- Import Cad. In the import settings, bottom right, tick the box make intermediate pmdb file.
- You can use the pmdb file on monarch.