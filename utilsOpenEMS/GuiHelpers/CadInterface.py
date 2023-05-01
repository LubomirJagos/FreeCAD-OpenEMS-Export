import re
import os

import PySide2.QtWidgets
from PySide2 import QtGui, QtCore, QtWidgets, QtUiTools

class CadInterface:
    def __init__(self, APP_DIR=""):
        self.type = "None"
        self.APP_DIR = APP_DIR

        try:
            import FreeCAD
            import FreeCADGui
            import Draft
            self.type = "FreeCAD"
        except:
            print("No FreeCAD interface available.")

        try:
            import bpy
            self.type = "Blender"
        except:
            print("No Blender interface available.")

        if self.type == "None":
            print("No available FreeCAD or Blender interface found using default dummy one, PROGRAM WILL RUN DOING NOTHING.")
            #raise Exception("No available FreeCAD or Blender interface found.")

        return

    def getIconByCategory(self, categoryName):
        if 'Material' in categoryName:
            iconPath = os.path.join(self.APP_DIR, "img", "material.svg")
        elif 'Excitation' in categoryName:
            iconPath = os.path.join(self.APP_DIR, "img", "excitation.svg")
        elif 'Grid' in categoryName:
            iconPath = os.path.join(self.APP_DIR, "img", "grid.svg")
        elif 'LumpedPart' in categoryName:
            iconPath = os.path.join(self.APP_DIR, "img", "lumpedpart.svg")
        elif 'Probe' in categoryName:
            iconPath = os.path.join(self.APP_DIR, "img", "probe.svg")
        elif 'Port' in categoryName:
            iconPath = os.path.join(self.APP_DIR, "img", "port.svg")
        else:
            iconPath = os.path.join(self.APP_DIR, "img", "error.svg")

        return QtGui.QIcon(iconPath)

    # return all items, at least all top level
    def getAllTreeWidgetItems(self, treeWidget):
        root = treeWidget.invisibleRootItem()
        child_count = root.childCount()
        itemList = []
        for i in range(child_count):
            print('Copying tree widget item ' + root.child(i).data(0, QtCore.Qt.UserRole).getName())
            item = root.child(i)
            itemList.append(item.data(0, QtCore.Qt.UserRole))
        return itemList

    ###############################################################################################################################
    #   CAD SPECIFIC FUNCTIONS
    ###############################################################################################################################

    def getOpenEMSObjects(self, filterStr=""):
        currentObjects = self.getObjects()

        objToExport = []

        for obj in currentObjects:
            if (len(filterStr) > 0 and re.search(filterStr, obj.Label, re.IGNORECASE)):
                objToExport.append(obj)
            elif (len(filterStr) == 0):
                objToExport.append(obj)

        return objToExport

    def selectObjectByLabel(self, objLabel):
        return None

    def drawDraftLine(self, lineName, p1Array, p2Array, gridLineStyle="Solid"):
        return None

    def drawDraftCircle(self, lineName, centerPoint, radius):
        return None

    # return x,y,z boundary box of model, going through all assigned objects into model and return boundary coordinates
    def getModelBoundaryBox(self, treeWidget):
        return None

    def getObjects(self):
        print(f"{__file__} > getObjects()")
        return []

    def removeObject(self, objName):
        print(f"{__file__} > removeObject()")
        return None

    def getCurrDocumentFileName(self):
        print(f"{__file__} > getCurrDocumentFileName() > {os.path.join(self.APP_DIR, __file__)}")
        return os.path.join(self.APP_DIR, __file__)

    def getObjectsByLabel(self, objLabel):
        print(f"{__file__} > getObjectsByLabel()")
        return None

    def getObjectById(self, objId):
        print(f"{__file__} > getObjectById()")
        return None

    def loadUI(self, path_to_ui, objParent):
        print(f"{__file__} > loadUI() > Loading {path_to_ui}")
        loader = QtUiTools.QUiLoader()
        uifile = QtCore.QFile(path_to_ui)
        uifile.open(QtCore.QFile.ReadOnly)
        ui = loader.load(uifile)
        uifile.close()
        return ui

    def printError(self, msg):
        print(msg)

    def printWarning(self, msg):
        print(msg)

    def clearSelection(self):
        print(f"{__file__} > clearSelection()")
        return None

    def Vector(self,x,y,z):
        print(f"{__file__} > Vector()")
        return None

    def recompute(self):
        print(f"{__file__} > recompute()")
        return None

    def exportSTL(self, partToExport, exportFileName):
        print(f"{__file__} > exportSTL()")
        return None

if __name__ == "__main__":
    cadInterface = CadInterface()