# ![FilaTrack Logo](./static/images/filatrack_logo_32.png) FilaTrack - The Smart Filament Tracker

FilaTrack is a **Flask-based Python web app** for managing **3D printing filament usage and print jobs**.
It tracks **filament rolls**, logs **print jobs**, and integrates with **PrusaSlicer** to automatically import print data.

## Features

- **Filament Roll Management**: Add, edit, duplicate, and delete filament rolls.
- **Print Job Tracking**: Log print jobs, assign them to specific filament rolls, and track filament usage.
- **Unreviewed Print Jobs**: Temporary print job storage for review and approval.
- **PrusaSlicer | OrcaSlicer | AnycubicSlicer Integration**: Automatically import print job details from G-code.
- **Search and Filter**: Easily search and filter through filament rolls and print jobs.
- **Data Persistence**: Uses an SQLite database to store all information.
- **Bootstrap-based UI**: Responsive and user-friendly design.

## Prerequisites

Ensure you have the following installed on your system:

- Docker
- Docker Compose

## Installation

1. Clone the repository:

   ```shell
   git clone https://github.com/mrfenyx/filament-tracker.git
   cd filament-tracker
   ```

2. Run the application using Docker Compose:

   ```shell
   docker-compose up -d --build
   ```

3. The database will be stored in the `./data/` directory, which should be backed up regularly to prevent data loss.

## Running the Application

The application will run as a Docker container. Access it in your browser at [http://127.0.0.1:5000/](http://127.0.0.1:5000/).

## Slicer Integration

FilaTrack can automatically capture **filament usage and project names** from different slicers using a post-processing script.

### Supported / Tested Slicers
* **PrusaSlicer**
* **OrcaSlicer**
* **AnycubicSlicer** and **AnycubicSlicerNext**

### ✅ How It Works

1. When you **export the gcode** of a model in a supported  **Slicer**, it executes a **specific script** as a post-processing script.
2. This script extracts relevant metadata from the generated G-code file, such as:
   - **Filament weight (g)**
   - **Project name (from filename or slicer environment variables)**
   - **Slicing timestamp**
3. The extracted data is sent to Filament Tracker as an **unreviewed print job**, where you can assign a filament roll and finalize it.

### 🔧 Setting Up the Integration

#### **1️⃣ Execute the Setup Script**

1. Open the /integrations folder and execute `setup_integrations.ps1` (PowerShell script)
2. Follow the prompts in the script (pay attention!)
3. At the end of the setup, you will see a **command** printed on the screen that you need to add to the post-processing script in your slicer software.

#### **2️⃣ Add the Post-Processing Script in PrusaSlicer**

1. Open **PrusaSlicer**.
2. Go to **Printer Settings → Custom G-code → Post-processing scripts**.
3. Add the command printed at the end of the script execution.

#### **2️⃣ Add the Post-Processing Script in OrcaSlicer, AnycubicSlicer or AnycubicSlicerNext**

1. Open **Slicer**.
2. Go to **Process → Others Tab → Post-processing scripts**.
3. Add the command printed at the end of the script execution.

#### **3️⃣ How to Manually Run `prusa_post.py` (Testing)**

You can manually run the script to test how it processes a G-code file:

```bash
python prusa_post.py "C:\path\to\your_model.gcode"
```

If successful, you should see something like:

```plaintext
INFO:root:Processing G-code: arcwelder/test.gcode
INFO:root:Successfully sent data to Filament Tracker API
```

#### **4️⃣ Assigning the Unreviewed Print Jobs**

1. Open FilaTrack (`http://localhost:5000`).
2. Under **Unreviewed Print Jobs**, find the newly added entry.
3. Click **Approve**, select the correct filament roll, adjust values if needed, and save the print job.

## Usage

![FilaTrack UI](./static/images/UI.png)

### Adding a Filament Roll

- Click on the 1️⃣ **"Add Roll"** button.
- Enter details like Maker, Color, Total Weight, and Remaining Weight.
- Click **"Add Roll"** to save it.

### Logging a Print Job

- Click on the 2️⃣ **"Add Print Job"** button.
- Select a filament roll, enter the print job details, and click **"Add Print Job"**.
- The remaining filament weight will automatically be updated.

### Reviewing Temporary Print Jobs

- Temporary jobs appear in the **"Unreviewed Print Jobs"** section.
- Click 6️⃣ **✅ Approve** to finalize a job.
- Click 7️⃣ **🗑️ Delete** to remove it.

### Managing Filament Rolls and Print Jobs

Each entry has action buttons:

- 3️⃣ & 8️⃣ **📄 Duplicate**: Clone an existing filament roll or print job.
- 4️⃣ & 9️⃣ **✏️ Edit**: Modify the details.
- 5️⃣ & 🔟 **🗑️ Delete**: Remove an entry (deleting a filament roll will also delete associated print jobs).

## Database Management

The database is mounted to the local `./data/` directory as defined in `docker-compose.yml` (feel free to change this):

```yaml
    volumes:
      - ./data:/app/data
```
**⚠️NOTES⚠️**
1. Ensure that if you map this to an existing folder (e.g. NAS volume), you need to give **RW permission to EVERYONE** for that folder.
2. Ensure that this folder is backed up regularly to avoid data loss.

## License

This project is open-source and available under the MIT License.

---
Happy Printing! 🎨🎭
