import os, glob
from slicerUtil.module import *
from slicerUtil.sitkUtil import *
import slicer
import meshio

# switchToMicroCTScale()

# import data and get a list() of volumeNodes
inputDir = r"C:\Users\wangs\Documents\35_um_data_100x100x48 niis\Data"
outputDir = r"C:\Users\wangs\Documents\35_um_data_100x100x48 niis\meshes"

fileList = ["322LT_w3.nii.gz"]
for f in fileList:
    sitkimg = sitk.ReadImage(os.path.join(inputDir,f))
    sitkimg = sitkimg[2:98, 2:98, :]
    sitkimg.SetSpacing((30,30,30))
    sitkimg.SetDirection([1,0,0, 0,1,0, 0,0,1])
    sitkimg.SetOrigin((1440, 1440, 720))
    # sitkimg = down_scale(sitkimg, down_scale_factor=0.5)
    sitkimg = sitk.BinaryThreshold(sitkimg, lowerThreshold=30, upperThreshold=255)
    sitkimg = sitk.Cast(sitkimg, sitk.sitkUInt8)
    openfilter = sitk.BinaryMorphologicalClosingImageFilter()
    openfilter.SetKernelRadius(1)
    sitkimg = openfilter.Execute(sitkimg)
    sitkimg = sitk.BinaryGrindPeak(sitkimg, fullyConnected=True)
    # sitkimg.SetSpacing((0.03,0.03,0.03))
    vNode = PushVolumeToSlicer(sitkimg*2, name=f[:-7])
    # vNode.SetSpacing(0.03,0.03,0.03)
    # vNode.SetOrigin(0, 0, 0)
    # vNode.SetIJKToRASDirections([[1,0,0], [0,1,0], [0,0,1]])
    showVolume(vNode)

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
        segMapName=node.GetName(), 
        to_file=None, 
        lowerThreshold=1, 
        upperThreshold=255, 
        smoothSigma=3, 
        color=(0.5,0.5,0.5),
        keep_largest_island=True, 
        cleanUp=False,
        openningRad=1
    )
    segments = GetAllSegment(segNode) # get all the segments from a segmentationNode
    getModelFromSegmentation(segNode, "model"+node.GetName())
    modelNode = slicer.util.getNode(node.GetName())
    # modelNode = logic.generateMesh(
    #     segNode, None,
    #     modelName=node.GetName() + "_model",
    #     segments=segments,
    #     featureScale=3,
    #     samplingRate=0.7,
    #     additionalParameters="--B 1"
    # )
    logic.generateMeshTetGen(modelNode, modelName="Mesh"+modelNode.GetName(),
        ratio = 2,
        angle = 20,
        volume = 50,
        additionalParameters = "R")
    slicer.util.saveNode(modelNode, os.path.join(outputDir, "slicer"+modelNode.GetName()+"_3mm.vtk")
    ) 

for model in glob.glob(os.path.join(outputDir, "*.vtk")):
    mesh = meshio.read(model)
    mesh.write(model.replace("vtk", "inp"), file_format="abaqus")


    # ,
    #     additionalParameters="--sigma_blend 20"