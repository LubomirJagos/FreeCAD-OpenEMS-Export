import re
from PySide2 import QtGui, QtCore, QtWidgets
import FreeCAD as App
import FreeCADGui, Part
import Draft

class FreeCADHelpers:
    def getOpenEMSObjects(self, filterStr=""):
        currentObjects = App.ActiveDocument.Objects

        objToExport = []

        for obj in currentObjects:
            if (len(filterStr) > 0 and re.search(filterStr, obj.Label, re.IGNORECASE)):
                objToExport.append(obj)
            elif (len(filterStr) == 0):
                objToExport.append(obj)

        return objToExport

    def getAllObjects(self):
        currentObjects = App.ActiveDocument.Objects
        objList = []
        for obj in currentObjects:
            item = QtWidgets.QTreeWidgetItem([obj.Label])
            if (obj.Name.find("Sketch") > -1):
                item.setIcon(0, QtGui.QIcon("./img/wire.svg"))
            elif (obj.Name.find("Discretized_Edge") > -1):
                item.setIcon(0, QtGui.QIcon("./img/curve.svg"))
            else:
                item.setIcon(0, QtGui.QIcon("./img/object.svg"))
            objList.append(item)
        return objList

    def getIconByCategory(self, categoryName):
        if 'Material' in categoryName:
            iconPath = "./img/material.svg"
        elif 'Excitation' in categoryName:
            iconPath = "./img/excitation.svg"
        elif 'Grid' in categoryName:
            iconPath = "./img/grid.svg"
        elif 'LumpedPart' in categoryName:
            iconPath = "./img/lumpedpart.svg"
        elif 'Port' in categoryName:
            iconPath = "./img/port.svg"
        else:
            iconPath = "./img/error.svg"

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

    def selectObjectByLabel(self, objLabel):
        freecadObj = App.ActiveDocument.getObjectsByLabel(objLabel)
        if (freecadObj):
            FreeCADGui.Selection.addSelection(App.ActiveDocument.Name, freecadObj[0].Name, '')

    #
    #	Draw line in Draft mode, this will be to show grid when going through object assigned to grid.
    #		p1Array - line start point
    #		p2Array - line end point
    #		rotation hardwires now pl.Rotation.Q = (0.0, 0.0, 0.0, 1.0)
    #
    def drawDraftLine(self, lineName, p1Array, p2Array, gridLineStyle="Solid"):
        pl = App.Placement()
        pl.Rotation.Q = (0.0, 0.0, 0.0, 1.0)
        pl.Base = App.Vector(p1Array[0], p1Array[1], p1Array[2])
        points = [App.Vector(p1Array[0], p1Array[1], p1Array[2]), App.Vector(p2Array[0], p2Array[1], p2Array[2])]
        line = Draft.makeWire(points, placement=pl, closed=False, face=False, support=None)
        line.Label = lineName  # set visible label how line is named, if name already exists FreeCAD adds number suffix like line001, line002, ...
        FreeCADGui.ActiveDocument.getObject(line.Name).DrawStyle = gridLineStyle
        Draft.autogroup(line)

    def drawDraftCircle(self, lineName, centerPoint, radius):
        pl = App.Placement()
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
                        freeCadObj = App.ActiveDocument.getObjectsByLabel(freeCadObjName)
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
