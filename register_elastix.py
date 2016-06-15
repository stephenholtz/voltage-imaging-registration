#!/usr/bin/env python

import os
import glob
import time
import subprocess

# Script settings
continue_from_previous_reg = True

nproc = subprocess.Popen("nproc", stdout=subprocess.PIPE)
n_threads = int(nproc.stdout.readline()[0:-1]) - 2

def get_next_mov_image():
    """ Return file name of the next moving image to register """
    
    reg_imgs = glob.glob(os.path.join(reg_output_dir, "*.tif*"))
    n_reg_imgs = len(reg_imgs)
    mov_imgs = glob.glob(os.path.join(moving_image_dir, "*.tif"))
    n_mov_imgs = len(mov_imgs)

    return n_reg_imgs+1

# Run from directory with data for now
cwd = os.getcwd()

# File locations
fixed_image_dir = os.path.join(cwd,"fixed_images")
moving_image_dir = os.path.join(cwd,"raw_images")
reg_output_dir = os.path.join(cwd,"elastix_reg")
elastix_output_dir = os.path.join(cwd,"elastix_out")

# Make output directory (disambiguates files & directories)
for d in [reg_output_dir, elastix_output_dir]:
  try: 
    os.makedirs(d)
  except OSError:
    if not os.path.isdir(d):
      raise

# Use the image in this directory as fixed_image
fixed_image_path = glob.glob(os.path.join(fixed_image_dir, "*.tif*"))[0]
moving_image_paths = glob.glob(os.path.join(moving_image_dir, "*.tif*"))

elastix = sitk.SimpleElastix()
elastix.SetFixedImage(fixed_image)

# Apply series of registrations
# registration 1 translation
param_1_file_path = os.path.join(cwd,"parameter_files","20160615","1_trans.txt")
# registration 2 rigid
param_2_file_path = os.path.join(cwd,"parameter_files","20160615","2_rigid.txt")
# registration 3 affine
param_3_file_path = os.path.join(cwd,"parameter_files","20160615","3_affine.txt")

if continue_from_previous_reg: 
    start_img = get_next_mov_image()
else:
    start_img = 0

print ""
print "Starting from image #" + str(start_img)
print ""

start = time.clock()

for idx, moving_image_path in enumerate(moving_image_paths[start_img-1:]):
    img_name = os.path.split(moving_image_path)[-1]
    print "Registering " + img_name
    subprocess.call(["elastix",
                     "-f "+fixed_image_path,
                     "-m "+moving_image_path,
                     "-out "+reg_output_dir,
                     "-p "+param_1_file_path,
                     "-p "+param_2_file_path,
                     "-p "+param_3_file_path,
                     "-threads "+str(n_threads)]
    print "Elapsed time " + str(time.clock())
    print ""

# Total elapsed time
end = time.clock()
print "Total elapsed time: " + str(end - start)
