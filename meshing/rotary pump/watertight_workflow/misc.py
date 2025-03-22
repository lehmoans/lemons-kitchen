import atexit
import psutil
import os
from pathlib import Path



def _delete_exiting_threads():
    for proc in psutil.process_iter(['pid', 'name']):
        if "fluent" in proc.info['name'].lower() or "mpi" in proc.info['name'].lower():
            try:
                os.kill(proc.info['pid'], 9)
                print(f"Killed Fluent process: {proc.info['name']} (PID: {proc.info['pid']})")
            except Exception as e:
                print(f"Error killing process {proc.info['name']}: {e}")

def cleanup_fluent():
    atexit.register(_delete_exiting_threads)


def write_sim_params(task, params:dict):
    """
    compiles all params specified or not in ansys
    """
    file_path = Path("sim_params.txt")
    if file_path.is_file():
        with open(file_path, "a") as file:

            file.write(f'task: {task}')
            for key, value in params.items():
                file.write(f'\t{key}: {value}')
            
            file.close()
    else:
        with open(file_path,"x") as file:
            file.write(f'task: {task}')
            for key, value in params.items():
                file.write(f'\t{key}: {value}')
            
            file.close()
    
    print("Task params of {task} added to {file_path}")



