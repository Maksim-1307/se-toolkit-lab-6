import subprocess
import os
import requests
import json

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

def query_api(args):
    """Query the deployed backend API with authentication.
    
    Args:
        args: dict with 'method', 'path', and optional 'body'
        
    Returns:
        JSON string with 'status_code' and 'body' fields
    """
    method = args.get("method", "GET").upper()
    path = args.get("path")
    body = args.get("body")
    
    if not path:
        return json.dumps({"status_code": 400, "body": {"error": "Missing 'path' parameter"}})
    
    # Read API base URL from environment (with default)
    api_base = os.getenv("AGENT_API_BASE_URL", "http://localhost:42002")
    url = f"{api_base}{path}"
    
    # Read LMS API key for authentication
    lms_api_key = os.getenv("LMS_API_KEY")
    
    headers = {}
    if lms_api_key:
        headers["Authorization"] = f"Bearer {lms_api_key}"
    
    try:
        # Prepare request body if provided
        json_body = None
        if body:
            try:
                json_body = json.loads(body)
            except json.JSONDecodeError:
                return json.dumps({"status_code": 400, "body": {"error": "Invalid JSON in body"}})
        
        # Make the request
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=json_body,
            timeout=30
        )
        
        # Try to parse response as JSON
        try:
            response_body = response.json()
        except json.JSONDecodeError:
            response_body = response.text
        
        return json.dumps({
            "status_code": response.status_code,
            "body": response_body
        })
        
    except requests.exceptions.ConnectionError:
        return json.dumps({"status_code": 0, "body": {"error": "Connection refused - is the backend running?"}})
    except requests.exceptions.Timeout:
        return json.dumps({"status_code": 0, "body": {"error": "Request timed out"}})
    except Exception as e:
        return json.dumps({"status_code": 0, "body": {"error": str(e)}})