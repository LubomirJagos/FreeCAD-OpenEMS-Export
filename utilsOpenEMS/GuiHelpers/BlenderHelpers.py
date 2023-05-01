from utilsOpenEMS.GuiHelpers.CadInterface import CadInterface

import bpy

class BlenderHelpers(CadInterface):
    def __init__(self, APP_DIR=""):
        super(BlenderHelpers, self).__init__(APP_DIR)
        return

    #########################################################################################################################
    #   BLENDER SPECIFIC FUNCTIONS
    #########################################################################################################################

    def getObjects(self):

        #
        #   Simple class to have same members for rest of GUI application, it expecting items to have obj.Name, obj.Label items
        #
        class BlenderToCadObject:
            def __init__(self, name, label):
                self.Name = name
                self.Label = label

        objList = []
        for obj in bpy.data.objects:
            objList.append(BlenderToCadObject(obj.name, obj.name))

        return objList
