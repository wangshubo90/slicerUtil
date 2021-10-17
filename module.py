import re
import vtk, qt, ctk, slicer
from SegmentMesher import SegmentMesherLogic
from slicer.ScriptedLoadableModule import *
import SimpleITK as sitk

def findProperty(obj, re_patter):
    return [i for i in dir(obj) if re.search(re_patter, i)]

def set3Dview(viewNode=None, bkgrColor=(255,255,255), bkgrColor2=(255,255,255), boxVisible=0, labelsVisible=0):
    if viewNode is None:
        viewNode = slicer.app.layoutManager().threeDWidget(0).mrmlViewNode()
    viewNode.SetBackgroundColor(*bkgrColor)
    viewNode.SetBackgroundColor2(*bkgrColor2)
    viewNode.SetBoxVisible(boxVisible)
    viewNode.SetAxisLabelsVisible(labelsVisible)

def loadVolume(filename):
    volumeNode = slicer.util.loadVolume(filename)
    return volumeNode

def NoInterpolate(caller,event):
    for node in slicer.util.getNodes("*").values():
        if node.IsA("vtkMRMLScalarVolumeDisplayNode"):
            node.SetInterpolate(0)

def iterScalarVolume(func):
    for node in slicer.util.getNodes("*").values():
        if node.IsA("vtkMRMLScalarVolumeNode"):
            func(node)

def showVolume(scalarVolume, foreground=None, foregroundOpacity=0):
    if type(scalarVolume) == str:
        volumeNode = slicer.util.getNode(scalarVolume)
    elif scalarVolume.IsA("vtkMRMLScalarVolumeNode"):
        volumeNode = scalarVolume
    if not foreground is None:
        if type(scalarVolume) == str:
            foreground= slicer.util.getNode(foreground)
        else:
            pass
    slicer.util.setSliceViewerLayers(background=volumeNode, foreground=foreground, foregroundOpacity=foregroundOpacity)

def showSegmentIn3D(segmentation):
    """
        segmentation: can be one of the followwing, 
                str, segmentationNode
                vtkMRMLSegmentationNode
                vtkMRMLSegmentationDisplayNode
    """
    if type(segmentation) == str:
        segmentationNode = slicer.util.getNode(segmentation)
        displayNode = segmentationNode.GetDisplayNode()
    elif segmentation.IsA("vtkMRMLSegmentationNode"):
        segmentationNode = segmentation
        displayNode = segmentationNode.GetDisplayNode()
    elif segmentation.IsA("vtkMRMLSegmentationDisplayNode"):
        displayNode = segmentation
    displayNode.SetVisibility3D(1)

def hideSegmentIn3D(segmentation):
    """
        segmentation: can be one of the followwing, 
                str, segmentationNode
                vtkMRMLSegmentationNode
                vtkMRMLSegmentationDisplayNode
    """
    if type(segmentation) == str:
        segmentationNode = slicer.util.getNode(segmentation)
        displayNode = segmentationNode.GetDisplayNode()
    elif segmentation.IsA("vtkMRMLSegmentationNode"):
        segmentationNode = segmentation
        displayNode = segmentationNode.GetDisplayNode()
    elif segmentation.IsA("vtkMRMLSegmentationDisplayNode"):
        displayNode = segmentation
    displayNode.SetVisibility3D(0)

def capture3Dview(outputfile):
    """
        outputfile : str, output file name
    """
    renderWindow = slicer.app.layoutManager().threeDWidget(0).threeDView().renderWindow()
    renderWindow.SetAlphaBitPlanes(1)
    wti = vtk.vtkWindowToImageFilter()
    wti.SetInputBufferTypeToRGBA()
    wti.SetInput(renderWindow)
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(outputfile)
    writer.SetInputConnection(wti.GetOutputPort())
    writer.Write()

def GetAllSegment(segmentation):
    """
        segmentation: either ID or the node of a segmentation
    """
    if type(segmentation) is str:
        segNode = slicer.util.getNode(segmentation)
    elif segmentation.IsA("vtkMRMLSegmentationNode"):
        segNode=segmentation
    segmentation = segNode.GetSegmentation()
    stringArray = vtk.vtkStringArray()
    segmentation.GetSegmentIDs(stringArray)
    segments = {}
    for i in range(stringArray.GetNumberOfValues()):
        segmentID = stringArray.GetValue(i)
        segment = segmentation.GetSegment(segmentID)
        segments[segmentID] = segment

    return segments

def startSegmentationEditor():
    segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
    segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
    segmentEditorNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentEditorNode")
    segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
    return {"segmentEditorWidget":segmentEditorWidget, "segmentEditorNode":segmentEditorNode}

def naiveSegment(masterVolumeNode,
                segmentEditorNode=None, 
                segmentEditorWidget=None, 
                segName="", 
                segMapName="bone", 
                to_file=None, 
                lowerThreshold=30, 
                upperThreshold=255, 
                smoothSigma=6, 
                color=(0.5,0.5,0.5),
                keep_largest_island=False, 
                cleanUp=False):
    # Create segmentation
    segmentationNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
    # segmentationNode.CreateDefaultDisplayNodes() # only needed for display
    segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(masterVolumeNode)
    segmentationNode.SetName(segName)
    addedSegmentID = segmentationNode.GetSegmentation().AddEmptySegment(segMapName)
    # Create segment editor to get access to effects
    if segmentEditorWidget is None:
        segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
    segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
    if segmentationNode is None:
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
    effect.setParameter("SmoothingMethod", "Gaussian")
    effect.setParameter("KernelSizeMm", smoothSigma)
    effect.self().onApply()

    if keep_largest_island:
        segmentEditorWidget.setActiveEffectByName("Islands")
        effect.setParameter("Operation", "KEEP_LARGEST_ISLANDS") # check other parameters https://slicer.readthedocs.io/en/latest/developer_guide/modules/segmenteditor.html
        effect.self().onApply()

    if cleanUp:
        segmentEditorWidget = None
        slicer.mrmlScene.RemoveNode(segmentEditorNode)

    # Make segmentation results visible in 3D
    segmentationNode.CreateClosedSurfaceRepresentation()
    # set color
    segmentationNode.GetSegmentation().GetSegment(addedSegmentID).SetColor(*color)
    assert segmentationNode.GetSegmentation().GetSegment(addedSegmentID).GetColor() == color

    if to_file:
        slicer.util.saveNode(segmentationNode, to_file)
    return segmentationNode, segmentEditorNode, segmentEditorWidget

class SegmentMesher3D(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self, filename, cleanUp=False, **kwards):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
        """
        if cleanUp:
            slicer.mrmlScene.Clear(0)
        self.volumeNode = loadVolume(filename)
        self.volumeNodeName = self.volumeNode.GetName()
        self.volumeNodeID = self.volumeNode.GetID()
        self.segmentationNode, self.segmentEditorNode, self.segmentEditorWidget = naiveSegment(
            self.volumeNode,
            **kwards
        )
        self.segmentID = self.segmentationNode.GetSegmentation().GetNthSegmentID(0)

    def run(self, inputSegmentNode, outputModelNode, **kwards):
        """Run as few or as many tests as needed here.
        """
        self.generateMesh(inputSegmentNode, outputModelNode, **kwards)

    def generateMesh(self, inputSegmentNode, outputModelNode=None,  modelName=None, segments=[], **kwargs):
        """ Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting the test")

        # cylinder = vtk.vtkCylinderSource()
        # cylinder.SetRadius(10)
        # cylinder.SetHeight(40)
        # cylinder.Update()
        inputSegmentNode = inputSegmentNode

        if outputModelNode is None:
            outputModelNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode")
        if modelName:
            outputModelNode.SetName(modelName)
        outputModelNode.CreateDefaultDisplayNodes()

        cleaverConfig = { 
            "additionalParameters": None, 
            "removeBackgroundMesh": True, 
            "paddingRatio": 0.10, 
            "featureScale": 2, 
            "samplingRate":0.2, 
            "rateOfChange":0.2}
        
        cleaverConfig.update(kwargs)

        logic = SegmentMesherLogic()
        logic.createMeshFromSegmentationCleaver(
            inputSegmentNode, 
            outputModelNode, 
            segments,
            **cleaverConfig)

        self.assertTrue(outputModelNode.GetMesh().GetNumberOfPoints()>0)
        self.assertTrue(outputModelNode.GetMesh().GetNumberOfCells()>0)

        # inputModelNode.GetDisplayNode().SetOpacity(0.2)

        outputDisplayNode = outputModelNode.GetDisplayNode()
        outputDisplayNode.SetColor(1,0,0)
        outputDisplayNode.SetEdgeVisibility(True)
        outputDisplayNode.SetClipping(False)

        clipNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLClipModelsNode")
        clipNode.SetRedSliceClipState(clipNode.ClipNegativeSpace)

        return outputModelNode