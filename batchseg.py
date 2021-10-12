import os
from naiveSegment import naiveSegment
from utils import *

masterdir = r"C:\Users\wangs\Documents\35_um_data_100x100x48 niis\Data"
outputdir = r"C:\temp"
imgls = ["236LT_w1.nii.gz", "236LT_w2.nii.gz", "236LT_w3.nii.gz", "236LT_w4.nii.gz"]

for img in imgls:
    file = os.path.join(masterdir, img)
    volumeNode = loadVolume(file)
    name = volumeNode.GetName()
    outputfile = os.path.join(outputdir, name+".nrrd")
    naiveSegment(volumeNode, segName=name, segMapName="bone", to_file=outputfile, lowerThreshold=30, upperThreshold=255, smoothSigma=6, keep_largest_island=True)