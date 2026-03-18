import subprocess
import os

def check_path (path):
    base_dir = os.getcwd()
    abs_path = os.path.abspath(path)
    return abs_path.startswith(base_dir)

def list_files (args):
    if not check_path(args["directory_path"]):
        return {f"Error: You are not allowed to access {args['directory_path']}"}
    result =  subprocess.run(
        ["ls", args["directory_path"]],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()

def read_file_content (args):
    if not check_path(args["file_path"]):
        return {f"Error: You are not allowed to access {args['file_path']}"}
    result = subprocess.run(
        ["cat", args["file_path"]],
        capture_output=True,
        text=True
    )
    return result.stdout.strip()