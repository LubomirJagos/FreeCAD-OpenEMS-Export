#   author: Lubomir Jagos
#
#
import os
from PySide2 import QtGui, QtCore, QtWidgets
import numpy as np
import re
import math

from utilsOpenEMS.GlobalFunctions.GlobalFunctions import _bool, _r
from utilsOpenEMS.SettingsItem.SettingsItem import SettingsItem
from utilsOpenEMS.GuiHelpers.GuiHelpers import GuiHelpers
from utilsOpenEMS.GuiHelpers.FactoryCadInterface import FactoryCadInterface

class CommonScriptLinesGenerator:

    #
    #   constructor, get access to form GUI
    #
    def __init__(self, form, statusBar = None):
        self.form = form
        self.statusBar = statusBar

        self.internalPortIndexNamesList = {}
        self.internalMaterialIndexNamesList = {}
        self.internalNF2FFIndexNamesList = {}

        #
        # GUI helpers function like display message box and so
        #
        self.guiHelpers = GuiHelpers(self.form, statusBar = self.statusBar)
        self.cadHelpers = FactoryCadInterface.createHelper()

    def getUnitLengthFromUI_m(self):
        unitStr = self.form.simParamsDeltaUnitList.currentText()
        return SettingsItem.getUnitsAsNumber(unitStr)

    def getFreeCADUnitLength_m(self):
        # # FreeCAD uses mm internally, so getFreeCADUnitLength_m() should always return 0.001.
        # # Below is one way to retrieve this value from schemaTranslate() without implying it.
        # [qtyStr, standardUnitsPerTargetUnit, targetUnitStr] = App.Units.schemaTranslate( App.Units.Quantity("1.0 m"), App.Units.Scheme.SI2 )
        # return 1.0 / standardUnitsPerTargetUnit # standard unit is mm : return 1.0 / 1000 [m]
        return 0.001

    def getItemsByClassName(self):
        categoryCount = self.form.objectAssignmentRightTreeWidget.invisibleRootItem().childCount()
        categoryNodes = [self.form.objectAssignmentRightTreeWidget.topLevelItem(k) for k in range(categoryCount)]
        itemsByClassName = {}
        for m, categoryNode in enumerate(categoryNodes):  # for each category
            for k in range(categoryNode.childCount()):  # for each child item in a given category
                item = categoryNode.child(k)
                itemData = item.data(0, QtCore.Qt.UserRole)
                if not itemData:
                    continue
                itemClassName = itemData.__class__.__name__
                if not (itemClassName in itemsByClassName):
                    itemsByClassName[itemClassName] = [[item, itemData]]
                else:
                    itemsByClassName[itemClassName].append([item, itemData])

        print("generateOpenEMSScript: Item classes found = " + ", ".join(itemsByClassName.keys()))

        return itemsByClassName

    #
    #	Returns object priority
    #		priorityItemName - string which identifies item by its text in priority tree view widget
    #
    def getItemPriority(self, priorityItemName):
        #
        #	priority is read from tree view
        #
        priorityItemValue = 42
        itemsCount = self.form.objectAssignmentPriorityTreeView.topLevelItemCount()
        for k in range(itemsCount):
            priorityItem = self.form.objectAssignmentPriorityTreeView.topLevelItem(k)
            if priorityItemName in priorityItem.text(0):
                #
                #	THIS IS MY FORMULA TO HAVE AT LEAST TWO 0 AT END AND NOT HAVE PRIORITY INDEX 0 BUT START AT 100 AT LEAST!
                #		ATTENTION: higher number means higher priority so fromual is: (1001 - k)     ...to get item at top of tree view with highest priority numbers!
                #
                priorityItemValue = (100 - k) * 100
                break  # this will break loop SO JUST ONE ITEM FROM PRIORITY LIST IS DELETED

        return priorityItemValue

    #
    #   Returns current FreeCAD file:
    #       - absolute directory
    #       - name without extension
    #
    def getCurrDir(self):
        programname = os.path.basename(self.cadHelpers.getCurrDocumentFileName())
        programDir = os.path.dirname(self.cadHelpers.getCurrDocumentFileName())
        programbase, ext = os.path.splitext(programname)  # extract basename and ext from filename
        return [programDir, programbase]

    #
    #   Creates output dir in current FreeCAD file directory if not exists.
    #       outputDir - absolute path to directory where folder with simulation files should be created
    #
    def createOuputDir(self, outputDir):
        programname = os.path.basename(self.cadHelpers.getCurrDocumentFileName())     # FreeCAD filename with extension
        programdir = os.path.dirname(self.cadHelpers.getCurrDocumentFileName())       # FreeCAD file directory
        programbase, ext = os.path.splitext(programname)                # FreeCAD filename without extension

        #
        #   Simulation files will be saved in folder named based on FreeCAD filename and suffix _openEMS_simulation
        #       If parameter outputDir is not set this folder will be generated in the same folder as FreeCAD file.
        #       If outputDir is set folder with simulation folder with files is genenrated next to .ini file
        #
        if outputDir is None or outputDir == False:
            absoluteOutputDir = f"{programdir}/{programbase}_openEMS_simulation"
        else:
            absoluteOutputDir = outputDir

        if not os.path.exists(absoluteOutputDir):
            os.makedirs(absoluteOutputDir)
            print(f"Created directory for simulation: {outputDir}")

        return absoluteOutputDir

    def reportFreeCADItemSettings(self, items):
        # "FreeCAD item detection everywhere in Main Tree!!! need to get rid this, now it's tolerated during development!"
        if not items:
            return

        for [item, currSetting] in items:
            #	GET PARENT NODE DATATYPE
            print("#")
            print("#FREECAD OBJ.")
            if (str(item.parent().text(0)) == "Grid"):
                print("name: Grid Default")
                print("type: FreeCADSettingsItem")
                pass
            elif (str(item.parent().text(0)) == "Ports"):
                print("name: Port Default")
                print("type: FreeCADSettingsItem")
                pass
            elif (str(item.parent().text(0)) == "Excitation"):
                print("name: Excitation Default")
                print("type: FreeCADSettingsItem")
                pass
            elif (str(item.parent().text(0)) == "Materials"):
                print("name: Material Default")
                print("type: FreeCADSettingsItem")
                pass
            else:
                print("Parent of FreeCADSettingItem UNKNOWN")
                pass

    def getModelCoordsType(self):
        """
        Returns current coordinate system, as there can be just rectangular or just cylindrical for all grid items it's enough to look at first grid item.
        :return: string (rectangular, cylindrical)
        """
        if self.form.gridSettingsTreeView.topLevelItemCount() > 0:
            coordsType = self.form.gridSettingsTreeView.topLevelItem(0).data(0, QtCore.Qt.UserRole).coordsType
        else:
            coordsType = "rectangular"
        return coordsType

    def getSketchPointsForConductingSheet(self, freeCadObj):
        """
        Generate points for conducting sheet area. Conducting sheet must lay in XY,XZ or YZ plane.
        :return: list of vertices which creates area of conducting sheet.
        """

        #
        #   Sketch is added as polygon into conducting sheet material
        #
        normDir = ""
        elevation = 0.0
        points = [[],[]]
        bbCoords = freeCadObj.Shape.BoundBox

        if (_r(bbCoords.XMin) == _r(bbCoords.XMax)):
            normDir = "x"
            elevation = _r(bbCoords.XMin)
        elif (_r(bbCoords.YMin) == _r(bbCoords.YMax)):
            normDir = "y"
            elevation = _r(bbCoords.YMin)
        elif (_r(bbCoords.ZMin) == _r(bbCoords.ZMax)):
            normDir = "z"
            elevation = _r(bbCoords.ZMin)
        else:
            normDir = "ERROR: sketch not lay in coordinate plane, conducting sheet polygon must lay in XY, XZ or YZ plane"

        """
        for geometryObj in freeCadObj.Geometry:
            if (str(type(geometryObj)).find("LineSegment") > -1):
                points[0].append(_r(geometryObj.StartPoint.x))
                points[1].append(_r(geometryObj.StartPoint.y))
        """

        if normDir == 'x':
            for v in freeCadObj.Shape.OrderedVertexes:
                points[0].append(_r(v.Y))
                points[1].append(_r(v.Z))
            points[0].append(_r(freeCadObj.Shape.OrderedVertexes[0].Y))
            points[1].append(_r(freeCadObj.Shape.OrderedVertexes[0].Z))
        elif normDir == 'y':
            for v in freeCadObj.Shape.OrderedVertexes:
                points[0].append(_r(v.X))
                points[1].append(_r(v.Z))
            points[0].append(_r(freeCadObj.Shape.OrderedVertexes[0].X))
            points[1].append(_r(freeCadObj.Shape.OrderedVertexes[0].Z))
        elif normDir == 'z':
            for v in freeCadObj.Shape.OrderedVertexes:
                points[0].append(_r(v.X))
                points[1].append(_r(v.Y))
            points[0].append(_r(freeCadObj.Shape.OrderedVertexes[0].X))
            points[1].append(_r(freeCadObj.Shape.OrderedVertexes[0].Y))

        return normDir, elevation, points

    def getFacePointsForConductingSheet(self, freeCadObj):

        normDir = ""
        elevation = ""
        facesList = []

        bbCoords = freeCadObj.Shape.BoundBox

        if (len(freeCadObj.Shape.Faces) > 0):

            if (_r(bbCoords.XMin) == _r(bbCoords.XMax)):
                normDir = "x"
                elevation = bbCoords.XMin

                for face in freeCadObj.Shape.Faces:
                    points = [[], []]
                    for vertex in face.Vertexes:
                        points[0].append(_r(vertex.Y))
                        points[1].append(_r(vertex.Z))
                    points[0].append(_r(face.Vertexes[0].Y))
                    points[1].append(_r(face.Vertexes[0].Z))
                    facesList.append(points)

            elif (_r(bbCoords.YMin) == _r(bbCoords.YMax)):
                normDir = "y"
                elevation = bbCoords.YMin

                for face in freeCadObj.Shape.Faces:
                    points = [[], []]
                    for vertex in face.Vertexes:
                        points[0].append(_r(vertex.X))
                        points[1].append(_r(vertex.Z))
                    points[0].append(_r(face.Vertexes[0].X))
                    points[1].append(_r(face.Vertexes[0].Z))
                    facesList.append(points)

            elif (_r(bbCoords.ZMin) == _r(bbCoords.ZMax)):
                normDir = "z"
                elevation = bbCoords.ZMin

                for face in freeCadObj.Shape.Faces:
                    points = [[], []]
                    for vertex in face.Vertexes:
                        points[0].append(_r(vertex.X))
                        points[1].append(_r(vertex.Y))
                    points[0].append(_r(face.Vertexes[0].X))
                    points[1].append(_r(face.Vertexes[0].Y))
                    facesList.append(points)

        else:
            pass

        return normDir, elevation, facesList
