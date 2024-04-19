# eye_tracking
We use EyeLink 1000 Plus to track eyes to obtain gaze and pupil diameter data during a haptic/visual task.\
Reference: https://www.sr-research.com/support-options/learning-resources/

## Installation
1. Update camera and screen setup (screen size, distance between camera and screen etc.)
2. Calibrate pupil size using the artificial eye
   
## Recording
1. Start the host and display computers.
2. In the host computer, (1) select EyeLink mode and (2) check the camera setup
3. In the display computer:
   - Open a terminal: 
    ```
    conda deactivate  % (if in some virtual environments)
    cd Code/visualTask1  
    python3 visualTask1_YC.py
    ```
    - Data is saved in a txt file.
5. To process data:
    - Open processData_YC.m in MATLAB
    - Plot gaze position and pupil diameter for each trial
7. For recording directly from the host computer:
    - Select Output/Record
    - Open File
    - Type a filename and press enter
    - Click the Record button
    - Click the Stop Recording button
    - Click the Close File button
    - Data is saved in an edf file.
    - To transfer the edf file to the display computer,
        + Click the Exit EyeLink button in the host computer
        + On the display computer, type 100.1.1.1 into the address bar of a browser to access the file manager software running on the host computer
        + Download the edf file
        + Open DataViwer to read the edf file on the display computer
      

