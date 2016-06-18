#!/usr/bin/env python

# not updated for multiple processors 
# still a reasonable starting point/example

import os
import glob
import time

import SimpleITK as sitk

# Script settings
continue_from_previous_reg = True

def get_next_mov_image():
    """ Return file number of next moving image to register """
    
    reg_imgs = glob.glob(os.path.join(reg_output_dir, "*.tif*"))
    n_reg_imgs = len(reg_imgs)
    mov_imgs = glob.glob(os.path.join(moving_image_dir, "*.tif"))
    n_mov_imgs = len(mov_imgs)

    # TODO: error check here

    return n_reg_imgs + 1

# Run from directory with data for now
# TODO: pass command line args
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
fixed_image = sitk.ReadImage(fixed_image_path)
moving_image_paths = glob.glob(os.path.join(moving_image_dir, "*.tif*"))

elastix = sitk.SimpleElastix()
elastix.SetFixedImage(fixed_image)

# Apply series of registrations
param_map = sitk.VectorOfParameterMap()

# first registration: rigid
param_map.append(sitk.GetDefaultParameterMap("rigid"))
param_map[0]["WriteResultImage"] = ["false"]
param_map[0]["DefaultPixelValue"] = "0"

# second registration: affine
param_map.append(sitk.GetDefaultParameterMap("affine"))
param_map[1]["Transform"] = ["AffineTransform"]
param_map[1]["WriteResultImage"] = ["true"]
param_map[1]["DefaultPixelValue"] = "0"

elastix.SetParameterMap(param_map)

if continue_from_previous_reg: 
    start_img = get_next_mov_image()
else:
    start_img = 1

print ""
print "Starting from image #" + str(start_img)
print ""

start = time.clock()

#for idx, moving_image_path in enumerate(moving_image_paths[start_img-1:]):
for moving_image_path in moving_image_paths[start_img-1:-1]:
    img_name = os.path.split(moving_image_path)[-1]
    print "Registering " + img_name

    moving_image = sitk.ReadImage(moving_image_path)
    elastix.SetMovingImage(moving_image)
    elastix.Execute()
    result_image = elastix.GetResultImage()
    sitk.WriteImage(result_image, os.path.join(reg_output_dir, "result_"+img_name))

    #transform_param_map = elastix.GetTransformParameterMap()

    print "Elapsed time " + str(time.clock())
    print ""

# Total elapsed time
end = time.clock()
print "Total elapsed time: " + str(end - start)
