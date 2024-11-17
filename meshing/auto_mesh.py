import uuid
from typing import Optional, Union
import yaml
from marshmallow import Schema, fields, validate, ValidationError, post_load
import ansys.fluent.core as pyfluent
import os
import pathlib
from dataclasses import dataclass

import geometry_handler
import psutil


class AutoMesh:
    def __init__(self, precision, show_gui, geometry, scoped,
                 size_field, mesh):
        """
        Auto Mesh class, handles all required attributes.

        :param precision: (str) single or double.
        :param processors: (Int) number of cores to use.
        :param show_gui: (Bool) show fluent gui or not.
        :param geometry: (Geometry) class for geometry.
        :param scoped: (list[ScopedSizing]) list of scoped sizing's.
        :param size_field: (SizeField) size field class.
        :param mesh: (Mesh) mesh field class.
        """

        self.cwd = os.path.dirname(__file__)
        self.uuid = uuid.uuid4().hex[:5]
        self.working_folder = pathlib.Path(self.cwd) / f'automesh_{self.uuid}'
        self.working_folder.mkdir(exist_ok=False)

        self.journals = 'journals'
        self.journal_folder = self.working_folder.joinpath(self.journals)
        self.journal_folder.mkdir(exist_ok=False)

        self.precision = precision
        self.processors = self.cores_available()-2
        self.show_gui = show_gui

        self.geometry = geometry
        self.scoped = scoped
        self.size_field = size_field
        self.size_field_path = self.working_folder.joinpath(self.size_field.name).with_suffix(".sf")

        self.mesh = mesh

        self.mesh_file = None
        self.meshing = None
        self.tui = None

    def write_journal(self, command_name, command):
        """
        Write text to a journal file to be read.

        :param command_name:
        :param command:
        """
        save_file_path = os.path.join(self.journal_folder, f"{command_name}.jou")

        with open(save_file_path, "w+") as f:
            f.write(command)

        return save_file_path

    def run(self):
        """
        Run the meshing process.
        """
        self.meshing = pyfluent.launch_fluent(mode="meshing",
                                              precision=self.precision,
                                              processor_count=self.processors,
                                              show_gui=self.show_gui)

        self.tui = self.meshing.tui
        self.tui.file.read_journal(self.import_geometry())
        self.tui.file.read_journal(self.scoped_sizings())
        self.tui.file.read_journal(self.write_size_field(self.size_field_path))
        self.tui.file.read_journal(self.load_size_field(self.size_field_path))
        self.tui.file.read_journal(self.run_diagnostics())
        self.tui.file.read_journal(self.compute_mesh())
        self.tui.file.read_journal(self.auto_node_move())
        self.tui.file.read_journal(self.check_mesh())
        self.tui.file.read_journal(self.save_mesh())
        self.tui.exit()

    def import_geometry(self):
        """
        Imports geometry given filepath.

        :return:
        """

        file_path = self.geometry.name + '.' + self.geometry.type \
            if not self.geometry.name.endswith(self.geometry.type) else self.geometry.name

        command = geometry_handler.import_geometry(file_path)

        return self.write_journal("geometry_import", command)

    def scoped_sizings(self):
        """
        Applies scoped sizing's.

        :return:
        """

        journal = []

        deleted_old_scoped = f'''
        scoped-sizing delete-size-field
        '''

        journal.append(deleted_old_scoped)

        for item in self.scoped:
            if item.type == 'boi':
                journal.append(
                    self.boi_scoped_sizing(
                        item.name,
                        item.max,
                        item.growth,
                        item.zone
                    )
                )
            elif item.type == 'curve':
                journal.append(
                    self.curve_scoped_sizing(
                        item.name,
                        item.max,
                        item.growth,
                        item.curve,
                        item.zone
                    )
                )
            elif item.type == 'proximity':
                journal.append(
                    self.proximity_scoped_sizing(
                        item.name,
                        item.max,
                        item.growth,
                        item.cells,
                        item.zone
                    )
                )

        compute_sizings = f'''
        scoped-sizing compute
        '''

        journal.append(compute_sizings)

        command = '\n'.join(journal)

        return self.write_journal("scoped_sizing", command)

    @staticmethod
    def boi_scoped_sizing(name, max_size, growth, selection,
                          zone: str = 'face-zone'):
        """
        Apply a boi scoped sizing.

        :param name: name of sizing.
        :param max_size: maximum cell size.
        :param growth: growth rate.
        :param selection: list of regions to apply to.
        :param zone: zone to apply condition.
        :return:
        """

        selections = ' '.join(selection)

        command = f'''
        scoped-sizing create {name} boi {zone} yes no "{selections}" {max_size} {growth}
        '''

        return command

    @staticmethod
    def curve_scoped_sizing(name, max_size, growth, angle, selection,
                            zone: str = 'face-zone'):
        """
        Apply a curve scoped sizing.

        :param name: name of sizing.
        :param max_size: maximum cell size.
        :param growth: growth rate.
        :param angle: normal angle.
        :param selection: list of regions to apply to.
        :param zone: zone to apply condition.
        :return:
        """
        selections = ' '.join(selection)

        command = f'''
        scoped-sizing create {name} curvature {zone} yes no "{selections}" , {max_size} {growth} {angle}
        '''

        return command

    @staticmethod
    def proximity_scoped_sizing(name, max_size, growth, cells, selection,
                                zone: str = 'face-zone'):
        """
        Apply a curve scoped sizing.

        :param name: name of sizing.
        :param max_size: maximum cell size.
        :param growth: growth rate.
        :param cells: cells across face.
        :param selection: list of regions to apply to.
        :param zone: zone to apply condition.
        :return:
        """
        selections = ' '.join(selection)

        command = f'''
        scoped-sizing create {name} proximity {zone} yes no "{selections}" , {max_size} {growth} {cells} both no yes
        '''

        return command
    
    @staticmethod
    def cores_available(self):
        return psutil.cpu_count(logical=False)

    def write_size_field(self, name):
        command = f'''
        file write-size-field {name}
        '''

        return self.write_journal("write_sf", command)

    def load_size_field(self, name):
        if not name.exists():
            raise FileNotFoundError(f'Cannot find size field {name}.')

        command = f'''
        file/import/cad-options/tessellation cfd-surface-mesh yes "{name.resolve()}"
        file/import/cad , , , , , , mm ok
        '''

        return self.write_journal("read_sf", command)

    def run_diagnostics(self):
        command = f'''
        diagnostics/quality collapse objects * () skewness 0.9 40 15 yes q
        diagnostics/quality general-improve objects * () skewness 0.9 30 15 yes q
        diagnostics/quality delaunay-swap objects * () 0.9 40 15 yes q
        diagnostics/quality smooth objects * () 15 yes q
        '''

        return self.write_journal("run_diagnostics", command)

    def compute_mesh(self):

        zones = ' '.join(self.mesh.zone)

        command = f'''
        objects/volumetric-regions compute fluid_domain:fluid_domain-enclosure no
        objects/volumetric-regions change-type fluid_domain:fluid_domain-enclosure "rocket_body" () dead
        mesh/scoped-prisms create rocket_inf uniform {self.mesh.initial_layer} {self.mesh.layers} {self.mesh.growth} fluid_domain:fluid_domain-enclosure fluid-regions selected-face-zones "{zones}"
        mesh/auto-mesh fluid_domain:fluid_domain-enclosure no scoped pyramids poly-hexcore yes
        '''

        return self.write_journal("mesh", command)

    def auto_node_move(self):
        command = f'''
        mesh/modify/auto-node-move "*" "*" , , , , 10
        '''

        return self.write_journal("auto_node_move", command)

    def check_mesh(self):
        command = f'''
        mesh check-mesh
        '''

        return self.write_journal("get_summary", command)

    def save_mesh(self):
        self.mesh_file = self.working_folder.joinpath(f'{self.mesh.name}_{self.uuid}').with_suffix(".msh")

        command = geometry_handler.write_mesh(self.mesh_file)

        return self.write_journal("save_mesh", command)


def validate_greater_than(n, num):
    if n <= num:
        raise ValidationError(f'{n} must be greater than {num}')


class GeometrySchema(Schema):
    name = fields.Str()
    type = fields.Str(validate=validate.OneOf(["scdoc", "pmdb"]))

    @post_load
    def make_user(self, data, **kwargs):
        return Geometry(**data)


@dataclass
class Geometry:
    name: str
    type: str


class ScopedSizingSchema(Schema):
    name = fields.Str()
    type = fields.Str(validate=validate.OneOf(["boi", "proximity", "curve"]))
    max = fields.Int(validate=lambda x: validate_greater_than(x, 0))
    growth = fields.Float(validate=lambda x: validate_greater_than(x, 1))
    cells = fields.Int(validate=lambda x: validate_greater_than(x, 0), required=False)
    curve = fields.Int(validate=lambda x: validate_greater_than(x, 0), required=False)
    zone = fields.List(fields.Str())

    @post_load
    def make_user(self, data, **kwargs):
        return ScopedSizing(**data)


@dataclass
class ScopedSizing:
    name: str
    type: str
    max: Union[int, None]
    growth: Union[int, None]
    zone: list[str]
    cells: Optional[int] = None
    curve: Optional[int] = None


class SizeFieldSchema(Schema):
    name = fields.Str()

    @post_load
    def make_user(self, data, **kwargs):
        return SizeField(**data)


@dataclass
class SizeField:
    name: str


class MeshSchema(Schema):
    name = fields.Str()
    initial_layer = fields.Float()
    layers = fields.Int()
    growth = fields.Float()
    zone = fields.List(fields.Str())

    @post_load
    def make_user(self, data, **kwargs):
        return Mesh(**data)


@dataclass
class Mesh:
    name: str
    initial_layer: float
    layers: int
    growth: float
    zone: list[str]

#parses the yaml
class AutoMeshSchema(Schema):
    precision = fields.Str(validate=validate.OneOf(['double', 'single']))
    processors = fields.Int(validate=lambda x: validate_greater_than(x, 0))
    show_gui = fields.Bool()
    scoped = fields.List(fields.Nested(ScopedSizingSchema))
    geometry = fields.Nested(GeometrySchema)
    size_field = fields.Nested(SizeFieldSchema)
    mesh = fields.Nested(MeshSchema)

    @post_load
    def make_user(self, data, **kwargs):
        return AutoMesh(**data)


if __name__ == "__main__":
    with open("../Resources/AutoMeshConfigs/auto_mesh_config.yaml") as auto_mesh_config:
        schema = yaml.full_load(auto_mesh_config)

    print(schema)
