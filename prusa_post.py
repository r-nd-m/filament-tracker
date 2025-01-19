import sys
import os
import re
import requests
import subprocess
from pathlib import Path
from datetime import datetime

# Flask API Endpoint
API_URL = "http://192.168.2.25:4892/add_temp_job" # Add path to your API endpoint

# ArcWelder Path
ARCWELDER_PATH = r"C:\Users\mirce\OneDrive\Desktop\3D Models\ArcWelder.exe"

def format_project_name(raw_name):
    """Converts raw input filename base to a properly formatted project name."""
    if not raw_name:
        return "Unknown Project"
    
    formatted_name = raw_name.replace("-", " ").replace("_", " ")
    return formatted_name.title()  # Capitalize Each Word

def extract_gcode_info(file_path):
    """Extracts filament weight and project details from the G-code file."""
    filament_weight = None
    project_name = None
    filename_format = None

    env_project_name = os.getenv("SLIC3R_PP_OUTPUT_NAME")
    if env_project_name:
        gcode_filename = Path(env_project_name).stem

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()

                # Extract filament weight
                if line.startswith("; filament used [g] ="):
                    match = re.search(r"; filament used \[g\] = ([\d.]+)", line)
                    if match:
                        filament_weight = float(match.group(1))

                # Extract output filename format
                if line.startswith("; output_filename_format"):
                    match = re.search(r"; output_filename_format = (.+)", line)
                    if match:
                        filename_format = match.group(1)

        # Extract project name using filename format
        if not gcode_filename:
            gcode_filename = os.path.basename(file_path).replace(".gcode", "")

        model_parts = gcode_filename.split('-')

        if filename_format:
            format_parts = filename_format.split('-')

            # Find where {input_filename_base} starts
            if "{input_filename_base}" in format_parts:
                base_index = format_parts.index("{input_filename_base}")
                
                # Calculate how many elements to drop from the end
                total_parts = len(model_parts)
                extra_parts = len(format_parts) - (base_index + 1)

                # Extract only the project name
                project_name_parts = model_parts[base_index : total_parts - extra_parts]
                project_name = format_project_name("-".join(project_name_parts))

    except Exception as e:
        print(f"Error reading G-code file: {e}")

    # Ensure we have the project name
    if not project_name:
        project_name = format_project_name(os.path.basename(file_path).replace(".gcode", ""))

    if filament_weight:
        return {
            "project_name": project_name,  # Aligned field name
            "weight_used": filament_weight,  # Aligned field name
            "date": datetime.now().strftime('%Y-%m-%dT%H:%M')
        }
    return None

def send_to_flask_api(data):
    """Sends extracted print job data to the Flask backend."""
    try:
        response = requests.post(API_URL, json=data)
        if response.status_code == 200:
            print("Successfully sent data to Flask")
        else:
            print(f"Failed to send data: {response.text}")
    except Exception as e:
        print(f"Error sending data: {e}")

def forward_to_arcwelder(file_path):
    """Calls ArcWelder with the given G-code file."""
    try:
        subprocess.run([ARCWELDER_PATH, file_path], check=True)
        print(f"Successfully forwarded G-code to ArcWelder: {file_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error calling ArcWelder: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: prusa_post.py <path_to_gcode>")
        sys.exit(1)

    gcode_path = sys.argv[1]
    print(f"Processing G-code: {gcode_path}")

    extracted_data = extract_gcode_info(gcode_path)
    if extracted_data:
        send_to_flask_api(extracted_data)

    # Forward the file to ArcWelder
    forward_to_arcwelder(gcode_path)
