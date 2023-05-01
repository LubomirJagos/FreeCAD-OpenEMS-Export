from utilsOpenEMS.GuiHelpers.CadInterface import CadInterface

import FreeCAD
import FreeCADGui
import Draft
import Mesh

class FreeCADHelpers(CadInterface):

    def __init__(self, APP_DIR=""):
        super(FreeCADHelpers, self).__init__(APP_DIR)

    def selectObjectByLabel(self, objLabel):
        freecadObj = FreeCAD.ActiveDocument.getObjectsByLabel(objLabel)
        if (freecadObj):
            FreeCADGui.Selection.addSelection(FreeCAD.ActiveDocument.Name, freecadObj[0].Name, '')

    #
    #	Draw line in Draft mode, this will be to show grid when going through object assigned to grid.
    #		p1Array - line start point
    #		p2Array - line end point
    #		rotation hardwires now pl.Rotation.Q = (0.0, 0.0, 0.0, 1.0)
    #
    def drawDraftLine(self, lineName, p1Array, p2Array, gridLineStyle="Solid"):
        pl = FreeCAD.Placement()
        pl.Rotation.Q = (0.0, 0.0, 0.0, 1.0)
        pl.Base = FreeCAD.Vector(p1Array[0], p1Array[1], p1Array[2])
        points = [FreeCAD.Vector(p1Array[0], p1Array[1], p1Array[2]), FreeCAD.Vector(p2Array[0], p2Array[1], p2Array[2])]
        line = Draft.makeWire(points, placement=pl, closed=False, face=False, support=None)
        line.Label = lineName  # set visible label how line is named, if name already exists FreeCAD adds number suffix like line001, line002, ...
        FreeCADGui.ActiveDocument.getObject(line.Name).DrawStyle = gridLineStyle
        Draft.autogroup(line)

    def drawDraftCircle(self, lineName, centerPoint, radius):
        pl = FreeCAD.Placement()
        pl.Rotation.Q = (0.0, 0.0, 0.0, 1.0)
        pl.Base = centerPoint
        circle = Draft.makeCircle(radius=radius, placement=pl, face=False, support=None)
        circle.Label = lineName
        Draft.autogroup(circle)

    # return x,y,z boundary box of model, going through all assigned objects into model and return boundary coordinates
    def getModelBoundaryBox(self, treeWidget):
        root = treeWidget.invisibleRootItem()
        child_count = root.childCount()
        itemList = []

        # iterate over whole objects assignments treeview and get just material or grid freecad objects because they are just one which are meshed
        for i in range(child_count):
            if (root.child(i).text(0) == "Material" or root.child(i).text(0) == "Grid"):
                child_count2 = root.child(i).childCount()
                for j in range(child_count2):
                    child_count3 = root.child(i).child(j).childCount()
                    for k in range(child_count3):
                        print(root.child(i).child(j).child(k).data(0, QtCore.Qt.UserRole).getName())
                        freeCadObjName = root.child(i).child(j).child(k).data(0, QtCore.Qt.UserRole).getName()
                        freeCadObj = FreeCAD.ActiveDocument.getObjectsByLabel(freeCadObjName)
                        itemList.append(freeCadObj)

        # values initialization, for minimal values must have be init to big numbers to be sure they will be overwritten, for max values have to put their small numbers to be sure to be overwritten
        minX = 9999
        minY = 9999
        minZ = 9999
        maxX = -9999
        maxY = -9999
        maxZ = -9999
        for i in range(len(itemList)):
            print(itemList[i][0].Shape.BoundBox)
            bBox = itemList[i][0].Shape.BoundBox
            if (bBox.XMin < minX):
                minX = bBox.XMin
            if (bBox.YMin < minY):
                minY = bBox.YMin
            if (bBox.ZMin < minZ):
                minZ = bBox.ZMin
            if (bBox.XMax > maxX):
                maxX = bBox.XMax
            if (bBox.YMax > maxY):
                maxY = bBox.YMax
            if (bBox.ZMax > maxZ):
                maxZ = bBox.ZMax

        return minX, minY, minZ, maxX, maxY, maxZ

    def getObjects(self):
        return FreeCAD.ActiveDocument.Objects

    def removeObject(self, objName):
        FreeCAD.ActiveDocument.removeObject(objName)
    def getCurrDocumentFileName(self):
        return FreeCAD.ActiveDocument.FileName

    def getObjectsByLabel(self, objLabel):
        return FreeCAD.ActiveDocument.getObjectsByLabel(objLabel)

    def getObjectById(self, objId):
        return FreeCAD.ActiveDocument.getObject(objId)

    def loadUI(self, path_to_ui, obj):
        return FreeCADGui.PySideUic.loadUi(path_to_ui, obj)

    def printError(self, msg):
        FreeCAD.Console.PrintError(msg)

    def printWarning(self, msg):
        FreeCAD.Console.PrintWarning(msg)

    def clearSelection(self):
        FreeCADGui.Selection.clearSelection()

    def getCurrDocumentFileName(self):
        return FreeCAD.ActiveDocument.FileName

    def Vector(self,x,y,z):
        return FreeCAD.Vector(x,y,z)

    def recompute(self):
        FreeCAD.ActiveDocument.recompute()

    def exportSTL(self, partToExport, exportFileName):
        Mesh.export(partToExport, exportFileName)
