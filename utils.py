import re
import slicer

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

def showVolume(scalarVolume):
    if type(scalarVolume) == str:
        volumeNode = slicer.util.getNode("YourVolumeNode")
    elif scalarVolume.IsA("vtkMRMLScalarVolumeDisplayNode"):
        volumeNode = scalarVolume
    slicer.util.setSliceViewerLayers(background=volumeNode)