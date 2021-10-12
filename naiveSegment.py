import SimpleITK as sitk
import slicer

def naiveSegment(masterVolumeNode,segName="", segMapName="bone", to_file=None, lowerThreshold=20, upperThreshold=255, smoothSigma=6, keep_largest_island=False):
    # Create segmentation
    segmentationNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
    # segmentationNode.CreateDefaultDisplayNodes() # only needed for display
    segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(masterVolumeNode)
    segmentationNode.SetName(segName)
    addedSegmentID = segmentationNode.GetSegmentation().AddEmptySegment(segName)

    # Create segment editor to get access to effects
    segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
    segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
    segmentEditorNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentEditorNode")
    segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
    segmentEditorWidget.setSegmentationNode(segmentationNode)
    segmentEditorWidget.setMasterVolumeNode(masterVolumeNode)

    # Thresholding
    segmentEditorWidget.setActiveEffectByName("Threshold")
    effect = segmentEditorWidget.activeEffect()
    effect.setParameter("MinimumThreshold", lowerThreshold)
    effect.setParameter("MaximumThreshold", upperThreshold)
    effect.self().onApply()

    # Smoothing
    segmentEditorWidget.setActiveEffectByName("Smoothing")
    effect = segmentEditorWidget.activeEffect()
    effect.setParameter("SmoothingMethod", "MEDIAN")
    effect.setParameter("KernelSizeMm", 11)
    effect.self().onApply()

    if keep_largest_island:
        segmentEditorWidget.setActiveEffectByName("Islands")
        effect.self().onApply()

    # Clean up
    segmentEditorWidget = None
    slicer.mrmlScene.RemoveNode(segmentEditorNode)

    # Make segmentation results visible in 3D
    segmentationNode.CreateClosedSurfaceRepresentation()

    if to_file:
        slicer.util.saveNode(segmentationNode, to_file)

def loadVolume(filename):
    slicer.util.loadVolume(filename)

def NoInterpolate(caller,event):
    for node in slicer.util.getNodes("*").values():
        if node.IsA("vtkMRMLScalarVolumeDisplayNode"):
            node.SetInterpolate(0)

def iterScalarVolume(func):
    for node in slicer.util.getNodes("*").values():
        if node.IsA("vtkMRMLScalarVolumeNode"):
            func(node)

def showVolume(scalarVolume):
    if type(scalarVolume) == str:
        volumeNode = slicer.util.getNode("YourVolumeNode")
    elif scalarVolume.IsA("vtkMRMLScalarVolumeDisplayNode"):
        volumeNode = scalarVolume
    slicer.util.setSliceViewerLayers(background=volumeNode)