import os, glob
from slicerUtil.module import *
import slicer

# import data and get a list() of volumeNodes
inputDir = r"C:\Users\wangs\Documents\35_um_data_100x100x48 niis\Data"
outputDir = r"C:\Users\wangs\Documents\35_um_data_100x100x48 niis\meshes"

fileList = ["236LT_w1.nii.gz", "236LT_w2.nii.gz"]
for f in fileList:
    vNode = loadVolume(os.path.join(inputDir, f))
nodes = slicer.util.getNodes("*_w*").values()

# format the 3D view
viewNode = slicer.app.layoutManager().threeDWidget(0).mrmlViewNode()
set3Dview(viewNode=viewNode, bkgrColor=(255,255,255), bkgrColor2=(255,255,255), boxVisible=0, labelsVisible=0)

# create a node segmentation editor and a widge to handle it.
nodeAndWidge = startSegmentationEditor() # a dict is returned
segEditorNode = nodeAndWidge["segmentEditorNode"]
segEditorWidge = nodeAndWidge["segmentEditorWidget"]

# create a instance of SegmentMesher3D
logic = SegmentMesher3D()

for node in nodes:
    segNode, _, _ = naiveSegment(
        node,
        segmentEditorNode=segEditorNode, 
        segmentEditorWidget=segEditorWidge, 
        segName=node.GetName() + "_seg", 
        segMapName="bone", 
        to_file=None, 
        lowerThreshold=30, 
        upperThreshold=255, 
        smoothSigma=4, 
        color=(0.5,0.5,0.5),
        keep_largest_island=True, 
        cleanUp=False
    )
    segments = GetAllSegment(segNode) # get all the segments from a segmentationNode
    modelNode = logic.generateMesh(
        node, segNode,
        modelName=node.GetName() + "_model",
        segments=segments,
    )
    slicer.util.saveNode(modelNode, os.path.join(outputDir, modelNode.GetName()+".vtk")) 