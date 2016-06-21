# quick and dirty fix to the tiled images out of elastix
from skimage import external
from skimage import data # for some reason also reqired
import os

cwd = os.getcwd()
filepaths = sorted(os.listdir(cwd))
for filename in iter(filepaths):
    print "Removing tiles from: " + filename
    tiff = external.tifffile.imread(os.path.join(cwd,filename))
    tiff = external.tifffile.imsave(os.path.join(cwd,filename),tiff)

