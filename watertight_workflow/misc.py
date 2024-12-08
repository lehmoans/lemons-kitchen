import atexit
import psutil
import os



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

