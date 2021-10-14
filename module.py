import re
import vtk, qt, ctk, slicer
from SegmentMesher import SegmentMesherLogic
from slicer.ScriptedLoadableModule import *
from naiveSegment import naiveSegment

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
    renderWindow = slicer.app.layoutManager().threeDWidget(0).threeDView().renderWindow()
    renderWindow.SetAlphaBitPlanes(1)
    wti = vtk.vtkWindowToImageFilter()
    wti.SetInputBufferTypeToRGBA()
    wti.SetInput(renderWindow)
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(outputfile)
    writer.SetInputConnection(wti.GetOutputPort())
    writer.Write()

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

    def generateMesh(self, inputSegmentNode, outputModelNode=None,  modelName=None, **kwargs):
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

        if not outputModelNode:
            outputModelNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode")
        if modelName:
            outputModelNode.SetName()
        outputModelNode.CreateDefaultDisplayNodes()

        cleaverConfig = {
            "segments": [], 
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