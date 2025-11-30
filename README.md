# LiveConfig
**The missing "Configuration Manager" for Autodesk Fusion.**

<img src="LiveConfigAppIcon.png" width="300">

## Introduction: The "Why" and "What"

We’ve all been there: you are tweaking a design for a 3D print. You open `Modify > Change Parameters`. You change a value. You hit Enter. The box closes. You rotate the model to check the fit. It’s wrong. You open the box again. You change the value. You hit Enter...

Fusion’s native parameter dialog is functional, but it’s **modal** (it blocks your view) and it doesn't let you save "states."

**LiveConfig** is a persistent, modeless dashboard designed to solve this. It sits quietly on the side of your screen, allowing you to drive your model's geometry in real-time while you orbit, zoom, and inspect your work.

* **Modeless Control:** Tweak user parameters using live input fields without locking up the viewport.

* **"Poor Man's" Configurations:** Save specific combinations of parameters and feature states (Suppressed/Unsuppressed) as named **Snapshots**. Switch between "Box_Small" and "Box_Large" with a single click.

* **Data Locality:** Your snapshots are stored as attributes *inside* the Fusion design file. If you share the file, the configurations travel with it.

## Installation

### Using Compiled Installers

#### Windows Users

1. **Download:** Download the latest installer (LiveConfig_Win.exe or .msi).

2. Install: Double-click the installer to run it.
   * Note: If Windows protects your PC saying "Unknown Publisher," click More Info → Run Anyway. (I'm an indie developer, not a giant corporation!)

3. Restart: If Fusion is open, restart it to load the new add-in.

#### Mac Users

1. **Download:** Download the latest package (LiveConfig_Mac.pkg).

2. Install: Double-click the package to run the installer.

   * Note: If macOS prevents the install, Right-Click the file and choose Open, then click Open again in the dialog box.

3. Restart: If Fusion is open, restart it to load the new add-in.

### Manual Installation

1. **Download:** Download the `LiveConfig` folder.

2. **Locate Add-Ins Folder:**

   * **Windows:** `%AppData%\Autodesk\Autodesk Fusion 360\API\AddIns\`

   * **Mac:** `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/`

3. **Install:** Copy the entire `LiveConfig` folder into that directory.

4. **Activate:**

   * Open Autodesk Fusion.

   * Press `Shift+S` to open **Scripts and Add-Ins**.

   * Click the **Add-Ins** tab.

   * Select **LiveConfig** and check **Run on Startup**.

   * Click **Run**.

## Using LiveConfig

### The Interface

Once running, you will find the **Live Configurator** button in the **Solid > Modify** panel (right next to *Change Parameters*). Click it to open the persistent sidecar palette.

![LiveConfig Screenshot](https://github.com/edjohnson100/LiveConfig/blob/146a1dff3c3b77ff34225dd1aa367d84c2cb2bb9/resources/LiveConfigDashboard_blank.png)

### 1. Live Parameters

The add-in automatically scans your design for **User Parameters**.

* **Real-Time Updates:** Type a new value into any box, and the model updates instantly. No "OK" or "Apply" buttons needed.

* **Favorites Only:** Use the **★ Favs** toggle in the header to filter the list to only your "Favorited" parameters, keeping the interface clean for complex models.

* **Dirty State:** If you modify a parameter manually, the interface will visually indicate that you are in an "unsaved" state (the active snapshot highlights turn off).

### 2. Tracked Features (The `CFG_` Magic)

Want to toggle features on and off like the Pro version of Fusion?

1. **Rename your Feature:** In the Fusion timeline, find any feature (Extrude, Fillet, Chamfer) you want to control.

2. **Add Prefix:** Rename it to start with `CFG_` (e.g., `CFG_Holes`, `CFG_Flange`).

3. **Rescan:** Click the **Rescan** (↻) button in the palette.

4. **Toggle:** You will now see a toggle switch for that feature. Flip it to instantly Suppress or Unsuppress that geometry.

### 3. Snapshots (Configurations)

This is the killer feature. Once you have your parameters and toggles set exactly how you like them:

1. **Save:** Type a name (e.g., "Printer_A_Settings") in the **New Config Name** box and click **Save State**.

2. **Activate:** A new button appears in the list. Click it anytime to restore that exact state.

3. **Manage:**

   * 💾 **Update:** Overwrite an existing snapshot with the current screen state.

   * 🗑️ **Delete:** Remove a snapshot permanently.

![Light mode example](https://github.com/edjohnson100/LiveConfig/blob/146a1dff3c3b77ff34225dd1aa367d84c2cb2bb9/resources/LiveConfigDashboard_example_light_mode.png)

![Dark mode example](https://github.com/edjohnson100/LiveConfig/blob/146a1dff3c3b77ff34225dd1aa367d84c2cb2bb9/resources/LiveConfigDashboard_example_dark_mode.png)

## Tech Stack

For the fellow coders and makers out there, here is how LiveConfig was built:

* **Language:** Python (Fusion API)

* **Interface:** HTML/CSS/JavaScript (running in a Fusion Palette)

* **Data Storage:** Custom JSON payloads stored in `Design.attributes` on the Root Component.

* **State Management:** A custom "Dirty State" tracking system that compares live model data against saved JSON snapshots to ensure the UI always reflects the truth.

## Acknowledgements & Credits

* **Developer:** Ed Johnson ([Making With An EdJ](https://www.youtube.com/@makingwithanedj))

* **AI Assistance:** Co-authored with Google's Gemini 3 Pro model.

* **Lucy (The Cavachon Puppy):**
  ***Chief Wellness Officer & Director of Mandatory Breaks***

  * Still preventing Repetitive Strain Injury one fetch session at a time.

* **License:** Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License.

***

*Happy Making!*
*— EdJ*
