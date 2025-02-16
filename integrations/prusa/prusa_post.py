import argparse
import logging
import sys
import os
import re
import requests
import subprocess
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Flask API Endpoint
# Set FILAMENT_TRACKER_API_URL env var with the address of your server if necessary
FILAMENT_TRACKER_API_URL = os.getenv("FILAMENT_TRACKER_API_URL", "http://127.0.0.1:5000/add_temp_job") 

# ArcWelder Path
# set env var ARCWELDER_PATH tothe full path to the ArcWelder.exe, otherwise ArcWelder executable should be in PATH
ARCWELDER_PATH = os.getenv("ARCWELDER_PATH", "ArcWelder")


logging.basicConfig(
    level=logging.DEBUG,  # Set logging level (INFO, DEBUG, WARNING, ERROR, CRITICAL)
)

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
    gcode_filename = None

    # Try to get filename from environment variable
    env_project_name = os.getenv("SLIC3R_PP_OUTPUT_NAME")
    if env_project_name:
        gcode_filename = Path(env_project_name).stem
        logging.info(f"Using filename from environment variable: {gcode_filename}")

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
                if line.startswith("; output_filename_format") or line.startswith("; filename_format"):
                    match = re.search(r"; (?:output_)?filename_format = (.+)", line)
                    if match:
                        filename_format = match.group(1)
                        logging.info(f"Using filename format: {filename_format}")
                        
        # Fallback to file name if env variable not set
        if not gcode_filename:
            gcode_filename = os.path.basename(file_path).replace(".gcode", "")
            logging.info(f"Using filename from file path: {gcode_filename}")

        # If a filename_format is provided, use dynamic parsing with regex.
        if filename_format:
            # Remove trailing .gcode if present in the format string.
            if filename_format.endswith(".gcode"):
                filename_format = filename_format[:-6]

            # Split the format string into tokens (literals and placeholders)
            tokens = re.split(r'(\{[^}]+\})', filename_format)
            regex_pattern = ""
            for token in tokens:
                logging.debug(f"Token: {token}")
                if token.startswith("{") and token.endswith("}"):
                    # Process placeholders.
                    if token == "{input_filename_base}":
                        # Use a greedy capture for the base so it can include internal separators.
                        regex_pattern += r"(?P<input_filename_base>.+)"
                    else:
                        # For other placeholders, assume they do not include '-' or '_'.
                        regex_pattern += r"[^-_]+"
                else:
                    # For literal parts, if the token is exactly '-' or '_', allow matching either.
                    if token in ["-", "_"]:
                        regex_pattern += "[-_]"
                    else:
                        regex_pattern += re.escape(token)
            # Force full string match and append .gcode extension.
            regex_pattern = "^" + regex_pattern + r"\.gcode$"
            logging.debug(f"Constructed regex pattern: {regex_pattern}")
            
            # Attempt to match the actual filename (append .gcode to match the regex).
            match = re.match(regex_pattern, gcode_filename + ".gcode")
            if match and "input_filename_base" in match.groupdict():
                extracted = match.group("input_filename_base")
                logging.info(f"Extracted project name: {extracted}")
                project_name = format_project_name(extracted)
                logging.info(f"Formatted project name: {project_name}")
                
        # Fallback to using the base filename if extraction fails.
        if not project_name:
            project_name = format_project_name(os.path.basename(file_path).replace(".gcode", ""))
    
    except Exception as e:
        logging.error(f"Error reading G-code file: {e}")

    # Only return info if filament weight was successfully extracted.
    if filament_weight is not None:
        return {
            "project_name": project_name,  # Aligned field name
            "weight_used": filament_weight,  # Aligned field name
            "date": datetime.now().strftime('%Y-%m-%dT%H:%M')
        }
    return None

def send_to_flask_api(data):
    """Sends extracted print job data to the Flask backend."""
    try:
        response = requests.post(FILAMENT_TRACKER_API_URL, json=data)
        if response.status_code == 200:
            logging.info("Successfully sent data to Filament Tracker API")
        else:
            logging.error(f"Failed to send data: {response.text}")
    except Exception as e:
        logging.error(f"Error sending data: {e}")

def forward_to_arcwelder(file_path):
    """Calls ArcWelder with the given G-code file."""
    try:
        subprocess.run([ARCWELDER_PATH, file_path], check=True)
        logging.info(f"Successfully forwarded G-code to ArcWelder: {file_path}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error calling ArcWelder: {e}")

def main():
    usage = """
    Basic usage:
    python3 prusa_post.py c:\\gcode\\my_file.gcode

    Use with ArcWelder to convert non-arcs to arcs in the output
    python3 prusa_post.py -a c:\\gcode\\my_file.gcode
    
    Use with ArcWelder to convert non-arcs to arcs in the output, with custom path to the executable
    ARCWELDER_PATH="C:\\tools\ArcWelder.exe" python3 prusa_post.py -a c:\\gcode\\my_file.gcode

    Linux: Use with ArcWelder to convert non-arcs to arcs in the output, with custom path to the executable
    ARCWELDER_PATH=arcwelder/bin/ArcWelder python3 prusa_post.py -a ../gcode/face_0.4n_0.2mm_PETG_MINI_1d5h24m.gcode
    """
    parser = argparse.ArgumentParser(
        epilog=usage,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "input",
        help='Input G-code file (if not provided, the script will try to detect it)',
        type=str,
        nargs="?"
    )
    parser.add_argument(
        "-a",
        "--arcwelder",
        help='Use ArcWelder for converting G-code short lines to arcs',
        action='store_true'
    )

    args = parser.parse_args()

    # If no argument is passed, fall back to sys.argv (for PrusaSlicer execution)
    gcode_path = args.input if args.input else (sys.argv[1] if len(sys.argv) > 1 else None)

    if not gcode_path:
        logging.error("Error: No G-code file provided.")
        print("Usage: python prusa_post.py <path_to_gcode>")
        sys.exit(1)

    print(f"Processing G-code: {gcode_path}")

    extracted_data = extract_gcode_info(gcode_path)
    if extracted_data:
        send_to_flask_api(extracted_data)

    # Forward the file to ArcWelder for further processing if needed
    if args.arcwelder:
        forward_to_arcwelder(gcode_path)

if __name__ == "__main__":
    main()
    # Uncomment for debugging
    # input("Press Enter to exit...")
