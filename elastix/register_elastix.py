#!/usr/bin/env python

# Be sure elastix/bin and elastix/lib are in the right paths
# and python can see them

# TODO: use a parameter_file folder for iterative transformations
# TODO: better scheduling for processor time

import os
import glob
import time
import subprocess
import platform
import shutil

# Script settings
NO_TERMINAL_OUTPUT = True # send output to /dev/null
USE_IMAGE_MASK = True # adds the -fMask and -mMask flags to elastix command
CONTINUE_FROM_PREVIOUS_REG = True # start up again after an interruption

def determine_max_proc():
    """Determine reasonable number of cores to use"""
    # Macbook
    if platform.system() == "Darwin":
        nproc = subprocess.Popen("sysctl -n hw.ncpu",shell=True,stdout=subprocess.PIPE)

    # Linux
    if platform.system() == "Linux":
        nproc = subprocess.Popen("nproc", stdout=subprocess.PIPE)

    max_processes = int(nproc.stdout.readline()[0:-1])
    max_processes = round(max_processes*.95)-1
    return max_processes

def get_remaining_images(elastix_output_dir):
    """ Return file names of images to register """
    reg_imgs = glob.glob(os.path.join(elastix_output_dir, "reg_image_*"))
    n_reg_imgs = len(reg_imgs)
    #mov_imgs = glob.glob(os.path.join(moving_image_dir, "*.tif"))
    #n_mov_imgs = len(mov_imgs)
    return n_reg_imgs

def main():
    # For now just run from the directory with images
    cwd = os.getcwd()

    # Fixed file locations
    fixed_image_dir = os.path.join(cwd,"fixed_image")
    moving_image_dir = os.path.join(cwd,"raw_images")
    reg_output_dir = os.path.join(cwd,"elastix_reg")
    elastix_output_dir = os.path.join(cwd,"elastix_out")

    # Use the image in this directory as fixed_image
    fixed_image_path = glob.glob(os.path.join(fixed_image_dir, "*.tif*"))[0]

    # Sort images
    moving_image_paths = glob.glob(os.path.join(moving_image_dir, "*.tif*"))
    sorted_moving_image_paths = sorted(moving_image_paths)

    if CONTINUE_FROM_PREVIOUS_REG:
        start_img_idx = get_remaining_images(elastix_output_dir) - 1
    else:
        start_img_idx = 0;

    if USE_IMAGE_MASK:
        mask_image_dir = os.path.join(cwd,"mask_image")
        mask_image_path = glob.glob(os.path.join(mask_image_dir, "*.tif*"))[0]

    # Make final output directory and dir for temporary registration output
    for d in [reg_output_dir, elastix_output_dir]:
        try:
            os.makedirs(d)
        except OSError:
            if not os.path.isdir(d):
                raise

    # TODO: specify parameter file folder location
    # Apply series of registrations
    code_loc = os.path.dirname(__file__)
    # rigid registration
    param_file_path = os.path.join(code_loc,"parameter_files","rigid","rigid_fast.txt")

    # Determine which images to register
    n_images = len(sorted_moving_image_paths)
    if (start_img_idx+1) == n_images:
        # No need to register
        n_registered = n_images
        print "Registration already complete"
    else:
        # Register from first image not already done
        n_registered = start_img_idx + 1;
    # start indexing after last registered
    img_idx = n_registered;

    # Only spawn this many processes
    max_processes = determine_max_proc()

    # Dictionary to keep track of processes
    outstanding_processes = {}

    # Time it
    reg_clock_start = time.clock()

    while n_registered < n_images:

        if (len(outstanding_processes) < max_processes):

            # Current image to use in process
            print len(sorted_moving_image_paths)
            print img_idx
            moving_image_path = sorted_moving_image_paths[img_idx]
            moving_img_name = os.path.split(moving_image_path)[-1]

            # Output dir is process specific, move to registration output later
            curr_output_dir = "reg_image_{:08d}".format(img_idx+1)
            curr_output_path = os.path.join(elastix_output_dir,curr_output_dir)
            if os.path.isdir(curr_output_path):
                shutil.rmtree(curr_output_path)
            os.makedirs(curr_output_path)

            elastix_cmd = ("elastix"
                            + " -f " + fixed_image_path
                            + " -m " + moving_image_path
                            + " -out " + curr_output_path
                            + " -p " + param_file_path)
            # TODO: add loop for appending subsequent parameter files from parameter
            # file containing folder

            if USE_IMAGE_MASK:
                # Use the same mask for fixed and moving images
                elastix_cmd += " -fMask " + mask_image_path + \
                               " -mMask " + mask_image_path
            if NO_TERMINAL_OUTPUT:
                # Send output to /dev/null
                elastix_cmd += " > /dev/null 2>&1"

            # Send command
            print "elastix_cmd: {}".format(elastix_cmd)

            p = subprocess.Popen(elastix_cmd,
                                    shell=True,
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    stdin=subprocess.PIPE )
            outstanding_processes[p] = elastix_cmd

            img_idx = img_idx + 1
        else:
            # wait for remaining processes to finish
            p = outstanding_processes.keys()[0]
            p.wait()
            del outstanding_processes[p]

            # remove processes which are finished
            to_delete = []
            for p in iter(outstanding_processes.keys()):
                p.poll()
                if p.returncode != None:
                    to_delete.append(p)

            for p in iter(to_delete):
                del outstanding_processes[p]

    # Wait for all processes to complete
    for p in iter(outstanding_processes.keys()):
        p.wait()

    # move all of the resulting images to one directory
    elastix_out_folders = glob.glob(os.path.join(elastix_output_dir,"reg_image_*"))

    # Multiple processors not needed here
    for filepath in iter(elastix_out_folders):
        origin_full_path = glob.glob(os.path.join(filepath,"*.tif*"))
        if len(origin_full_path) == 0:
            # Account for some errors in shell scripting :/
            print "SKIPPED: " + filepath 
        else:
            # Use the folder name to be the new registerd image name
            reg_img_name = os.path.split(os.path.dirname(origin_full_path[-1]))[-1] + ".tiff"
            destin_full_path = os.path.join(reg_output_dir,reg_img_name)
            print origin_full_path[-1]
            print destin_full_path
            shutil.move(origin_full_path[-1],destin_full_path)

    reg_clock_end = time.clock()
    print "Total elapsed time: " + str(reg_clock_end - reg_clock_start)

# Run
main()
