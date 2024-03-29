import slicer
from slicerUtil.module import *
import os
import time

# white background withoud box and coordinates
set3Dview(viewNode=None, bkgrColor=(255,255,255), bkgrColor2=(255,255,255), boxVisible=0, labelsVisible=0) 

nodes = slicer.util.getNodes("epoch*").values()
segEdConfig = startSegmentationEditor()
for node in nodes:
    _ = naiveSegment(node, segName=node.GetName()+"_seg", segMapName="bone", lowerThreshold=0.02, smoothSigma=1, **segEdConfig)

color=(0.5,0.5,0.5)
segnodes = slicer.util.getNodes("*seg").values()
for node in segnodes:
    node.GetSegmentation().GetSegment("bone").SetColor(*color)
    hideSegmentIn3D(node)

fd = r"C:\Users\wangs\Documents\35_um_data_100x100x48 niis\predicted\3d-20211014T002147Z-001\3d"
for node in segnodes:
    showSegmentIn3D(node)
    time.sleep(0.5)
    capture3Dview(os.path.join(fd, node.GetName()+".png"))
    time.sleep(0.5)
    hideSegmentIn3D(node)

slicer.mrmlScene.Clear(0)