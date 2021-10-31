import slicer
import ctk
import vtk
import SimpleITK as sitk
import warnings
import numpy as np

__sitk__MRMLIDImageIO_Registered__ = False

def PushVolumeToSlicer(sitkimage, targetNode=None, name=None, className='vtkMRMLScalarVolumeNode'):
    """ Given a SimpleITK image, push it back to slicer for viewing
    :param targetNode: Target node that will store the image. If None then a new node will be created.
    :param className: if a new target node is created then this parameter determines node class. For label volumes, set it to vtkMRMLLabelMapVolumeNode.
    :param name: if a new target node is created then this parameter will be used as basis of node name.
      If an existing node is specified as targetNode then this value will not be used.
    """

    EnsureRegistration()

    # Create new node if needed
    if not targetNode:
        targetNode = slicer.mrmlScene.AddNewNodeByClass(className, slicer.mrmlScene.GetUniqueNameByString(name))
        targetNode.CreateDefaultDisplayNodes()

    myNodeFullITKAddress = GetSlicerITKReadWriteAddress(targetNode)
    sitk.WriteImage(sitkimage, myNodeFullITKAddress)

    return targetNode


def PullVolumeFromSlicer(nodeObjectOrName):
    """ Given a slicer MRML image node or name, return the SimpleITK
        image object.
    """
    EnsureRegistration()
    myNodeFullITKAddress = GetSlicerITKReadWriteAddress(nodeObjectOrName)
    sitkimage = sitk.ReadImage(myNodeFullITKAddress)
    return sitkimage

def GetSlicerITKReadWriteAddress(nodeObjectOrName):
    """ This function will return the ITK FileIO formatted text address
            so that the image can be read directly from the MRML scene
    """
    myNode = nodeObjectOrName if isinstance(nodeObjectOrName, slicer.vtkMRMLNode) else slicer.util.getNode(nodeObjectOrName)
    myNodeSceneAddress = myNode.GetScene().GetAddressAsString("").replace('Addr=','')
    myNodeSceneID = myNode.GetID()
    myNodeFullITKAddress = 'slicer:' + myNodeSceneAddress + '#' + myNodeSceneID
    return myNodeFullITKAddress

def EnsureRegistration():
    """Make sure MRMLIDImageIO reader is registered.
    """
    if 'MRMLIDImageIO' in sitk.ImageFileReader().GetRegisteredImageIOs():
      # already registered
      return

    # Probably this hack is not needed anymore, but it would require some work to verify this,
    # so for now just leave this here:
    # This is a complete hack, but attempting to read a dummy file with AddArchetypeVolume
    # has a side effect of registering the MRMLIDImageIO file reader.
    global __sitk__MRMLIDImageIO_Registered__
    if __sitk__MRMLIDImageIO_Registered__:
      return
    vl = slicer.modules.volumes.logic()
    volumeNode = vl.AddArchetypeVolume('_DUMMY_DOES_NOT_EXIST__','invalidRead')
    __sitk__MRMLIDImageIO_Registered__ = True

def down_scale(tar_img,down_scale_factor=1.0,new_dtype=sitk.sitkFloat32):
    '''
    Description:
        Use sitk.Resample method to extract an image with lower resolution
    Args:
        tar_img: sitk.Image / numpy.ndarray
        down_scale_factor:  float/double, 
    Returns:
        sitk.Image
    '''
    if type(tar_img) == np.ndarray:
        tar_img = sitk.GetImageFromArray(tar_img)

    dimension = sitk.Image.GetDimension(tar_img)
    idt_transform = sitk.Transform(dimension,sitk.sitkIdentity)
    resample_size = [int(i/down_scale_factor) for i in sitk.Image.GetSize(tar_img)]
    resample_spacing = [i*down_scale_factor for i in sitk.Image.GetSpacing(tar_img)]
    resample_origin = sitk.Image.GetOrigin(tar_img)
    resample_direction = sitk.Image.GetDirection(tar_img)
    new_img = sitk.Resample(sitk.Cast(tar_img,sitk.sitkFloat32),resample_size, idt_transform, sitk.sitkLinear,
                     resample_origin,resample_spacing,resample_direction,new_dtype)
    new_img = sitk.Cast(new_img,new_dtype)

    return new_img