This Hand Tracking tool was built by Ariel Sol for Mirrored Glass's "Pulse of the City" Project. 
It uses Google's MediaPipe framework to capture hand data, stream it over OSC, and write to a CSV file. 

=== HOW TO RUN ===
> Open the terminal
> Type py main.py
> Hit ENTER

=== FUNCTIONS ===
> When the program starts, you will be prompted to select a webcam
> Once the camera has opened, CLICK THE VIDEO WINDOW to access the controls below:
> Press SPACE to toggle start/stop streaming data 
> Press S to print a snapshot of current hand data to terminal 
> Press ENTER to quit

When you stop streaming, a CSV is automatically timestamped and generated in the CSV_Exports folder. 

=== MAKING ADJUSTMENTS ===
> global_vars.py contains adjustable settings