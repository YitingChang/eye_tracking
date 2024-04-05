""" visualTask1_yiting.py
    YT 05 April 2024
    Modify Justin's visual task1 to record pupil size data

    JK 20 Feb 2024
    Loads a block of trials from an input csv file.  Displays images and records
    gaze data during fixation and image presentation.  The task is controlled
    by keyboard commands.  A reward is delivered at the end of each trial if 
    fixation is maintained for the required duration.

    Keyboard commands:
    'r'  load and run the trial block file
    'c'  calibrate the tracker
        'c'  calibrate the tracker
             'Enter' start calibration
        'Enter' accept the calibration
        'o' exit the calibration
    'p' pause the task
        'q' quit the task
    'g' toggle gaze display
    'ESC' skip the current trial
    'Ctrl-c' terminate the task

  bench3 19 Mar 2024
"""

import csv
import random
import math
import pygame
import pylink
import sys
import os
import time
import serial
from pygame.locals import *
import CalibrationGraphicsPygame
from CalibrationGraphicsPygame import CalibrationGraphics


def run_trial(trial_pars):
    """Run a single trial of the visual task and record gaze data."""
    show_gaze = False  # True  #
    should_pause = False
    # present each image for 2.0 seconds
    stim_dur = 2000
    # fixation acceptance window parameters
    radius = 200
    maxNumOutside = 500

    # unpacking the trial parameters
    trial_index, pic1, pic2 = trial_pars
    print(f"Running trial {trial_index} with images {pic1} and {pic2}")

    # load the images to display, here we stretch the image to fill full screen
    try:
        img1 = pygame.image.load("./images/" + pic1)
    except:
        print(f"Error loading image {pic1}")
        return pylink.TRIAL_ERROR
    img1 = pygame.transform.scale(img1, (scn_width, scn_height))

    try:
        img2 = pygame.image.load("./images/" + pic2)
    except:
        print(f"Error loading image {pic2}")
        return pylink.TRIAL_ERROR
    img2 = pygame.transform.scale(img2, (scn_width, scn_height))

    active_img = img1

    # get the currently active window
    surf = pygame.display.get_surface()

    # get a reference to the currently active EyeLink connection
    el_tracker = pylink.getEYELINK()

    # put the tracker in the offline mode first
    el_tracker.setOfflineMode()

    # clear the host screen before we draw the backdrop
    el_tracker.sendCommand("clear_screen 0")

    # create a begin trial marker in the datafile
    dataFile.write(f"{trial_index}, nan, nan, nan\n")

    # Start recording
    # arguments: sample_to_file, events_to_file, sample_over_link,
    # event_over_link (1-yes, 0-no)
    try:
        el_tracker.startRecording(0, 0, 1, 1)
    except RuntimeError as error:
        print("ERROR:", error)
        abort_trial()
        return pylink.TRIAL_ERROR

    # Allocate some time for the tracker to cache some samples
    pylink.pumpDelay(10)

    # show the image
    surf.fill((128, 128, 128))  # clear the screen
    surf.blit(active_img, (0, 0))
    pygame.display.flip()
    onset_time = pygame.time.get_ticks()  # image onset time

    pygame.event.clear()  # clear all cached events if there were any
    get_keypress = False

    fix_x, fix_y = scn_width / 2, scn_height / 2
    gaze_x, gaze_y = scn_width / 2, scn_height / 2
    numOutside = 0
    oldTimestamp = None

    while not get_keypress:
        # get fresh data
        newSample = el_tracker.getNewestSample()

        if newSample is not None:
            timestamp = newSample.getTime()
            if timestamp != oldTimestamp:
                oldTimestamp = timestamp
                # get gaze data
                gaze_x, gaze_y = newSample.getLeftEye().getGaze()
                # get pupil size data
                pupil_size = newSample.getLeftEye().getPupilSize()

                # write gaze and pupil size to data file
                dataFile.write(f"{timestamp}, {gaze_x}, {gaze_y}, {pupil_size}\n")

        # is the gaze inside the fixation zone
        x = fix_x - gaze_x
        y = fix_y - gaze_y
        d = math.sqrt(x**2 + y**2)
        if d > radius:
            color = (200, 0, 0)
            numOutside += 1
        else:
            color = (0, 200, 0)

        # redraw the image to erase previous gaze marker
        surf.blit(active_img, (0, 0))

        # screen marker parameters, img1: bottom left, img2: bottom right
        length = 32
        if active_img == img1:
            pygame.draw.rect(surf, (255, 255, 255), (0, scn_height - length, length, length))
        else:
            pygame.draw.rect(surf, (255, 255, 255), (scn_width - length, scn_height - length, length, length))

        # fixation point parameters
        length = 8
        pygame.draw.rect(surf, (255, 255, 255), (scn_width / 2 - length, scn_height / 2 - length, length, length))

        if show_gaze:
            # draw the acceptance window
            pygame.draw.circle(surf, (200, 0, 0), (fix_x, fix_y), radius, 1)
            # draw new gaze marker
            pygame.draw.circle(surf, color, (gaze_x, gaze_y), 5)

        pygame.display.flip()

        if numOutside > maxNumOutside:
            # el_tracker.sendMessage('gaze_outside_fixation_window')
            errorSnd.play()
            break

        dt = pygame.time.get_ticks() - onset_time

        if dt >= stim_dur and dt < stim_dur * 2:
            # switch to the other image
            if active_img == img1:
                active_img = img2

        elif dt >= stim_dur * 2:
            # el_tracker.sendMessage('time_out')
            successSnd.play()
            # reward by writing pulse width in millis to serial port.
            # '\n' is mandatory
            reward(b"200\n")
            break

        # abort the current trial if the tracker is no longer recording
        error = el_tracker.isRecording()
        if error is not pylink.TRIAL_OK:
            # el_tracker.sendMessage('tracker_disconnected')
            abort_trial()
            return error

        # check for keyboard events
        for ev in pygame.event.get():
            # Stop stimulus presentation when the spacebar is pressed
            if (ev.type == KEYDOWN) and (ev.key == K_SPACE):
                # send over a message to log the key press
                # el_tracker.sendMessage('key_pressed')
                get_keypress = True

            # Abort a trial if "ESCAPE" is pressed
            if (ev.type == KEYDOWN) and (ev.key == K_ESCAPE):
                # el_tracker.sendMessage('trial_skipped_by_user')
                # abort trial
                abort_trial()
                return pylink.SKIP_TRIAL

            # Terminate the task if Ctrl-c
            if (ev.type == KEYDOWN) and (ev.key == K_c):
                if ev.mod in [KMOD_LCTRL, KMOD_RCTRL, 4160, 4224]:
                    # el_tracker.sendMessage('terminated_by_user')
                    terminate_task()
                    return pylink.ABORT_EXPT

            # Toggle showGaze
            if (ev.type == KEYDOWN) and (ev.key == K_g):
                show_gaze = not show_gaze

    # clear the screen
    surf.fill((128, 128, 128))
    pygame.display.flip()

    # stop recording; add 10 msec to catch final events before stopping
    pylink.pumpDelay(10)
    el_tracker.stopRecording()


def terminate_task():
    """Terminate the task gracefully and close the connection to the tracker."""
    # disconnect from the tracker if there is an active connection
    el_tracker = pylink.getEYELINK()

    if el_tracker.isConnected():
        # Terminate the current trial first if the task terminated prematurely
        error = el_tracker.isRecording()
        if error == pylink.TRIAL_OK:
            abort_trial()

        # Put tracker in Offline mode
        el_tracker.setOfflineMode()

        # Clear the Host PC screen and wait for 500 ms
        el_tracker.sendCommand("clear_screen 0")
        pylink.msecDelay(500)

        # Close the link to the tracker.
        el_tracker.close()

    try:
        dataFile.close()
    except:
        pass

    try:
        ser.close()
    except:
        pass

    # quit pygame and python
    pygame.quit()
    sys.exit()


def abort_trial():
    """Ends recording and clears the display."""
    # get the currently active tracker object (connection)
    el_tracker = pylink.getEYELINK()

    # Stop recording
    el_tracker.stopRecording()

    # clear the screen
    surf = pygame.display.get_surface()
    surf.fill((128, 128, 128))
    pygame.display.flip()

    return pylink.TRIAL_ERROR


def initEyelink():
    """Initialize the Eyelink connection and set up the graphics environment
    for calibration. Set sample rate and calibration type.
    """
    # initialize eyelink and pygame
    print(f"Initializing Eyelink")
    el_tracker = pylink.EyeLink(None)
    try:
        el_tracker = pylink.EyeLink("100.1.1.1")
    except RuntimeError as error:
        print("ERROR:", error)
        el_tracker = pylink.EyeLink(None)

    # open an EDF data file on the Host PC
    el_tracker.openDataFile("test.edf")

    # Optional tracking parameters
    # Sample rate, 250, 500, 1000, or 2000, check your tracker specification
    el_tracker.sendCommand("sample_rate 500")
    # Choose a calibration type, H3, HV3, HV5, HV13 (HV = horizontal/vertical),
    el_tracker.sendCommand("calibration_type = HV5")
    pygame.mouse.set_visible(False)
    # win = pygame.display.set_mode((800, 600), 0) # FULLSCREEN | DOUBLEBUF)
    win = pygame.display.set_mode((0, 0), FULLSCREEN | DOUBLEBUF)
    scn_width, scn_height = win.get_size()

    # Pass the display pixel coordinates (left, top, right, bottom) to the
    # tracker see the EyeLink Installation Guide, "Customizing Screen Settings"
    el_coords = "screen_pixel_coords = 0 0 %d %d" % (scn_width - 1, scn_height - 1)
    el_tracker.sendCommand(el_coords)

    # Configure a graphics environment (genv) for tracker calibration
    genv = CalibrationGraphics(el_tracker, win)

    # Set background and foreground colors
    # parameters: foreground_color, background_color
    foreground_color = (0, 0, 0)
    background_color = (128, 128, 128)
    genv.setCalibrationColors(foreground_color, background_color)

    # Set up the calibration target
    # Use a picture as the calibration target
    genv.setTargetType("picture")
    genv.setPictureTarget(os.path.join("images", "sm.jpg"))
    genv.setup_cal_display()
    genv.setCalibrationSounds("", "", "")

    # Request Pylink to use the Pygame window we opened above for calibration
    pylink.openGraphicsEx(genv)

    return el_tracker


def read_csv_file(file_path):
    """Read a csv file and return the data as a list of lists.
    File format: trial_id, pic1, pic2
    """
    data = []
    with open(file_path, "r") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            data.append(row)
    return data


def wait_for_ITI(sec_to_wait):
    """Wait for the inter-trial interval (ITI) to expire and handle pause
    event.
    """
    start_time = pygame.time.get_ticks()
    is_paused = False
    while pygame.time.get_ticks() - start_time < sec_to_wait * 1000:
        # check for keyboard events
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                # pause the task
                if event.key == pygame.K_p:
                    is_paused = True
                    print("pausing")
                    while is_paused:
                        for ev in pygame.event.get():
                            if (ev.type == KEYDOWN) and (ev.key == K_p):
                                print("unpausing")
                                is_paused = False
                                break
                            # Terminate the task if q is pressed
                            if (ev.type == KEYDOWN) and (ev.key == pygame.K_q):
                                is_paused = False
                                terminate_task()
                                return 0
                        pygame.time.wait(10)
                return 1
    return 1


def reward(pulse_width_ms=200):
    """Trigger a pulse for the reward system"""
    if ser is not None:
        # ser.write(f'{pulse_width_ms}\n'.encode())
        ser.write(b"200\n")
    pass


def fix_on():
    """Show the fixation point and wait for the gaze to be within the
    acceptance window for the required duration, fix_dur.
    """
    display_dur = 3000  # max duration to display fixation target
    fix_dur = 1000  # fixation duration to initiate the trial
    maxNumOutside = 100
    fix_x, fix_y = scn_width / 2, scn_height / 2
    gaze_x, gaze_y = scn_width / 2, scn_height / 2
    radius = 200
    numOutside = 0
    show_gaze = False  # True  #
    oldTimestamp = None
    dt = 0
    zone_time = 0
    #  return True

    el_tracker = pylink.getEYELINK()
    # Start recording
    # arguments: sample_to_file, events_to_file, sample_over_link,
    # event_over_link (1-yes, 0-no)
    try:
        el_tracker.startRecording(0, 0, 1, 1)
    except RuntimeError as error:
        print("ERROR:", error)
        abort_trial()
        return pylink.TRIAL_ERROR

    # clear the screen
    surf = pygame.display.get_surface()
    surf.fill((128, 128, 128))
    # fixation point parameters
    length = 8
    pygame.draw.rect(surf, (255, 240, 255), (scn_width / 2 - length, scn_height / 2 - length, length, length))

    pygame.display.flip()
    start_time = pygame.time.get_ticks()

    while dt < display_dur:
        dt = pygame.time.get_ticks() - start_time
        # get fresh data
        newSample = el_tracker.getNewestSample()

        if newSample is not None:
            timestamp = newSample.getTime()
            if timestamp != oldTimestamp:
                oldTimestamp = timestamp
                gaze_x, gaze_y = newSample.getLeftEye().getGaze()

        # is the gaze inside the fixation zone
        x = fix_x - gaze_x
        y = fix_y - gaze_y
        d = math.sqrt(x**2 + y**2)
        # outside the zone
        if d > radius:
            color = (200, 0, 0)
            numOutside += 1
        # inside the zone
        else:
            color = (0, 200, 0)
            if zone_time == 0:
                zone_time = dt
            # inside the zone for the required duration
            if dt - zone_time > fix_dur:
                # surf.fill((128, 128, 150))
                # pygame.display.flip()
                # Stop recording
                el_tracker.stopRecording()
                print("fixation succeded")
                return True

        if show_gaze:
            surf.fill((128, 128, 128))
            # redraw fix point
            pygame.draw.rect(surf, (255, 240, 255), (scn_width / 2 - length, scn_height / 2 - length, length, length))
            # draw the acceptance window
            pygame.draw.circle(surf, (200, 0, 0), (fix_x, fix_y), radius, 1)
            # draw new gaze marker
            pygame.draw.circle(surf, color, (gaze_x, gaze_y), 5)

        # surf.fill((128, 128, 150))
        pygame.display.flip()

    el_tracker.stopRecording()
    surf.fill((128, 128, 140))
    pygame.display.flip()

    return False


if __name__ == "__main__":

    pygame.init()
    errorSnd = pygame.mixer.Sound("error.wav")
    successSnd = pygame.mixer.Sound("qbeep.wav")
    el_tracker = None
    should_pause = False
    min_iti = 1  # minimum inter-trial interval
    max_iti = 3  # maximum inter-trial interval

    # initialize eyelink
    eyelink = initEyelink()
    scn_width, scn_height = pygame.display.get_window_size()
    print(f"Eyelink initialized: {scn_width}, {scn_height}")

    # serial port
    try:
        ser = serial.Serial("/dev/ttyACM0", 115200, timeout=0)
    except:
        print("Serial port not found")
        ser = None

    # the main trial loop
    while True:
        # check for keyboard events
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.KEYDOWN:

                # 'r'  load and run the trial block
                if event.key == pygame.K_r:
                    print("r pressed")
                    # open dataFile
                    dataFile = open(r"testData.txt", "w+")
                    # read the trial block
                    file_path = "trialBlock.csv"
                    csv_trial_block = read_csv_file(file_path)
                    n = len(csv_trial_block)
                    i = 1

                    # loop through the trial block.  Advance only if initial
                    # fixation is maintained
                    while i < n:
                        wait_for_ITI(random.randint(min_iti, max_iti))
                        # print(csv_trial_block[i])
                        if fix_on():
                            # print(i)
                            run_trial(csv_trial_block[i])
                            i = i + 1
                        else:
                            pass
                            # print("<{}>".format(i))
                    print("trial block completed")

                # 'c'  calibrate the tracker
                if event.key == pygame.K_c:
                    print("calibrate pressed")
                    try:
                        eyelink.doTrackerSetup()
                    except RuntimeError as err:
                        print("ERROR:", err)
                        eyelink.exitCalibration()

                # 'p' pause the task
                if event.key == pygame.K_p:
                    print("main pausing")
                    # toggle pause state
                    should_pause = not should_pause
                    while should_pause:
                        for ev in pygame.event.get():
                            if (ev.type == KEYDOWN) and (ev.key == K_p):
                                should_pause = False
                                print("unpausing")
                                break
                        time.sleep(0.1)  # sleep for 100 ms
                        print("waiting")
                        break

                # 'q' quit the task
                if event.key == pygame.K_q:
                    print("quitting")
                    terminate_task()
                    break
