import os
import pathlib


def import_geometry(file_path: os.PathLike,
                    length_unit: str = 'mm',
                    tessellation_method: str = 'cad-faceting',
                    refine_faceting: str = 'no'):
    """
    Import a cad geometry.

    :param refine_faceting: (str)
    :param file_path: (os.Pathlike)
    :param length_unit: (str)
    :param tessellation_method: (str)
    :return:
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} not found.")

    command = f'''
    file/import cad-geometry yes {file_path} {length_unit} {tessellation_method} {refine_faceting}
    '''
    return command


def save_pmdb(file_path: os.PathLike, iteration,
                    length_unit: str = 'mm',
                    tessellation_method: str = 'cad-faceting',
                    refine_faceting: str = 'no'):
    """
    Import a cad geometry and save a PMDB intermediate file.

    :param refine_faceting: (str)
    :param iteration: (int) used for preventing appending/overwriting of geometries when importing
    :param file_path: (os.Pathlike)
    :param length_unit: (str)
    :param tessellation_method: (str)
    :return:
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} not found.")

    append = 'no' if iteration != 0 else ""
    overwrite = 'ok' if iteration != 0 else ""

    command = f'''
    /file import cad-options save-PMDB y
    /file import cad-geometry yes {file_path} {append} {length_unit} {tessellation_method} {refine_faceting} {overwrite}
    '''
    return command


def import_mesh(file_path: os.PathLike, iteration):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} not found.")

    answer = 'ok' if iteration != 0 else ""

    command = f'''
    file read-mesh {file_path} {answer}
    '''

    return command


def write_mesh(file_path: pathlib.Path):
    file_path = file_path.with_suffix('.msh')

    command = f'''
    preferences general default-ioformat "Legacy"
    file write-mesh {file_path}
    '''

    return command
