#!/usr/bin/env python

# Be sure elastix/bin and elastix/lib are in the right paths
# and python can see them

# TODO: set up passing a parameter_file folder and image folder
# TODO: set up constant passing
# TODO: implement CONTINUE_FROM_PREVIOUS_REG

import os
import glob
import time
import subprocess
import platform
import shutil

# Script settings
NO_TERMINAL_OUTPUT = True
USE_IMAGE_MASK = True
CONTINUE_FROM_PREVIOUS_REG = False

def determine_max_proc():
    """Determine reasonable number of cores to use"""
    # Macbook
    if platform.system() == "Darwin":
        nproc = subprocess.Popen("sysctl -n hw.ncpu",shell=True,stdout=subprocess.PIPE)

    # Linux
    if platform.system() == "Linux":
        nproc = subprocess.Popen("nproc", stdout=subprocess.PIPE)

    max_processes = int(nproc.stdout.readline()[0:-1])
    max_processes = round(max_processes/2)-1
    return max_processes

def get_remaining_images(reg_output_dir,moving_image_dir):
    """ Return file names of images to register """
#    reg_imgs = glob.glob(os.path.join(reg_output_dir, "*.tif*"))
#    n_reg_imgs = len(reg_imgs)
#    mov_imgs = glob.glob(os.path.join(moving_image_dir, "*.tif"))
#    n_mov_imgs = len(mov_imgs)
#
#    return n_reg_imgs+1

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
        # TODO: implement
        sorted_moving_image_paths = sorted_moving_image_paths

    if USE_IMAGE_MASK:
        mask_images = os.path.join(cwd,"mask_image")
        mask_image_path = glob.glob(os.path.join(mask_image_dir, "*.tif*"))[0]

    # Make final output directory and dir for temporary registration output
    for d in [reg_output_dir, elastix_output_dir]:
        os.makedirs(d)

    # TODO: specify parameter file folder location
    # Apply series of registrations
    code_loc = os.path.dirname(__file__)
    # registration 1 translation
    param_1_file_path = os.path.join(code_loc,"parameter_files","20160615","1_trans.txt")
    # registration 2 rigid
    param_2_file_path = os.path.join(code_loc,"parameter_files","20160615","2_rigid.txt")
    # registration 3 affine
    param_3_file_path = os.path.join(code_loc,"parameter_files","20160615","3_affine.txt")

#    if CONTINUE_FROM_PREVIOUS_REG:
#        start_img_num = get_next_mov_image(reg_output_dir,moving_image_dir)

    # Register from first image
    start_img_num = 0
    n_registered = 0
    total_images = len(sorted_moving_image_paths)

    # Only spawn this many processes
    max_processes = determine_max_proc()

    reg_clock_start = time.clock()

    img_idx = 0;
    while n_registered < total_images:

        if len(outstanding_processes) < max_processes:
            # Current image to use in process
            moving_image_path = sorted_moving_image_paths[img_idx]
            moving_img_name = os.path.split(moving_image_path)[-1]

            # Output dir is process specific, move to registration output later
            curr_output_dir = os.path.join(elastix_output_dir,"reg_image_"+str(img_idx+1))
            if os.path.isdir(curr_output_dir)
                shutil.rmtree(curr_output_dir)
            os.makedirs(curr_output_dir)

            elastix_cmd = ("elastix"
                            + " -f " + fixed_image_path
                            + " -m " + moving_image_path
                            + " -out " + curr_output_dir
                            + " -p " + param_2_file_path)
            # TODO: add loop for appending subsequent parameter files

            if USE_IMAGE_MASK:
                # Use the same mask for fixed and moving images
                elastix_cmd.append(" -fMask " + mask_image_path
                                   " -mMask " + mask_image_path)
            if NO_TERMINAL_OUTPUT:
                # Send output to /dev/null
                elastix_cmd.append(" > /dev/null 2>&1")

            # Send command
            print "elastix_cmd: %s" % (elastix_cmd)

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
            for p in iter(outstanding_processes.keys())
                p.poll()
                if p.returncode != None:
                    todelete.append(p)

            for p in iter(todelete):
                del outstanding_processes[p]

        # Wait for all processes to complete
        for p in iter(outstanding_processes.keys())
            p.wait()

        # move all of the resulting images to one directory
        elastix_out_folders = glob.glob(os.path.join(elastix_output_dir,"reg_image_*"))
        for filepath in iter(elastix_out_folders)
            origin_full_path = glob.glob(os.path.join(filepath),"*.tif*")
            reg_img_name = os.path.split(origin_full_path)[-1]
            destin_full_path = os.path.join(reg_output_dir,reg_img_name)

            print destin_full_path
            shutil.move(origin_full_path,destin_full_path)
    reg_clock_end = time.clock()
    print "Total elapsed time: " + str(reg_clock_end - reg_clock_start)

# Run
main()

"""
        From previous

        for idx, moving_image_path in enumerate(moving_image_paths[start_img-1:]):
        img_name = os.path.split(moving_image_path)[-1]
        print "Registering " + img_name

        txt_cmd = ("elastix"
                    + " -f "  + fixed_image_path
                    + " -m " + moving_image_path
                    + " -out " + elastix_output_dir
                    + " -p " + param_2_file_path
                    + " -threads " + str(n_threads))
                    #+ " -p " + param_1_file_path
                    #+ " -p " + param_3_file_path
        #print txt_cmd
        subprocess.call(txt_cmd, shell=True)
        #print subprocess.Popen("echo $PATH", shell=True, stdout=subprocess.PIPE).stdout.read()

        # Rename file from output
        output_filepath = glob.glob(os.path.join(elastix_output_dir, "result.*.tif*"))[0]
        shutil.move(output_filepath, os.path.join(reg_output_dir,'reg_'+img_name))

        print "Elapsed time " + str(time.clock())
"""
