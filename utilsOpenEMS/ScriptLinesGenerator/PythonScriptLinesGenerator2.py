#   author: Lubomir Jagos
#
#
import os
from PySide2 import QtGui, QtCore, QtWidgets
import numpy as np
import re
import math

from utilsOpenEMS.GlobalFunctions.GlobalFunctions import _bool, _r, _r2
from utilsOpenEMS.ScriptLinesGenerator.OctaveScriptLinesGenerator2 import OctaveScriptLinesGenerator2
from utilsOpenEMS.GuiHelpers.GuiHelpers import GuiHelpers
from utilsOpenEMS.GuiHelpers.FactoryCadInterface import FactoryCadInterface

from utilsOpenEMS.ScriptLinesGenerator.CommonScriptLinesGenerator import CommonScriptLinesGenerator

class PythonScriptLinesGenerator2(CommonScriptLinesGenerator):

    #
    #   constructor, get access to form GUI
    #
    def __init__(self, form, statusBar = None):
        super(PythonScriptLinesGenerator2, self).__init__(form, statusBar)

    def getCoordinateSystemScriptLines(self):
        genScript = ""

        genScript += "#######################################################################################################################################\n"
        genScript += "# COORDINATE SYSTEM\n"
        genScript += "#######################################################################################################################################\n"

        """ # Till now not used, just using rectangular coordination type, cylindrical MUST BE IMPLEMENTED!
        gridCoordsType = self.getModelCoordsType()
        if (gridCoordsType == "rectangular"):
            genScript += "CSX = InitCSX('CoordSystem',0); # Cartesian coordinate system.\n"
        elif (gridCoordsType == "cylindrical"):
            genScript += "CSX = InitCSX('CoordSystem',1); # Cylindrical coordinate system.\n"
        else:
            genScript += "%%%%%% ERROR GRID COORDINATION SYSTEM TYPE UNKNOWN"				
        """

        genScript += "def mesh():\n"
        genScript += "\tx,y,z\n"
        genScript += "\n"
        genScript += "mesh.x = np.array([]) # mesh variable initialization (Note: x y z implies type Cartesian).\n"
        genScript += "mesh.y = np.array([])\n"
        genScript += "mesh.z = np.array([])\n"
        genScript += "\n"
        genScript += "openEMS_grid = CSX.GetGrid()\n"
        genScript += "openEMS_grid.SetDeltaUnit(unit) # First call with empty mesh to set deltaUnit attribute.\n"
        genScript += "\n"

        return genScript

    def getMaterialDefinitionsScriptLines(self, items, outputDir=None, generateObjects=True):
        genScript = ""

        genScript += "#######################################################################################################################################\n"
        genScript += "# MATERIALS AND GEOMETRY\n"
        genScript += "#######################################################################################################################################\n"

        # PEC is created by default due it's used when microstrip port is defined, so it's here to have it here.
        # Note that the user will need to create a metal named 'PEC' and populate it to avoid a warning
        # about "no primitives assigned to metal 'PEC'".
        genScript += "materialList = {}\n"                              # !!!THIS IS ON PURPOSE NOT LITERAL {} brackets are generated into code for python
        genScript += "\n"

        if not items:
            return genScript

        materialCounter = -1    #increment of this variable is at beginning f for loop so start at 0
        simObjectCounter = 0

        # now export material children, if it's object export as STL, if it's curve export as curve
        if (generateObjects):
            for [item, currSetting] in items:

                #
                #   Materials are stored in variables in python script, so this is counter to create universal name ie. material_1, material_2, ...
                #
                materialCounter += 1

                print(currSetting)
                if (currSetting.getName() == 'Material Default'):
                    print("#Material Default")
                    print("---")
                    continue

                print("#")
                print("#MATERIAL")
                print("#name: " + currSetting.getName())
                print("#epsilon, mue, kappa, sigma")
                print("#" + str(currSetting.constants['epsilon']) + ", " + str(currSetting.constants['mue']) + ", " + str(
                    currSetting.constants['kappa']) + ", " + str(currSetting.constants['sigma']))

                genScript += f"## MATERIAL - {currSetting.getName()}\n"
                materialPythonVariable = f"materialList['{currSetting.getName()}']"

                if (currSetting.type == 'metal'):
                    genScript += f"{materialPythonVariable} = CSX.AddMetal('{currSetting.getName()}')\n"
                    genScript += "\n"
                    self.internalMaterialIndexNamesList[currSetting.getName()] = materialPythonVariable
                elif (currSetting.type == 'userdefined'):
                    self.internalMaterialIndexNamesList[currSetting.getName()] = materialPythonVariable
                    genScript += f"{materialPythonVariable} = CSX.AddMaterial('{currSetting.getName()}')\n"
                    genScript += "\n"

                    smp_args = []
                    if str(currSetting.constants['epsilon']) != "0":
                        smp_args.append(f"epsilon={str(currSetting.constants['epsilon'])}")
                    if str(currSetting.constants['mue']) != "0":
                        smp_args.append(f"mue={str(currSetting.constants['mue'])}")
                    if str(currSetting.constants['kappa']) != "0":
                        smp_args.append(f"kappa={str(currSetting.constants['kappa'])}")
                    if str(currSetting.constants['sigma']) != "0":
                        smp_args.append(f"sigma={str(currSetting.constants['sigma'])}")

                    genScript += f"{materialPythonVariable}.SetMaterialProperty(" + ", ".join(smp_args) + ")\n"
                elif (currSetting.type == 'conducting sheet'):
                    genScript += f"{materialPythonVariable} = CSX.AddConductingSheet(" + \
                                 f"'{currSetting.getName()}', " + \
                                 f"conductivity={str(currSetting.constants['conductingSheetConductivity'])}, " + \
                                 f"thickness={str(currSetting.constants['conductingSheetThicknessValue'])}*{str(currSetting.getUnitsAsNumber(currSetting.constants['conductingSheetThicknessUnits']))}" + \
                                 f")\n"
                    genScript += "\n"
                    self.internalMaterialIndexNamesList[currSetting.getName()] = materialPythonVariable

                # first print all current material children names
                for k in range(item.childCount()):
                    childName = item.child(k).text(0)
                    print("##Children:")
                    print("\t" + childName)

                # now export material children, if it's object export as STL, if it's curve export as curve
                for k in range(item.childCount()):
                    simObjectCounter += 1               #counter for objects
                    childName = item.child(k).text(0)

                    #
                    #	getting item priority
                    #
                    objModelPriorityItemName = item.parent().text(0) + ", " + item.text(0) + ", " + childName
                    objModelPriority = self.getItemPriority(objModelPriorityItemName)

                    # getting reference to FreeCAD object
                    freeCadObj = [i for i in self.cadHelpers.getObjects() if (i.Label) == childName][0]

                    #
                    #   HERE IS OBJECT GENERATOR THERE ARE FEW SPECIAL CASES WHICH ARE HANDLED FIRST AND IF OBJECT IS NORMAL STRUCTURE AT THE END IS GENERATED AS .stl FILR:
                    #       - conducting sheet = just plane is generated, in case of 3D object shell of object bounding box is generated
                    #       - discretized edge = curve from line is generated
                    #       - sketch           = curve is generated from it's vertices
                    #
                    if (currSetting.type == 'conducting sheet'):
                        #
                        #   Here comes object generator for conducting sheet. It's possible to define it as plane in XY, XZ, YZ plane in cartesian coords and XY plane in cylindrical coords.
                        #   So in case of conducting sheet no .stl is generated, it will be generated rectangle based on bounding box.
                        #
                        genScript += "##conducting sheet object\n"
                        genScript += f"#object Label: {freeCadObj.Label}\n"
                        bbCoords = freeCadObj.Shape.BoundBox

                        if (freeCadObj.Name.find("Sketch") > -1):
                            #
                            # If object is sketch then it's added as it outline
                            #

                            normDir, elevation, points = self.getSketchPointsForConductingSheet(freeCadObj)
                            if not normDir.startswith("ERROR"):
                                genScript += "points = [[],[]]\n"
                                if len(points[0])  == 0:
                                    genScript += "## ERROR, no points for polygon for conducting sheet nothing generated"
                                else:
                                    for k in range(len(points[0])):
                                        genScript += f"points[0].append({points[0][k]})\n"
                                        genScript += f"points[1].append({points[1][k]})\n"
                                genScript += "\n"

                                genScript += f"{materialPythonVariable}.AddPolygon(points, '{normDir}', {elevation}, priority={objModelPriority})\n"
                                genScript += "\n"
                                print("material conducting sheet: polygon into conducting sheet added.")
                            else:
                                genScript += f"## {normDir}\n"
                                genScript += "\n"
                                print("ERROR: material conducting sheet: " + normDir)

                        elif (_r(bbCoords.XMin) == _r(bbCoords.XMax) or _r(bbCoords.YMin) == _r(bbCoords.YMax) or _r(bbCoords.ZMin) == _r(bbCoords.ZMax)):
                            #
                            # Adding planar object into conducting sheet, if it consists from faces then each face is added as polygon.
                            #

                            normDir, elevation, facesList = self.getFacePointsForConductingSheet(freeCadObj)
                            if normDir != "":
                                for face in facesList:
                                    genScript += f"points = [[],[]]\n"
                                    for pointIndex in range(len(face[0])):
                                        genScript += f"points[0].append({face[0][pointIndex]})\n"
                                        genScript += f"points[1].append({face[1][pointIndex]})\n"
                                        genScript += "\n"
                                    genScript += f"{materialPythonVariable}.AddPolygon(points, '{normDir}', {elevation}, priority={objModelPriority})\n"
                                    genScript += "\n"
                            else:
                                genScript += f"#\tObject has no faces, conducting sheet is generated based on object bounding box since it's planar.\n"
                                genScript += f"{materialPythonVariable}.AddBox([{_r(bbCoords.XMin)},{_r(bbCoords.YMin)},{_r(bbCoords.ZMin)}], [{_r(bbCoords.XMax)},{_r(bbCoords.YMax)},{_r(bbCoords.ZMax)}], priority={objModelPriority})\n"
                                genScript += "\n"

                        else:
                            #
                            # If object is 3D object then it's boundaries are added as conducting sheets.
                            #

                            genScript += f"#\tObject is 3D so there are sheets on its boundary box generated.\n"
                            genScript += f"{materialPythonVariable}.AddBox([{_r(bbCoords.XMin)}, {_r(bbCoords.YMin)}, {_r(bbCoords.ZMin)}], [{_r(bbCoords.XMax)}, {_r(bbCoords.YMax)}, {_r(bbCoords.ZMin)}], priority={objModelPriority})\n"
                            genScript += f"{materialPythonVariable}.AddBox([{_r(bbCoords.XMin)}, {_r(bbCoords.YMin)}, {_r(bbCoords.ZMin)}], [{_r(bbCoords.XMax)}, {_r(bbCoords.YMin)}, {_r(bbCoords.ZMax)}], priority={objModelPriority})\n"
                            genScript += f"{materialPythonVariable}.AddBox([{_r(bbCoords.XMin)}, {_r(bbCoords.YMin)}, {_r(bbCoords.ZMin)}], [{_r(bbCoords.XMin)}, {_r(bbCoords.YMax)}, {_r(bbCoords.ZMax)}], priority={objModelPriority})\n"
                            genScript += f"{materialPythonVariable}.AddBox([{_r(bbCoords.XMin)}, {_r(bbCoords.YMin)}, {_r(bbCoords.ZMax)}], [{_r(bbCoords.XMax)}, {_r(bbCoords.YMax)}, {_r(bbCoords.ZMax)}], priority={objModelPriority})\n"
                            genScript += f"{materialPythonVariable}.AddBox([{_r(bbCoords.XMin)}, {_r(bbCoords.YMax)}, {_r(bbCoords.ZMin)}], [{_r(bbCoords.XMax)}, {_r(bbCoords.YMax)}, {_r(bbCoords.ZMax)}], priority={objModelPriority})\n"
                            genScript += f"{materialPythonVariable}.AddBox([{_r(bbCoords.XMax)}, {_r(bbCoords.YMin)}, {_r(bbCoords.ZMin)}], [{_r(bbCoords.XMax)}, {_r(bbCoords.YMax)}, {_r(bbCoords.ZMax)}], priority={objModelPriority})\n"
                            genScript += "\n"

                    elif (freeCadObj.Name.find("Discretized_Edge") > -1):
                        #
                        #	Adding discretized curve
                        #

                        curvePoints = freeCadObj.Points
                        genScript += "points = [[],[],[]]\n"
                        for k in range(0, len(curvePoints)):
                            genScript += f"points[0].append({_r(curvePoints[k].x)})\n"
                            genScript += f"points[1].append({_r(curvePoints[k].y)})\n"
                            genScript += f"points[2].append({_r(curvePoints[k].z)})\n"
                            genScript += "\n"

                        genScript += f"{materialPythonVariable}.AddCurve(points, priority={objModelPriority})\n"
                        genScript += "\n"
                        print("Curve added to generated script using its points.")

                    elif (freeCadObj.Name.find("Sketch") > -1):
                        #
                        #	Adding JUST LINE SEGMENTS FROM SKETCH, THIS NEED TO BE IMPROVED TO PROPERLY GENERATE CURVE FROM SKETCH,
                        #	there can be circle, circle arc and maybe something else in sketch geometry
                        #

                        genScript += "points = [[],[],[]]\n"

                        """
                        # WRONG SINCE StartPoint, EndPoint are defined in XY and not in absolute coordinates
                        for geometryObj in freeCadObj.Geometry:
                            if (str(type(geometryObj)).find("LineSegment") > -1):
                                genScript += f"points[0].append({geometryObj.StartPoint.x})\n"
                                genScript += f"points[1].append({geometryObj.StartPoint.y})\n"
                                genScript += f"points[2].append({geometryObj.StartPoint.z})\n"

                                genScript += f"points[0].append({geometryObj.EndPoint.x})\n"
                                genScript += f"points[1].append({geometryObj.EndPoint.y})\n"
                                genScript += f"points[2].append({geometryObj.EndPoint.z})\n"

                                genScript += "\n"
                        """

                        for v in freeCadObj.Shape.OrderedVertexes:
                            genScript += f"points[0].append({_r(v.X)})\n"
                            genScript += f"points[1].append({_r(v.Y)})\n"
                            genScript += f"points[2].append({_r(v.Z)})\n"
                            genScript += "\n"

                        #   HERE IS MADE ASSUMPTION THAT:
                        #       We suppose in sketch there are no mulitple closed sketches
                        #
                        #   Add first vertex into list
                        #
                        v = freeCadObj.Shape.OrderedVertexes[0]
                        if len(freeCadObj.OpenVertices) == 0:
                            genScript += f"points[0].append({_r(v.X)})\n"
                            genScript += f"points[1].append({_r(v.Y)})\n"
                            genScript += f"points[2].append({_r(v.Z)})\n"
                            genScript += "\n"

                        genScript += f"{materialPythonVariable}.AddCurve(points, priority={objModelPriority})\n"
                        genScript += "\n"
                        print("Line segments from sketch added.")

                    else:
                        #
                        #	Adding part as STL model, first export it into file and that file load using octave openEMS function
                        #

                        currDir, baseName = self.getCurrDir()
                        stlModelFileName = childName + "_gen_model.stl"

                        #genScript += "CSX = ImportSTL( CSX, '" + currSetting.getName() + "'," + str(
                        #    objModelPriority) + ", [currDir '/" + stlModelFileName + "'],'Transform',{'Scale', fc_unit/unit} );\n"
                        genScript += f"{materialPythonVariable}.AddPolyhedronReader(os.path.join(currDir,'{stlModelFileName}'), priority={objModelPriority}).ReadFile()\n"

                        #   _____ _______ _                                        _   _
                        #  / ____|__   __| |                                      | | (_)
                        # | (___    | |  | |        __ _  ___ _ __   ___ _ __ __ _| |_ _  ___  _ __
                        #  \___ \   | |  | |       / _` |/ _ \ '_ \ / _ \ '__/ _` | __| |/ _ \| '_ \
                        #  ____) |  | |  | |____  | (_| |  __/ | | |  __/ | | (_| | |_| | (_) | | | |
                        # |_____/   |_|  |______|  \__, |\___|_| |_|\___|_|  \__,_|\__|_|\___/|_| |_|
                        #                           __/ |
                        #                          |___/
                        #
                        # going through each concrete material items and generate their .stl files

                        currDir = os.path.dirname(self.cadHelpers.getCurrDocumentFileName())
                        partToExport = [i for i in self.cadHelpers.getObjects() if (i.Label) == childName]

                        #output directory path construction, if there is no parameter for output dir then output is in current freecad file dir
                        if (not outputDir is None):
                            exportFileName = os.path.join(outputDir, stlModelFileName)
                        else:
                            exportFileName = os.path.join(currDir, stlModelFileName)

                        self.cadHelpers.exportSTL(partToExport, exportFileName)
                        print("Material object exported as STL into: " + stlModelFileName)

                genScript += "\n"   #newline after each COMPLETE material category code generated

            genScript += "\n"

        return genScript

    def getCartesianOrCylindricalScriptLinesFromStartStop(self, bbCoords, startPointName=None, stopPointName=None):
        genScript = "";
        refUnit = self.getUnitLengthFromUI_m()  # Coordinates need to be given in drawing units
        sf = self.getFreeCADUnitLength_m() / refUnit  # scaling factor for FreeCAD units to drawing units

        strPortCoordsCartesianToCylindrical = ""
        strPortCoordsCartesianToCylindrical += "[generatedAuxTheta, generatedAuxR, generatedAuxZ] = cart2pol(portStart);\n"
        strPortCoordsCartesianToCylindrical += "portStart = [generatedAuxR, generatedAuxTheta, generatedAuxZ];\n"
        strPortCoordsCartesianToCylindrical += "[generatedAuxTheta, generatedAuxR, generatedAuxZ] = cart2pol(portStop);\n"
        strPortCoordsCartesianToCylindrical += "portStop = [generatedAuxR, generatedAuxTheta, generatedAuxZ];\n"

        if (self.getModelCoordsType() == "cylindrical"):
            # CYLINDRICAL COORDINATE TYPE USED
            if ((bbCoords.XMin <= 0 and bbCoords.YMin <= 0 and bbCoords.XMax >= 0 and bbCoords.YMax >= 0) or
                (bbCoords.XMin >= 0 and bbCoords.YMin >= 0 and bbCoords.XMax <= 0 and bbCoords.YMax <= 0)
            ):
                if (_r2(bbCoords.XMin) == _r2(bbCoords.XMax) or _r2(bbCoords.YMin) == _r2(bbCoords.YMax)):
                    #
                    #   Object is thin it's plane or line crossing origin
                    #
                    radius1 = -math.sqrt((sf * bbCoords.XMin) ** 2 + (sf * bbCoords.YMin) ** 2)
                    theta1 = math.atan2(bbCoords.YMin, bbCoords.XMin)
                    radius2 = math.sqrt((sf * bbCoords.XMax) ** 2 + (sf * bbCoords.YMax) ** 2)

                    genScript += 'portStart = [{0:g}, {1:g}, {2:g}]\n'.format(_r(radius1), _r(theta1), _r(sf * bbCoords.ZMin))
                    genScript += 'portStop = [{0:g}, {1:g}, {2:g}]\n'.format(_r(radius2), _r(theta1), _r(sf * bbCoords.ZMax))
                    genScript += '\n'
                else:
                    #
                    # origin [0,0,0] is contained inside boundary box, so now must used theta 0-360deg
                    #
                    radius1 = math.sqrt((sf * bbCoords.XMin) ** 2 + (sf * bbCoords.YMin) ** 2)
                    radius2 = math.sqrt((sf * bbCoords.XMax) ** 2 + (sf * bbCoords.YMax) ** 2)

                    genScript += 'portStart = [ 0, -math.pi, {0:g} ]\n'.format(_r(sf * bbCoords.ZMin))
                    genScript += 'portStop  = [ {0:g}, math.pi, {1:g} ]\n'.format(_r(max(radius1, radius2)), _r(sf * bbCoords.ZMax))
                    genScript += '\n'
            else:
                #
                # port is lying outside origin
                #
                genScript += 'portStart = [ {0:g}, {1:g}, {2:g} ]\n'.format(_r(sf * bbCoords.XMin),
                                                                             _r(sf * bbCoords.YMin),
                                                                             _r(sf * bbCoords.ZMin))
                genScript += 'portStop  = [ {0:g}, {1:g}, {2:g} ]\n'.format(_r(sf * bbCoords.XMax),
                                                                             _r(sf * bbCoords.YMax),
                                                                             _r(sf * bbCoords.ZMax))
                genScript += strPortCoordsCartesianToCylindrical

                if (bbCoords.YMin <= 0 and bbCoords.YMax >= 0):
                    #
                    #   special case when planar object lays on X axis like in Y+ and Y- in this case theta is generated:
                    #       -pi for start point
                    #       +pi for stop point
                    #   therefore to correct this since theta is in range -pi..+pi I have to add 360deg so +2*pi for start point will get it right as it should be
                    #
                    genScript += f"portStart[1] += 2*math.pi\n"

        else:
            # CARTESIAN GRID USED
            genScript += 'portStart = [ {0:g}, {1:g}, {2:g} ]\n'.format(_r(sf * bbCoords.XMin),
                                                                         _r(sf * bbCoords.YMin),
                                                                         _r(sf * bbCoords.ZMin))
            genScript += 'portStop  = [ {0:g}, {1:g}, {2:g} ]\n'.format(_r(sf * bbCoords.XMax),
                                                                         _r(sf * bbCoords.YMax),
                                                                         _r(sf * bbCoords.ZMax))

        if (not startPointName is None):
            genScript = genScript.replace("portStart", startPointName)
        if (not stopPointName is None):
            genScript = genScript.replace("portStop", stopPointName)

        return genScript

    def getPortDefinitionsScriptLines(self, items):
        genScript = ""
        if not items:
            return genScript

        refUnit = self.getUnitLengthFromUI_m()  # Coordinates need to be given in drawing units
        sf = self.getFreeCADUnitLength_m() / refUnit  # scaling factor for FreeCAD units to drawing units

        # port index counter, they are generated into port{} cell variable for octave, cells index starts at 1
        genScriptPortCount = 1

        # nf2ff box counter, they are stored inside octave cell variable {} so this is to index them properly, in octave cells index starts at 1
        genNF2FFBoxCounter = 1

        #
        #   This here generates string for port excitation field, ie. for z+ generates [0 0 1], for y- generates [0 -1 0]
        #       Options for select field x,y,z were removed from GUI, but left here due there could be saved files from previous versions
        #       with these options so to keep backward compatibility they are treated as positive direction in that directions.
        #

        #baseVectorStr = {'x': '[1 0 0]', 'y': '[0 1 0]', 'z': '[0 0 1]', 'x+': '[1 0 0]', 'y+': '[0 1 0]', 'z+': '[0 0 1]', 'x-': '[-1 0 0]', 'y-': '[0 -1 0]', 'z-': '[0 0 -1]', 'XY plane, top layer': '[0 0 -1]', 'XY plane, bottom layer': '[0 0 1]', 'XZ plane, front layer': '[0 -1 0]', 'XZ plane, back layer': '[0 1 0]', 'YZ plane, right layer': '[-1 0 0]', 'YZ plane, left layer': '[1 0 0]',}
        #ERROR: followed baseVectorStr is just to generate something but need to take into consideration also sign of propagation direction
        baseVectorStr = {'x': "'x'", 'y': "'y'", 'z': "'z'", 'x+': "'x'", 'y+': "'y'", 'z+': "'z'", 'x-': "'x'", 'y-': "'y'", 'z-': "'z'", 'XY plane, top layer': "'z'", 'XY plane, bottom layer': "'z'", 'XZ plane, front layer': "'y'", 'XZ plane, back layer': "'y'", 'YZ plane, right layer': "'z'", 'YZ plane, left layer': "'x'",}

        mslDirStr = {'x': "'x'", 'y': "'y'", 'z': "'z'", 'x+': "'x'", 'y+': "'y'", 'z+': "'z'", 'x-': "'x'", 'y-': "'y'", 'z-': "'z'",}
        coaxialDirStr = {'x': '0', 'y': '1', 'z': '2', 'x+': '0', 'y+': '1', 'z+': '2', 'x-': '0', 'y-': '1', 'z-': '2',}
        coplanarDirStr = {'x': '0', 'y': '1', 'z': '2', 'x+': '0', 'y+': '1', 'z+': '2', 'x-': '0', 'y-': '1', 'z-': '2',}
        striplineDirStr = {'x': '0', 'y': '1', 'z': '2', 'x+': '0', 'y+': '1', 'z+': '2', 'x-': '0', 'y-': '1', 'z-': '2',}
        probeDirStr = {'x': '0', 'y': '1', 'z': '2', 'x+': '0', 'y+': '1', 'z+': '2', 'x-': '0', 'y-': '1', 'z-': '2',}

        genScript += "#######################################################################################################################################\n"
        genScript += "# PORTS\n"
        genScript += "#######################################################################################################################################\n"
        genScript += "port = {}\n"
        genScript += "portNamesAndNumbersList = {}\n"

        for [item, currSetting] in items:

            print(f"#PORT - {currSetting.getName()} - {currSetting.getType()}")

            objs = self.cadHelpers.getObjects()
            for k in range(item.childCount()):
                childName = item.child(k).text(0)

                genScript += "## PORT - " + currSetting.getName() + " - " + childName + "\n"

                freecadObjects = [i for i in objs if (i.Label) == childName]

                # print(freecadObjects)
                for obj in freecadObjects:
                    # BOUNDING BOX
                    bbCoords = obj.Shape.BoundBox
                    print('\tFreeCAD lumped port BoundBox: ' + str(bbCoords))

                    #
                    #	getting item priority
                    #
                    priorityItemName = item.parent().text(0) + ", " + item.text(0) + ", " + childName
                    priorityIndex = self.getItemPriority(priorityItemName)

                    #
                    # PORT openEMS GENERATION INTO VARIABLE
                    #
                    if (currSetting.getType() == 'lumped'):
                        genScript += self.getCartesianOrCylindricalScriptLinesFromStartStop(bbCoords)

                        if currSetting.infiniteResistance:
                            genScript += 'portR = inf\n'
                        else:
                            genScript += 'portR = ' + str(currSetting.R) + '\n'

                        genScript += 'portUnits = ' + str(currSetting.getRUnits()) + '\n'
                        genScript += "portExcitationAmplitude = " + str(currSetting.excitationAmplitude) + "\n"
                        genScript += 'portDirection = \'' + currSetting.direction + '\'\n'

                        genScript += 'port[' + str(genScriptPortCount) + '] = FDTD.AddLumpedPort(' + \
                                     'port_nr=' + str(genScriptPortCount) + ', ' + \
                                     'R=portR*portUnits, start=portStart, stop=portStop, p_dir=portDirection, ' + \
                                     'priority=' + str(priorityIndex) + ', ' + \
                                     'excite=' + ('1.0*portExcitationAmplitude' if currSetting.isActive else '0') + ')\n'

                        internalPortName = currSetting.name + " - " + obj.Label
                        self.internalPortIndexNamesList[internalPortName] = genScriptPortCount
                        genScript += f'portNamesAndNumbersList["{obj.Label}"] = {genScriptPortCount};\n'
                        genScriptPortCount += 1

                    #
                    #   ERROR - BELOW STILL NOT REWRITTEN INTO PYTHON!!!
                    #

                    elif (currSetting.getType() == 'microstrip'):
                        portStartX, portStartY, portStartZ, portStopX, portStopY, portStopZ = currSetting.getMicrostripStartStopCoords(bbCoords, sf)
                        bbCoords.Xmin = portStartX
                        bbCoords.Ymin = portStartY
                        bbCoords.Zmin = portStartZ
                        bbCoords.Xmax = portStopX
                        bbCoords.Ymax = portStopY
                        bbCoords.Zmax = portStopZ
                        genScript += self.getCartesianOrCylindricalScriptLinesFromStartStop(bbCoords)

                        if currSetting.infiniteResistance:
                            genScript += 'portR = inf\n'
                        else:
                            genScript += 'portR = ' + str(currSetting.R) + '\n'

                        genScript += 'portUnits = ' + str(currSetting.getRUnits()) + '\n'

                        #
                        #   if currSetting.isActive == False then excitation is 0
                        #
                        genScript += f"portExcitationAmplitude = {str(currSetting.excitationAmplitude)} * {'1' if currSetting.isActive else '0'}\n"

                        genScript += 'mslDir = {}\n'.format(mslDirStr.get(currSetting.mslPropagation[0], '?')) #use just first letter of propagation direction
                        genScript += 'mslEVec = {}\n'.format(baseVectorStr.get(currSetting.direction, '?'))

                        feedShiftStr = {False: "", True: ", FeedShift=" + str(_r(currSetting.mslFeedShiftValue / self.getUnitLengthFromUI_m() * currSetting.getUnitsAsNumber(currSetting.mslFeedShiftUnits)))}
                        measPlaneStr = {False: "", True: ", MeasPlaneShift=" + str(_r(currSetting.mslMeasPlaneShiftValue / self.getUnitLengthFromUI_m() * currSetting.getUnitsAsNumber(currSetting.mslMeasPlaneShiftUnits)))}

                        isActiveMSLStr = {False: "", True: ", 'ExcitePort', true"}

                        genScript_R = ", 'Feed_R', portR*portUnits"

                        genScript += f'port[{str(genScriptPortCount)}] = FDTD.AddMSLPort(' + \
                                         f'{str(genScriptPortCount)}, ' + \
                                         f"{self.internalMaterialIndexNamesList[currSetting.mslMaterial]}, " + \
                                         f'portStart, ' + \
                                         f'portStop, ' + \
                                         f'mslDir, ' + \
                                         f'mslEVec, ' + \
                                         f"excite=portExcitationAmplitude, " + \
                                         f'priority={str(priorityIndex)}, ' + \
                                         f'Feed_R=portR*portUnits' + \
                                         feedShiftStr.get(True) + \
                                         measPlaneStr.get(True) + \
                                   f")\n"

                        internalPortName = currSetting.name + " - " + obj.Label
                        self.internalPortIndexNamesList[internalPortName] = genScriptPortCount
                        genScript += f'portNamesAndNumbersList["{obj.Label}"] = {genScriptPortCount};\n'
                        genScriptPortCount += 1

                    elif (currSetting.getType() == 'circular waveguide'):
                        #
                        #   NOV 2023 - PYTHON API NOT IMPLEMENTED
                        #
                        genScript += "%% circular port openEMS code should be here, NOT IMPLEMENTED python API for it\n"

                    elif (currSetting.getType() == 'rectangular waveguide'):
                        portStartX, portStartY, portStartZ, portStopX, portStopY, portStopZ, waveguideWidth, waveguideHeight = currSetting.getRectangularWaveguideStartStopWidthHeight(bbCoords, sf)
                        bbCoords.Xmin = portStartX
                        bbCoords.Ymin = portStartY
                        bbCoords.Zmin = portStartZ
                        bbCoords.Xmax = portStopX
                        bbCoords.Ymax = portStopY
                        bbCoords.Zmax = portStopZ
                        genScript += self.getCartesianOrCylindricalScriptLinesFromStartStop(bbCoords)

                        genScript += f"portExcitationAmplitude = {str(currSetting.excitationAmplitude)} * {'1' if currSetting.isActive else '0'}\n"

                        genScript += f'port[{str(genScriptPortCount)}] = FDTD.AddRectWaveGuidePort(' + \
                                     f'{str(genScriptPortCount)}, ' + \
                                     f'portStart, ' + \
                                     f'portStop, ' + \
                                     f'"{currSetting.waveguideRectDir[0]}", ' + \
                                     f'{waveguideWidth}, ' + \
                                     f'{waveguideHeight}, ' + \
                                     f'"{currSetting.modeName}", ' + \
                                     f"excite=portExcitationAmplitude, " + \
                                     f'priority={str(priorityIndex)}, ' + \
                                     f")\n"

                        internalPortName = currSetting.name + " - " + obj.Label
                        self.internalPortIndexNamesList[internalPortName] = genScriptPortCount
                        genScript += f'portNamesAndNumbersList["{obj.Label}"] = {genScriptPortCount};\n'
                        genScriptPortCount += 1
                    elif (currSetting.getType() == 'coaxial'):
                        #
                        #   NOV 2023 - PYTHON API NOT IMPLEMENTED
                        #
                        genScript += '# ERROR: caoxial port function NOT IMPLEMENTED IN openEMS PYTHON INTERFACE\n'
                        genScript += '# raise BaseException("caoxial port function NOT IMPLEMENTED IN openEMS PYTHON INTERFACE coaxial port")\n'

                    elif (currSetting.getType() == 'coplanar'):
                        #
                        #   NOV 2023 - PYTHON API NOT IMPLEMENTED
                        #
                        genScript += '# ERROR: coplanar port function NOT IMPLEMENTED IN openEMS PYTHON INTERFACE\n'
                        genScript += 'raise BaseException("coplanar port function NOT IMPLEMENTED IN openEMS PYTHON INTERFACE")\n'

                    elif (currSetting.getType() == 'stripline'):
                        #
                        #   NOV 2023 - PYTHON API NOT IMPLEMENTED
                        #
                        genScript += '# ERROR: stripline port function NOT IMPLEMENTED IN openEMS PYTHON INTERFACE\n'
                        genScript += 'raise BaseException("stripline port function NOT IMPLEMENTED IN openEMS PYTHON INTERFACE")\n'

                    elif (currSetting.getType() == 'curve'):
                        genScript += '# ERROR: curve port function NOT IMPLEMENTED IN openEMS PYTHON INTERFACE\n'
                        genScript += 'raise BaseException("curve port function NOT IMPLEMENTED IN openEMS PYTHON INTERFACE")\n'

                    else:
                        genScript += '# Unknown port type. Nothing was generated.\n'
                        genScript += 'raise BaseException("Unknown port type. Nothing was generated.")\n'

            genScript += "\n"

        return genScript

    def getProbeDefinitionsScriptLines(self, items):
        genScript = ""
        if not items:
            return genScript

        refUnit = self.getUnitLengthFromUI_m()  # Coordinates need to be given in drawing units
        sf = self.getFreeCADUnitLength_m() / refUnit  # scaling factor for FreeCAD units to drawing units

        # counters for indexing generated python code variables containing list of generated object by their type
        genProbeCounter = 1
        genDumpBoxCounter = 1

        # nf2ff box counter, they are stored inside octave cell variable nf2ff{} so this is to index them properly, in octave cells index starts at 1
        genNF2FFBoxCounter = 1

        #
        #   This here generates string for port excitation field, ie. for z+ generates [0 0 1], for y- generates [0 -1 0]
        #       Options for select field x,y,z were removed from GUI, but left here due there could be saved files from previous versions
        #       with these options so to keep backward compatibility they are treated as positive direction in that directions.
        #
        baseVectorStr = {'x': '0', 'y': '1', 'z': '2', 'x+': '0', 'y+': '1', 'z+': '2', 'x-': '0', 'y-': '1', 'z-': '2', 'XY plane, top layer': '2', 'XY plane, bottom layer': '2', 'XZ plane, front layer': '1', 'XZ plane, back layer': '1', 'YZ plane, right layer': '0', 'YZ plane, left layer': '0',}
        probeDirStr = {'x': '0', 'y': '1', 'z': '2', 'x+': '0', 'y+': '1', 'z+': '2', 'x-': '0', 'y-': '1', 'z-': '2',}

        genScript += "#######################################################################################################################################\n"
        genScript += "# PROBES\n"
        genScript += "#######################################################################################################################################\n"
        genScript += "nf2ffBoxList = {}\n"
        genScript += "dumpBoxList = {}\n"
        genScript += "probeList = {}\n"
        genScript += "\n"

        for [item, currSetting] in items:

            print(f"#PROBE - {currSetting.getName()} - {currSetting.getType()}")

            objs = self.cadHelpers.getObjects()
            for k in range(item.childCount()):
                childName = item.child(k).text(0)

                genScript += "# PROBE - " + currSetting.getName() + " - " + childName + "\n"

                freecadObjects = [i for i in objs if (i.Label) == childName]

                # print(freecadObjects)
                for obj in freecadObjects:
                    print(f"\t{obj.Label}")
                    # BOUNDING BOX
                    bbCoords = obj.Shape.BoundBox
                    print(f"\t\t{bbCoords}")

                    #
                    # PROBE openEMS GENERATION INTO VARIABLE
                    #
                    if (currSetting.getType() == "probe"):
                        probeName = f"{currSetting.name}_{childName}"
                        genScript += f'probeName = "{probeName}"\n'

                        genScript += 'probeDirection = {}\n'.format(baseVectorStr.get(currSetting.direction, '?'))

                        if currSetting.probeType == "voltage":
                            genScript += 'probeType = 0\n'
                        elif currSetting.probeType == "current":
                            genScript += 'probeType = 1\n'
                        elif currSetting.probeType == "E field":
                            genScript += 'probeType = 2\n'
                        elif currSetting.probeType == "H field":
                            genScript += 'probeType = 3\n'
                        else:
                            genScript += 'probeType = ?    #ERROR probe code generate don\'t know type\n'

                        argStr = ""
                        if not (bbCoords.XMin == bbCoords.XMax or bbCoords.YMin == bbCoords.YMax or bbCoords.ZMin == bbCoords.ZMax):
                            argStr += f", norm_dir=probeDirection"

                        if (currSetting.probeDomain == "frequency"):
                            argStr += f", frequency=["

                            if (len(currSetting.probeFrequencyList) > 0):
                                for freqStr in currSetting.probeFrequencyList:
                                    freqStr = freqStr.strip()
                                    result = re.search(r"([+,\,\-,.,0-9]+)([A-Za-z]+)$", freqStr)
                                    if result:
                                        freqValue = float(result.group(1))
                                        freqUnits = result.group(2)
                                        freqValue = freqValue * currSetting.getUnitsAsNumber(freqUnits)
                                        argStr += str(freqValue) + ","
                                argStr += "]"
                            else:
                                argStr += "f0]#{ERROR NO FREQUENCIES FOR PROBE FOUND, SO INSTEAD USED f0#}"
                                self.cadHelpers.printWarning(f"probe octave code generator error, no frequencies defined for '{probeName}', using f0 instead\n")

                        genScript += f"probeList[probeName] = CSX.AddProbe(probeName, probeType" + argStr + ")\n"
                        genScript += self.getCartesianOrCylindricalScriptLinesFromStartStop(bbCoords, "probeStart", "probeStop")
                        genScript += f"probeList[probeName].AddBox(probeStart, probeStop )\n"
                        genScript += "\n"
                        genProbeCounter += 1

                    elif (currSetting.getType() == "dumpbox"):
                        dumpboxName = f"{currSetting.name}_{childName}"
                        genScript += f'dumpboxName = "{dumpboxName}"\n'

                        dumpType = currSetting.getDumpType()
                        genScript += f'dumpboxType = {dumpType}\n'

                        argStr = ""
                        #
                        #   dump file type:
                        #       0 = vtk (default)
                        #       1 = hdf5
                        #
                        if (currSetting.dumpboxFileType == "hdf5"):
                            argStr += f", file_type=1"

                        emptyFrequencyListError = False
                        if (currSetting.dumpboxDomain == "frequency"):
                            argStr += ", frequency=["

                            if (len(currSetting.dumpboxFrequencyList) > 0):
                                for freqStr in currSetting.dumpboxFrequencyList:
                                    freqStr = freqStr.strip()
                                    result = re.search(r"([+,\,\-,.,0-9]+)([A-Za-z]+)$", freqStr)
                                    if result:
                                        freqValue = float(result.group(1))
                                        freqUnits = result.group(2)
                                        freqValue = freqValue * currSetting.getUnitsAsNumber(freqUnits)
                                        argStr += str(freqValue) + ","
                                argStr += "]"
                            else:
                                emptyFrequencyListError = True
                                argStr += "f0]"
                                self.cadHelpers.printWarning(f"dumpbox octave code generator error, no frequencies defined for '{dumpboxName}', using f0 instead\n")

                        #if error put note about it into script
                        if emptyFrequencyListError:
                            genScript += f"dumpBoxList[dumpboxName] = CSX.AddDump(dumpboxName, dump_type=dumpboxType" + argStr + ") # ERROR script generation no frequencies for dumpbox, therefore using f0\n"
                        else:
                            genScript += f"dumpBoxList[dumpboxName] = CSX.AddDump(dumpboxName, dump_type=dumpboxType" + argStr + ")\n"

                        genScript += self.getCartesianOrCylindricalScriptLinesFromStartStop(bbCoords, "dumpboxStart", "dumpboxStop")
                        genScript += f"dumpBoxList[dumpboxName].AddBox(dumpboxStart, dumpboxStop )\n"
                        genScript += "\n"
                        genDumpBoxCounter += 1

                    elif (currSetting.getType() == 'et dump'):
                        dumpboxName = f"{currSetting.name}_{childName}"
                        genScript += f'dumpboxName = "{dumpboxName}"\n'

                        genScript += f"dumpBoxList[dumpboxName] = CSX.AddDump(dumpboxName, dump_type=0, dump_mode=2)\n"
                        genScript += self.getCartesianOrCylindricalScriptLinesFromStartStop(bbCoords, "dumpboxStart", "dumpboxStop")
                        genScript += f"dumpBoxList[dumpboxName].AddBox(dumpboxStart, dumpboxStop)\n"
                        genDumpBoxCounter += 1

                    elif (currSetting.getType() == 'ht dump'):
                        dumpboxName = f"{currSetting.name}_{childName}"
                        genScript += f'dumpboxName = "{dumpboxName}"\n'

                        genScript += f"dumpBoxList[dumpboxName] = CSX.AddDump(dumpboxName, dumnp_type=1, dump_mode=2)\n"
                        genScript += self.getCartesianOrCylindricalScriptLinesFromStartStop(bbCoords, "dumpboxStart", "dumpboxStop")
                        genScript += f"dumpBoxList[dumpboxName].AddBox(dumpboxStart, dumpboxStop );\n"
                        genDumpBoxCounter += 1

                    elif (currSetting.getType() == 'nf2ff box'):
                        dumpboxName = f"{currSetting.name} - {childName}"
                        dumpboxName = dumpboxName.replace(" ", "_")
                        genScript += f'dumpboxName = "{dumpboxName}"\n'

                        genScript += self.getCartesianOrCylindricalScriptLinesFromStartStop(bbCoords, "nf2ffStart", "nf2ffStop")

                        # genScript += 'nf2ffUnit = ' + currSetting.getUnitAsScriptLine() + ';\n'
                        genScript += f"nf2ffBoxList[dumpboxName] = FDTD.CreateNF2FFBox(dumpboxName, nf2ffStart, nf2ffStop)\n"
                        # NF2FF grid lines are generated below via getNF2FFDefinitionsScriptLines()

                        #
                        #   ATTENTION this is NF2FF box counter
                        #
                        self.internalNF2FFIndexNamesList[dumpboxName] = genNF2FFBoxCounter
                        genNF2FFBoxCounter += 1

                    else:
                        genScript += '# Unknown port type. Nothing was generated. \n'

            genScript += "\n"

        return genScript

    def getLumpedPartDefinitionsScriptLines(self, items):
        genScript = ""
        if not items:
            return genScript

        refUnit = self.getUnitLengthFromUI_m()  # Coordinates need to be given in drawing units
        sf = self.getFreeCADUnitLength_m() / refUnit  # scaling factor for FreeCAD units to drawing units

        genScript += "#######################################################################################################################################\n"
        genScript += "# LUMPED PART\n"
        genScript += "#######################################################################################################################################\n"

        for [item, currentSetting] in items:
            genScript += "# LUMPED PARTS " + currentSetting.getName() + "\n"

            # traverse through all children item for this particular lumped part settings
            objs = self.cadHelpers.getObjects()
            objsExport = []
            for k in range(item.childCount()):
                childName = item.child(k).text(0)
                print("#LUMPED PART " + currentSetting.getType())

                freecadObjects = [i for i in objs if (i.Label) == childName]
                for obj in freecadObjects:
                    # obj = FreeCAD Object class

                    # BOUNDING BOX
                    bbCoords = obj.Shape.BoundBox

                    genScript += self.getCartesianOrCylindricalScriptLinesFromStartStop(bbCoords, "lumpedPartStart", "lumpedPartStop")

                    lumpedPartParams = f"'{currentSetting.name}'"
                    lumpedPartParams += f", ny='{currentSetting.getDirection()}'"

                    if ('r' in currentSetting.getType().lower()):
                        lumpedPartParams += f", R={currentSetting.getR()}"
                    if ('l' in currentSetting.getType().lower()):
                        lumpedPartParams += f", L={currentSetting.getL()}"
                    if ('c' in currentSetting.getType().lower()):
                        lumpedPartParams += f", C={currentSetting.getC()}"

                    lumpedPartParams += f", caps={'True' if currentSetting.getCapsEnabled() else 'False'}"

                    #
                    #   WARNING: This was added just recently needs to be validated.
                    #
                    if (currentSetting.getCombinationType() == 'parallel'):
                        lumpedPartParams += f", LEtype=0"
                    elif (currentSetting.getCombinationType() == 'series'):
                        lumpedPartParams += f", LEtype=1"
                    else:
                        pass

                    #
                    #	getting item priority
                    #
                    priorityItemName = item.parent().text(0) + ", " + item.text(0) + ", " + childName
                    priorityIndex = self.getItemPriority(priorityItemName)

                    # WARNING: Caps param has hardwired value 1, will be generated small metal caps to connect part with circuit !!!
                    genScript += f"lumpedPart = CSX.AddLumpedElement({lumpedPartParams});\n"
                    genScript += f"lumpedPart.AddBox(lumpedPartStart, lumpedPartStop, priority={priorityIndex});\n"

            genScript += "\n"

        return genScript

    def getNF2FFDefinitionsScriptLines(self, items):
        genScript = ""
        if not items:
            return genScript

        refUnit = self.getUnitLengthFromUI_m()  # Coordinates need to be given in drawing units
        sf = self.getFreeCADUnitLength_m() / refUnit  # scaling factor for FreeCAD units to drawing units
        nf2ff_gridlines = {'x': [], 'y': [], 'z': []}

        for [item, currSetting] in items:

            objs = self.cadHelpers.getObjects()
            for k in range(item.childCount()):
                childName = item.child(k).text(0)

                freecadObjects = [i for i in objs if (i.Label) == childName]

                # print(freecadObjects)
                for obj in freecadObjects:
                    # BOUNDING BOX
                    bbCoords = obj.Shape.BoundBox

                    if (currSetting.getType() == 'nf2ff box'):
                        nf2ff_gridlines['x'].append("{0:g}".format(_r(sf * bbCoords.XMin)))
                        nf2ff_gridlines['x'].append("{0:g}".format(_r(sf * bbCoords.XMax)))
                        nf2ff_gridlines['y'].append("{0:g}".format(_r(sf * bbCoords.YMin)))
                        nf2ff_gridlines['y'].append("{0:g}".format(_r(sf * bbCoords.YMax)))
                        nf2ff_gridlines['z'].append("{0:g}".format(_r(sf * bbCoords.ZMin)))
                        nf2ff_gridlines['z'].append("{0:g}".format(_r(sf * bbCoords.ZMax)))

        writeNF2FFlines = (len(nf2ff_gridlines['x']) > 0) or (len(nf2ff_gridlines['y']) > 0) or (
                    len(nf2ff_gridlines['z']) > 0)

        if writeNF2FFlines:
            genScript += "#######################################################################################################################################\n"
            genScript += "# NF2FF PROBES GRIDLINES\n"
            genScript += "#######################################################################################################################################\n"

            genScript += "mesh.x = np.array([])\n"
            genScript += "mesh.y = np.array([])\n"
            genScript += "mesh.z = np.array([])\n"

            if (len(nf2ff_gridlines['x']) > 0):
                genScript += "mesh.x = np.append(mesh.x, [" + ", ".join(str(i) for i in nf2ff_gridlines['x']) + "])\n"
            if (len(nf2ff_gridlines['y']) > 0):
                genScript += "mesh.y = np.append(mesh.y, [" + ", ".join(str(i) for i in nf2ff_gridlines['y']) + "])\n"
            if (len(nf2ff_gridlines['z']) > 0):
                genScript += "mesh.z = np.append(mesh.z, [" + ", ".join(str(i) for i in nf2ff_gridlines['z']) + "])\n"

            genScript += "openEMS_grid.AddLine('x', mesh.x)\n"
            genScript += "openEMS_grid.AddLine('y', mesh.y)\n"
            genScript += "openEMS_grid.AddLine('z', mesh.z)\n"
            genScript += "\n"

        return genScript

    def getOrderedGridDefinitionsScriptLines(self, items):
        genScript = ""
        meshPrioritiesCount = self.form.meshPriorityTreeView.topLevelItemCount()

        if (not items) or (meshPrioritiesCount == 0):
            return genScript

        refUnit = self.getUnitLengthFromUI_m()  # Coordinates need to be given in drawing units
        refUnitStr = self.form.simParamsDeltaUnitList.currentText()
        sf = self.getFreeCADUnitLength_m() / refUnit  # scaling factor for FreeCAD units to drawing units

        genScript += "#######################################################################################################################################\n"
        genScript += "# GRID LINES\n"
        genScript += "#######################################################################################################################################\n"
        genScript += "\n"

        # Create lists and dict to be able to resolve ordered list of (grid settings instance <-> FreeCAD object) associations.
        # In its current form, this implies user-defined grid lines have to be associated with the simulation volume.
        _assoc = lambda idx: list(map(str.strip, self.form.meshPriorityTreeView.topLevelItem(idx).text(0).split(',')))
        orderedAssociations = [_assoc(k) for k in reversed(range(meshPrioritiesCount))]
        gridSettingsNodeNames = [gridSettingsNode.text(0) for [gridSettingsNode, gridSettingsInst] in items]
        fcObjects = {obj.Label: obj for obj in self.cadHelpers.getObjects()}

        for gridSettingsNodeName in gridSettingsNodeNames:
            print("Grid type : " + gridSettingsNodeName)

        for k, [categoryName, gridName, FreeCADObjectName] in enumerate(orderedAssociations):

            print("Grid priority level {} : {} :: {}".format(k, FreeCADObjectName, gridName))

            if not (gridName in gridSettingsNodeNames):
                print("Failed to resolve '{}'.".format(gridName))
                continue
            itemListIdx = gridSettingsNodeNames.index(gridName)

            #GridSettingsItem object from GUI
            gridSettingsInst = items[itemListIdx][1]

            #Grid category object from GUI
            gridCategoryObj = items[itemListIdx][0]

            #
            #   Fixed Distance, Fixed Count mesh boundaries coords obtain
            #
            if (gridSettingsInst.getType() in ['Fixed Distance', 'Fixed Count', 'User Defined']):
                fcObject = fcObjects.get(FreeCADObjectName, None)
                if (not fcObject):
                    print("Failed to resolve '{}'.".format(FreeCADObjectName))
                    continue

                ### Produce script output.

                if (not "Shape" in dir(fcObject)):
                    continue

                bbCoords = fcObject.Shape.BoundBox

                deltaX = 0
                deltaY = 0
                deltaZ = 0
                if gridSettingsInst.generateLinesInside:
                    gridOffset = gridSettingsInst.getGridOffset()
                    unitsAsNumber = gridSettingsInst.getUnitsAsNumber(gridOffset['units'])
                    deltaX = gridOffset['x'] * unitsAsNumber
                    deltaY = gridOffset['y'] * unitsAsNumber
                    deltaZ = gridOffset['z'] * unitsAsNumber
                    print(f"GRID generateLinesInside object detected, delta in X,Y,Z: {deltaX}, {deltaY}, {deltaZ}")

                xmax = sf * bbCoords.XMax - np.sign(bbCoords.XMax - bbCoords.XMin) * deltaX
                ymax = sf * bbCoords.YMax - np.sign(bbCoords.YMax - bbCoords.YMin) * deltaY
                zmax = sf * bbCoords.ZMax - np.sign(bbCoords.ZMax - bbCoords.ZMin) * deltaZ
                xmin = sf * bbCoords.XMin + np.sign(bbCoords.XMax - bbCoords.XMin) * deltaX
                ymin = sf * bbCoords.YMin + np.sign(bbCoords.YMax - bbCoords.YMin) * deltaY
                zmin = sf * bbCoords.ZMin + np.sign(bbCoords.ZMax - bbCoords.ZMin) * deltaZ

                # Write grid definition.
                genScript += "## GRID - " + gridSettingsInst.getName() + " - " + FreeCADObjectName + ' (' + gridSettingsInst.getType() + ")\n"

            #
            #   Smooth Mesh boundaries coords obtain
            #
            elif (gridSettingsInst.getType() == "Smooth Mesh"):

                xList = []
                yList = []
                zList = []

                #iterate over grid smooth mesh category freecad children
                for k in range(gridCategoryObj.childCount()):
                    FreeCADObjectName = gridCategoryObj.child(k).text(0)

                    fcObject = fcObjects.get(FreeCADObjectName, None)
                    if (not fcObject):
                        print("Smooth Mesh - Failed to resolve '{}'.".format(FreeCADObjectName))
                        continue

                    ### Produce script output.

                    if (not "Shape" in dir(fcObject)):
                        continue

                    bbCoords = fcObject.Shape.BoundBox

                    deltaX = 0
                    deltaY = 0
                    deltaZ = 0
                    if gridSettingsInst.generateLinesInside:
                        gridOffset = gridSettingsInst.getGridOffset()
                        unitsAsNumber = gridSettingsInst.getUnitsAsNumber(gridOffset['units'])
                        deltaX = gridOffset['x'] * unitsAsNumber
                        deltaY = gridOffset['y'] * unitsAsNumber
                        deltaZ = gridOffset['z'] * unitsAsNumber
                        print(f"GRID generateLinesInside object detected, delta in X,Y,Z: {deltaX}, {deltaY}, {deltaZ}")

                    #append boundary coordinates into list
                    xList.append(sf * bbCoords.XMax - np.sign(bbCoords.XMax - bbCoords.XMin) * deltaX)
                    yList.append(sf * bbCoords.YMax - np.sign(bbCoords.YMax - bbCoords.YMin) * deltaY)
                    zList.append(sf * bbCoords.ZMax - np.sign(bbCoords.ZMax - bbCoords.ZMin) * deltaZ)
                    xList.append(sf * bbCoords.XMin + np.sign(bbCoords.XMax - bbCoords.XMin) * deltaX)
                    yList.append(sf * bbCoords.YMin + np.sign(bbCoords.YMax - bbCoords.YMin) * deltaY)
                    zList.append(sf * bbCoords.ZMin + np.sign(bbCoords.ZMax - bbCoords.ZMin) * deltaZ)

                    # Write grid definition.
                    genScript += "## GRID - " + gridSettingsInst.getName() + " - " + FreeCADObjectName + ' (' + gridSettingsInst.getType() + ")\n"

                #order from min -> max coordinates in each list
                xList.sort()
                yList.sort()
                zList.sort()

            #
            #   Real octave mesh lines code generate starts here
            #

            #in case of cylindrical coordinates convert xyz to theta,r,z
            if (gridSettingsInst.coordsType == "cylindrical"):
                #FROM GUI ARE GOING DEGREES

                #
                #   Here calculate right r, theta, z from boundaries of object, it depends if origin lays inside boundaries or where object is positioned.
                #
                xmin, xmax, ymin, ymax, zmin, zmax = gridSettingsInst.getCartesianAsCylindricalCoords(bbCoords, xmin, xmax, ymin, ymax, zmin, zmax)

                if (gridSettingsInst.getType() == 'Smooth Mesh' and gridSettingsInst.unitsAngle == "deg"):
                    yParam = math.radians(gridSettingsInst.smoothMesh['yMaxRes'])
                elif (gridSettingsInst.getType() == 'Fixed Distance' and gridSettingsInst.unitsAngle == "deg"):
                    yParam = math.radians(gridSettingsInst.getXYZ(refUnit)['y'])
                elif (gridSettingsInst.getType() == 'User Defined'):
                    pass  # user defined is jaust text, doesn't have ['y']
                else:
                    yParam = gridSettingsInst.getXYZ(refUnit)['y']

                #z coordinate stays as was

            else:
                if (gridSettingsInst.getType() == 'Smooth Mesh'):
                    yParam = gridSettingsInst.smoothMesh['yMaxRes']
                elif (gridSettingsInst.getType() == 'User Defined'):
                    pass                                                #user defined is just text, doesn't have ['y']
                else:
                    yParam = gridSettingsInst.getXYZ(refUnit)['y']

            if (gridSettingsInst.getType() == 'Fixed Distance'):
                if gridSettingsInst.xenabled:
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.x = np.delete(mesh.x, np.argwhere((mesh.x >= {0:g}) & (mesh.x <= {1:g})))\n".format(_r(xmin), _r(xmax))
                    genScript += "mesh.x = np.concatenate((mesh.x, arangeWithEndpoint({0:g},{1:g},{2:g})))\n".format(_r(xmin), _r(xmax), _r(gridSettingsInst.getXYZ(refUnit)['x']))
                if gridSettingsInst.yenabled:
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.y = np.delete(mesh.y, np.argwhere((mesh.y >= {0:g}) & (mesh.y <= {1:g})))\n".format(_r(ymin), _r(ymax))
                    genScript += "mesh.y = np.concatenate((mesh.y, arangeWithEndpoint({0:g},{1:g},{2:g})))\n".format(_r(ymin),_r(ymax),_r(yParam))
                if gridSettingsInst.zenabled:
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.z = np.delete(mesh.z, np.argwhere((mesh.z >= {0:g}) & (mesh.z <= {1:g})))\n".format(_r(zmin), _r(zmax))
                    genScript += "mesh.z = np.concatenate((mesh.z, arangeWithEndpoint({0:g},{1:g},{2:g})))\n".format(_r(zmin),_r(zmax),_r(gridSettingsInst.getXYZ(refUnit)['z']))

            elif (gridSettingsInst.getType() == 'Fixed Count'):
                if gridSettingsInst.xenabled:
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.x = np.delete(mesh.x, np.argwhere((mesh.x >= {0:g}) & (mesh.x <= {1:g})))\n".format(_r(xmin), _r(xmax))
                    if (not gridSettingsInst.getXYZ()['x'] == 1):
                        genScript += "mesh.x = np.concatenate((mesh.x, linspace({0:g},{1:g},{2:g})))\n".format(_r(xmin), _r(xmax), _r(gridSettingsInst.getXYZ(refUnit)['x']))
                    else:
                        genScript += "mesh.x = np.append(mesh.x, {0:g})\n".format(_r((xmin + xmax) / 2))

                if gridSettingsInst.yenabled:
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.y = np.delete(mesh.y, np.argwhere((mesh.y >= {0:g}) & (mesh.y <= {1:g})))\n".format(_r(ymin), _r(ymax))
                    if (not gridSettingsInst.getXYZ()['y'] == 1):
                        genScript += "mesh.y = np.concatenate((mesh.y, linspace({0:g},{1:g},{2:g})))\n".format(_r(ymin), _r(ymax), _r(yParam))
                    else:
                        genScript += "mesh.y = np.append(mesh.y, {0:g})\n".format(_r((ymin + ymax) / 2))

                if gridSettingsInst.zenabled:
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.z = np.delete(mesh.z, np.argwhere((mesh.z >= {0:g}) & (mesh.z <= {1:g})))\n".format(_r(zmin), _r(zmax))
                    if (not gridSettingsInst.getXYZ()['z'] == 1):
                        genScript += "mesh.z = np.concatenate((mesh.z, linspace({0:g},{1:g},{2:g})))\n".format(_r(zmin), _r(zmax), _r(gridSettingsInst.getXYZ(refUnit)['z']))
                    else:
                        genScript += "mesh.z = np.append(mesh.z, {0:g})\n".format(_r((zmin + zmax) / 2))

            elif (gridSettingsInst.getType() == 'User Defined'):
                if gridSettingsInst.xenabled:
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.x = np.delete(mesh.x, np.argwhere((mesh.x >= {0:g}) & (mesh.x <= {1:g})))\n".format(_r(xmin), _r(xmax))
                if gridSettingsInst.yenabled:
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.y = np.delete(mesh.y, np.argwhere((mesh.y >= {0:g}) & (mesh.y <= {1:g})))\n".format(_r(ymin), _r(ymax))
                if gridSettingsInst.zenabled:
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.z = np.delete(mesh.z, np.argwhere((mesh.z >= {0:g}) & (mesh.z <= {1:g})))\n".format(_r(zmin), _r(zmax))

                genScript += "xmin = {0:g}\n".format(_r(xmin))
                genScript += "xmax = {0:g}\n".format(_r(xmax))
                genScript += "ymin = {0:g}\n".format(_r(ymin))
                genScript += "ymax = {0:g}\n".format(_r(ymax))
                genScript += "zmin = {0:g}\n".format(_r(zmin))
                genScript += "zmax = {0:g}\n".format(_r(zmax))
                genScript += gridSettingsInst.getXYZ() + "\n"

            elif (gridSettingsInst.getType() == 'Smooth Mesh'):
                genScript += "smoothMesh = {}\n"
                if gridSettingsInst.xenabled:

                    #when top priority lines setting set, remove lines between min and max in ax direction
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.x = np.delete(mesh.x, np.argwhere((mesh.x >= {0:g}) & (mesh.x <= {1:g})))\n".format(_r(xList[0]), _r(xList[-1]))

                    genScript += f"smoothMesh.x = {str(xList)};\n"
                    if gridSettingsInst.smoothMesh['xMaxRes'] == 0:
                        genScript += "smoothMesh.x = CSXCAD.SmoothMeshLines.SmoothMeshLines(smoothMesh.x, max_res/unit) #max_res calculated in excitation part\n"
                    else:
                        genScript += f"smoothMesh.x = CSXCAD.SmoothMeshLines.SmoothMeshLines(smoothMesh.x, {gridSettingsInst.smoothMesh['xMaxRes']})\n"
                    genScript += "mesh.x = np.concatenate((mesh.x, smoothMesh.x))\n"
                if gridSettingsInst.yenabled:

                    #when top priority lines setting set, remove lines between min and max in ax direction
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.y = np.delete(mesh.y, np.argwhere((mesh.y >= {0:g}) & (mesh.y <= {1:g})))\n".format(_r(yList[0]), _r(yList[-1]))

                    genScript += f"smoothMesh.y = {str(yList)};\n"
                    if gridSettingsInst.smoothMesh['yMaxRes'] == 0:
                        genScript += "smoothMesh.y = CSXCAD.SmoothMeshLines.SmoothMeshLines(smoothMesh.y, max_res/unit) #max_res calculated in excitation part\n"
                    else:
                        genScript += f"smoothMesh.y = CSXCAD.SmoothMeshLines.SmoothMeshLines(smoothMesh.y, {yParam})\n"
                    genScript += "mesh.y = np.concatenate((mesh.y, smoothMesh.y))\n"
                if gridSettingsInst.zenabled:

                    #when top priority lines setting set, remove lines between min and max in ax direction
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.z = np.delete(mesh.z, np.argwhere((mesh.z >= {0:g}) & (mesh.z <= {1:g})))\n".format(_r(zList[0]), _r(zList[-1]))

                    genScript += f"smoothMesh.z = {str(zList)};\n"
                    if gridSettingsInst.smoothMesh['zMaxRes'] == 0:
                        genScript += "smoothMesh.z = CSXCAD.SmoothMeshLines.SmoothMeshLines(smoothMesh.z, max_res/unit) #max_res calculated in excitation part\n"
                    else:
                        genScript += f"smoothMesh.z = CSXCAD.SmoothMeshLines.SmoothMeshLines(smoothMesh.z, {gridSettingsInst.smoothMesh['zMaxRes']})\n"
                    genScript += "mesh.z = np.concatenate((mesh.z, smoothMesh.z))\n"

            genScript += "\n"

        genScript += "openEMS_grid.AddLine('x', mesh.x)\n"
        genScript += "openEMS_grid.AddLine('y', mesh.y)\n"
        genScript += "openEMS_grid.AddLine('z', mesh.z)\n"
        genScript += "\n"

        return genScript

    def getOrderedGridDefinitionsScriptLines_old_01(self, items):
        genScript = ""
        meshPrioritiesCount = self.form.meshPriorityTreeView.topLevelItemCount()

        if (not items) or (meshPrioritiesCount == 0):
            return genScript

        refUnit = self.getUnitLengthFromUI_m()  # Coordinates need to be given in drawing units
        refUnitStr = self.form.simParamsDeltaUnitList.currentText()
        sf = self.getFreeCADUnitLength_m() / refUnit  # scaling factor for FreeCAD units to drawing units

        genScript += "#######################################################################################################################################\n"
        genScript += "# GRID LINES\n"
        genScript += "#######################################################################################################################################\n"
        genScript += "\n"

        # Create lists and dict to be able to resolve ordered list of (grid settings instance <-> FreeCAD object) associations.
        # In its current form, this implies user-defined grid lines have to be associated with the simulation volume.
        _assoc = lambda idx: list(map(str.strip, self.form.meshPriorityTreeView.topLevelItem(idx).text(0).split(',')))
        orderedAssociations = [_assoc(k) for k in reversed(range(meshPrioritiesCount))]
        gridSettingsNodeNames = [gridSettingsNode.text(0) for [gridSettingsNode, gridSettingsInst] in items]
        fcObjects = {obj.Label: obj for obj in self.cadHelpers.getObjects()}

        for gridSettingsNodeName in gridSettingsNodeNames:
            print("Grid type : " + gridSettingsNodeName)

        for k, [categoryName, gridName, FreeCADObjectName] in enumerate(orderedAssociations):

            print("Grid priority level {} : {} :: {}".format(k, FreeCADObjectName, gridName))

            if not (gridName in gridSettingsNodeNames):
                print("Failed to resolve '{}'.".format(gridName))
                continue
            itemListIdx = gridSettingsNodeNames.index(gridName)
            gridSettingsInst = items[itemListIdx][1]

            fcObject = fcObjects.get(FreeCADObjectName, None)
            if (not fcObject):
                print("Failed to resolve '{}'.".format(FreeCADObjectName))
                continue

            ### Produce script output.

            if (not "Shape" in dir(fcObject)):
                continue

            bbCoords = fcObject.Shape.BoundBox

            # If generateLinesInside is selected, grid line region is shifted inward by lambda/20.
            if gridSettingsInst.generateLinesInside:
                delta = self.maxGridResolution_m / refUnit
                print("GRID generateLinesInside object detected, setting correction constant to " + str(
                    delta) + " " + refUnitStr)
            else:
                delta = 0

            #
            #	THIS IS HARD WIRED HERE, NEED TO BE CHANGED, LuboJ, September 2022
            #
            # DEBUG - DISABLED - generate grid inside using 1/20 of maximum lambda, it's not that equation,
            #	ie. for 3.4GHz simulation 1/20th is 4mm what is wrong for delta to generate
            #	gridlines inside object, must be much much lower like 10times
            delta = 0
            debugHardLimit = 0.1e-3  # debug hard limit to get gridlines inside STL objects

            xmax = sf * bbCoords.XMax - np.sign(bbCoords.XMax - bbCoords.XMin) * delta - debugHardLimit
            ymax = sf * bbCoords.YMax - np.sign(bbCoords.YMax - bbCoords.YMin) * delta - debugHardLimit
            zmax = sf * bbCoords.ZMax - np.sign(bbCoords.ZMax - bbCoords.ZMin) * delta - debugHardLimit
            xmin = sf * bbCoords.XMin + np.sign(bbCoords.XMax - bbCoords.XMin) * delta + debugHardLimit
            ymin = sf * bbCoords.YMin + np.sign(bbCoords.YMax - bbCoords.YMin) * delta + debugHardLimit
            zmin = sf * bbCoords.ZMin + np.sign(bbCoords.ZMax - bbCoords.ZMin) * delta + debugHardLimit

            # Write grid definition.

            genScript += "## GRID - " + gridSettingsInst.getName() + " - " + FreeCADObjectName + ' (' + gridSettingsInst.getType() + ")\n"

            if (gridSettingsInst.getType() == 'Fixed Distance'):
                if gridSettingsInst.xenabled:
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.x = np.delete(mesh.x, np.argwhere((mesh.x >= {0:g}) & (mesh.x <= {1:g})))\n".format(_r(xmin), _r(xmax))
                    genScript += "mesh.x = np.concatenate((mesh.x, np.arange({0:g},{1:g},{2:g})))\n".format(_r(xmin), _r(xmax), _r(gridSettingsInst.getXYZ(refUnit)['x']))
                if gridSettingsInst.yenabled:
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.y = np.delete(mesh.y, np.argwhere((mesh.y >= {0:g}) & (mesh.y <= {1:g})))\n".format(_r(ymin), _r(ymax))
                    genScript += "mesh.y = np.concatenate((mesh.y, np.arange({0:g},{1:g},{2:g})))\n".format(_r(ymin),_r(ymax),_r(gridSettingsInst.getXYZ(refUnit)['y']))
                if gridSettingsInst.zenabled:
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.z = np.delete(mesh.z, np.argwhere((mesh.z >= {0:g}) & (mesh.z <= {1:g})))\n".format(_r(zmin), _r(zmax))
                    genScript += "mesh.z = np.concatenate((mesh.z, np.arange({0:g},{1:g},{2:g})))\n".format(_r(zmin),_r(zmax),_r(gridSettingsInst.getXYZ(refUnit)['z']))

            elif (gridSettingsInst.getType() == 'Fixed Count'):
                if gridSettingsInst.xenabled:
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.x = np.delete(mesh.x, np.argwhere((mesh.x >= {0:g}) & (mesh.x <= {1:g})))\n".format(_r(xmin), _r(xmax))
                    if (not gridSettingsInst.getXYZ()['x'] == 1):
                        genScript += "mesh.x = np.concatenate((mesh.x, linspace({0:g},{1:g},{2:g})))\n".format(_r(xmin), _r(xmax), _r(gridSettingsInst.getXYZ(refUnit)['x']))
                    else:
                        genScript += "mesh.x = np.append(mesh.x, {0:g})\n".format(_r((xmin + xmax) / 2))

                if gridSettingsInst.yenabled:
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.y = np.delete(mesh.y, np.argwhere((mesh.y >= {0:g}) & (mesh.y <= {1:g})))\n".format(_r(ymin), _r(ymax))
                    if (not gridSettingsInst.getXYZ()['y'] == 1):
                        genScript += "mesh.y = np.concatenate((mesh.y, linspace({0:g},{1:g},{2:g})))\n".format(_r(ymin), _r(ymax), _r(
                            gridSettingsInst.getXYZ(refUnit)['y']))
                    else:
                        genScript += "mesh.y = np.append(mesh.y, {0:g})\n".format(_r((ymin + ymax) / 2))

                if gridSettingsInst.zenabled:
                    if gridSettingsInst.topPriorityLines:
                        genScript += "mesh.z = np.delete(mesh.z, np.argwhere((mesh.z >= {0:g}) & (mesh.z <= {1:g})))\n".format(_r(zmin), _r(zmax))
                    if (not gridSettingsInst.getXYZ()['z'] == 1):
                        genScript += "mesh.z = np.concatenate((mesh.z, linspace({0:g},{1:g},{2:g})))\n".format(_r(zmin), _r(zmax), _r(
                            gridSettingsInst.getXYZ(refUnit)['z']))
                    else:
                        genScript += "mesh.z = np.append(mesh.z, {0:g})\n".format(_r((zmin + zmax) / 2))

            elif (gridSettingsInst.getType() == 'User Defined'):
                genScript += "mesh = " + gridSettingsInst.getXYZ() + ";\n"

            genScript += "\n"

        genScript += "openEMS_grid.AddLine('x', mesh.x)\n"
        genScript += "openEMS_grid.AddLine('y', mesh.y)\n"
        genScript += "openEMS_grid.AddLine('z', mesh.z)\n"
        genScript += "\n"

        return genScript


    def getInitScriptLines(self):
        genScript = ""
        genScript += "# To be run with python.\n"
        genScript += "# FreeCAD to OpenEMS plugin by Lubomir Jagos, \n"
        genScript += "# see https://github.com/LubomirJagos/FreeCAD-OpenEMS-Export\n"
        genScript += "#\n"
        genScript += "# This file has been automatically generated. Manual changes may be overwritten.\n"
        genScript += "#\n"
        genScript += "### Import Libraries\n"
        genScript += "import math\n"
        genScript += "import numpy as np\n"
        genScript += "import os, tempfile, shutil\n"
        genScript += "from pylab import *\n"
        genScript += "import csv\n"
        genScript += "import CSXCAD\n"
        genScript += "from openEMS import openEMS\n"
        genScript += "from openEMS.physical_constants import *\n"
        genScript += "\n"

        genScript += "#\n"
        genScript += "# FUNCTION TO CONVERT CARTESIAN TO CYLINDRICAL COORDINATES\n"
        genScript += "#     returns coordinates in order [theta, r, z]\n"
        genScript += "#\n"
        genScript += "def cart2pol(pointCoords):\n"
        genScript += "\ttheta = np.arctan2(pointCoords[1], pointCoords[0])\n"
        genScript += "\tr = np.sqrt(pointCoords[0] ** 2 + pointCoords[1] ** 2)\n"
        genScript += "\tz = pointCoords[2]\n"
        genScript += "\treturn theta, r, z\n"
        genScript += "\n"

        genScript += "#\n"
        genScript += "# FUNCTION TO GIVE RANGE WITH ENDPOINT INCLUDED arangeWithEndpoint(0,10,2.5) = [0, 2.5, 5, 7.5, 10]\n"
        genScript += "#     returns coordinates in order [theta, r, z]\n"
        genScript += "#\n"
        genScript += "def arangeWithEndpoint(start, stop, step=1, endpoint=True):\n"
        genScript += "\tif start == stop:\n"
        genScript += "\t\treturn [start]\n"
        genScript += "\n"
        genScript += "\tarr = np.arange(start, stop, step)\n"
        genScript += "\tif endpoint and arr[-1] + step == stop:\n"
        genScript += "\t\tarr = np.concatenate([arr, [stop]])\n"
        genScript += "\treturn arr\n"
        genScript += "\n"

        genScript += "# Change current path to script file folder\n"
        genScript += "#\n"
        genScript += "abspath = os.path.abspath(__file__)\n"
        genScript += "dname = os.path.dirname(abspath)\n"
        genScript += "os.chdir(dname)\n"

        genScript += "## constants\n"
        genScript += "unit    = " + str(
            self.getUnitLengthFromUI_m()) + " # Model coordinates and lengths will be specified in " + self.form.simParamsDeltaUnitList.currentText() + ".\n"
        genScript += "fc_unit = " + str(
            self.getFreeCADUnitLength_m()) + " # STL files are exported in FreeCAD standard units (mm).\n"
        genScript += "\n"

        return genScript

    def getExcitationScriptLines(self, definitionsOnly=False):
        genScript = ""

        excitationCategory = self.form.objectAssignmentRightTreeWidget.findItems("Excitation",
                                                                                 QtCore.Qt.MatchFixedString)
        if len(excitationCategory) >= 0:
            print("Excitation Settings detected")
            print("#")
            print("#EXCITATION")

            # FOR WHOLE SIMULATION THERE IS JUST ONE EXCITATION DEFINED, so first is taken!
            if (excitationCategory[0].childCount() > 0):
                item = excitationCategory[0].child(0)
                currSetting = item.data(0, QtCore.Qt.UserRole)  # At index 0 is Default Excitation.
                # Currently only 1 excitation is allowed. Multiple excitations could be managed by setting one of them as "selected" or "active", while all others are deactivated.
                # This would help the user to manage different analysis scenarios / excitation ranges.

                print("#name: " + currSetting.getName())
                print("#type: " + currSetting.getType())

                genScript += "#######################################################################################################################################\n"
                genScript += "# EXCITATION " + currSetting.getName() + "\n"
                genScript += "#######################################################################################################################################\n"

                # EXCITATION FREQUENCY AND CELL MAXIMUM RESOLUTION CALCULATION (1/20th of minimal lambda - calculated based on maximum simulation frequency)
                # maximum grid resolution is generated into script but NOT USED IN OCTAVE SCRIPT, instead is also calculated here into python variable and used in bounding box correction
                if (currSetting.getType() == 'sinusodial'):
                    genScript += "f0 = " + str(currSetting.sinusodial['f0']) + "*" + str(
                        currSetting.getUnitsAsNumber(currSetting.units)) + "\n"
                    if not definitionsOnly:
                        genScript += "FDTD.SetSinusExcite(fc);\n"
                    genScript += "max_res = C0 / f0 / 20\n"
                    self.maxGridResolution_m = 3e8 / (
                                currSetting.sinusodial['f0'] * currSetting.getUnitsAsNumber(currSetting.units) * 20)
                    pass
                elif (currSetting.getType() == 'gaussian'):
                    genScript += "f0 = " + str(currSetting.gaussian['f0']) + "*" + str(
                        currSetting.getUnitsAsNumber(currSetting.units)) + "\n"
                    genScript += "fc = " + str(currSetting.gaussian['fc']) + "*" + str(
                        currSetting.getUnitsAsNumber(currSetting.units)) + "\n"
                    if not definitionsOnly:
                        genScript += "FDTD.SetGaussExcite(f0, fc)\n"
                    genScript += "max_res = C0 / (f0 + fc) / 20\n"
                    self.maxGridResolution_m = 3e8 / ((currSetting.gaussian['f0'] + currSetting.gaussian[
                        'fc']) * currSetting.getUnitsAsNumber(currSetting.units) * 20)
                    pass
                elif (currSetting.getType() == 'custom'):
                    f0 = currSetting.custom['f0'] * currSetting.getUnitsAsNumber(currSetting.units)
                    genScript += "f0 = " + str(currSetting.custom['f0']) + "*" + str(
                        currSetting.getUnitsAsNumber(currSetting.units)) + "\n"
                    genScript += "fc = 0.0;\n"
                    if not definitionsOnly:
                        genScript += "FDTD.SetCustomExcite(f0, '" + currSetting.custom['functionStr'].replace(
                            'f0', str(f0)) + "' )\n"
                    genScript += "max_res = 0\n"
                    self.maxGridResolution_m = 0
                    pass
                pass

                genScript += "\n"
            else:
                self.guiHelpers.displayMessage("Missing excitation, please define one.")
                pass
            pass
        return genScript

    def getBoundaryConditionsScriptLines(self):
        genScript = ""

        genScript += "#######################################################################################################################################\n"
        genScript += "# BOUNDARY CONDITIONS\n"
        genScript += "#######################################################################################################################################\n"

        _bcStr = lambda pml_val, text: '\"PML_{}\"'.format(str(pml_val)) if text == 'PML' else '\"{}\"'.format(text)
        strBC = ""
        strBC += _bcStr(self.form.PMLxmincells.value(), self.form.BCxmin.currentText()) + ","
        strBC += _bcStr(self.form.PMLxmaxcells.value(), self.form.BCxmax.currentText()) + ","
        strBC += _bcStr(self.form.PMLymincells.value(), self.form.BCymin.currentText()) + ","
        strBC += _bcStr(self.form.PMLymaxcells.value(), self.form.BCymax.currentText()) + ","
        strBC += _bcStr(self.form.PMLzmincells.value(), self.form.BCzmin.currentText()) + ","
        strBC += _bcStr(self.form.PMLzmaxcells.value(), self.form.BCzmax.currentText())

        genScript += "BC = [" + strBC + "]\n"
        genScript += "FDTD.SetBoundaryCond(BC)\n"
        genScript += "\n"

        return genScript

    def getMinimalGridlineSpacingScriptLines(self):
        genScript = ""

        if (self.form.genParamMinGridSpacingEnable.isChecked()):
            minSpacingX = self.form.genParamMinGridSpacingX.value() / 1000 / self.getUnitLengthFromUI_m()
            minSpacingY = self.form.genParamMinGridSpacingY.value() / 1000 / self.getUnitLengthFromUI_m()
            minSpacingZ = self.form.genParamMinGridSpacingZ.value() / 1000 / self.getUnitLengthFromUI_m()

            genScript += "#######################################################################################################################################\n"
            genScript += "# MINIMAL GRIDLINES SPACING, removing gridlines which are closer as defined in GUI\n"
            genScript += "#######################################################################################################################################\n"
            genScript += 'mesh.x = openEMS_grid.GetLines("x", True)\n'
            genScript += 'mesh.y = openEMS_grid.GetLines("y", True)\n'
            genScript += 'mesh.z = openEMS_grid.GetLines("z", True)\n'
            genScript += '\n'
            genScript += 'openEMS_grid.ClearLines("x")\n'
            genScript += 'openEMS_grid.ClearLines("y")\n'
            genScript += 'openEMS_grid.ClearLines("z")\n'
            genScript += '\n'
            genScript += 'for k in range(len(mesh.x)-1):\n'
            genScript += '\tif (not np.isinf(mesh.x[k]) and abs(mesh.x[k+1]-mesh.x[k]) <= ' + str(minSpacingX) + '):\n'
            genScript += '\t\tprint("Removnig line at x: " + str(mesh.x[k+1]))\n'
            genScript += '\t\tmesh.x[k+1] = np.inf\n'
            genScript += '\n'
            genScript += 'for k in range(len(mesh.y)-1):\n'
            genScript += '\tif (not np.isinf(mesh.y[k]) and abs(mesh.y[k+1]-mesh.y[k]) <= ' + str(minSpacingY) + '):\n'
            genScript += '\t\tprint("Removnig line at y: " + str(mesh.y[k+1]))\n'
            genScript += '\t\tmesh.y[k+1] = np.inf\n'
            genScript += '\n'
            genScript += 'for k in range(len(mesh.z)-1):\n'
            genScript += '\tif (not np.isinf(mesh.z[k]) and abs(mesh.z[k+1]-mesh.z[k]) <= ' + str(minSpacingZ) + '):\n'
            genScript += '\t\tprint("Removnig line at z: " + str(mesh.z[k+1]))\n'
            genScript += '\t\tmesh.z[k+1] = np.inf\n'
            genScript += '\n'

            genScript += 'mesh.x = mesh.x[~np.isinf(mesh.x)]\n'
            genScript += 'mesh.y = mesh.y[~np.isinf(mesh.y)]\n'
            genScript += 'mesh.z = mesh.z[~np.isinf(mesh.z)]\n'
            genScript += '\n'

            genScript += "openEMS_grid.AddLine('x', mesh.x)\n"
            genScript += "openEMS_grid.AddLine('y', mesh.y)\n"
            genScript += "openEMS_grid.AddLine('z', mesh.z)\n"
            genScript += '\n'

        return genScript

    #########################################################################################################################
    #                                  _                       _       _          _ _      _            _
    #                                 | |                     (_)     | |        | (_)    | |          | |
    #   __ _  ___ _ __   ___ _ __ __ _| |_ ___   ___  ___ _ __ _ _ __ | |_    ___| |_  ___| | _____  __| |
    #  / _` |/ _ \ '_ \ / _ \ '__/ _` | __/ _ \ / __|/ __| '__| | '_ \| __|  / __| | |/ __| |/ / _ \/ _` |
    # | (_| |  __/ | | |  __/ | | (_| | ||  __/ \__ \ (__| |  | | |_) | |_  | (__| | | (__|   <  __/ (_| |
    #  \__, |\___|_| |_|\___|_|  \__,_|\__\___| |___/\___|_|  |_| .__/ \__|  \___|_|_|\___|_|\_\___|\__,_|
    #   __/ |                                                   | |
    #  |___/
    #
    #	GENERATE SCRIPT CLICKED - go through object assignment tree categories, output child item data.
    #
    def generateOpenEMSScript(self, outputDir=None):

        # Create outputDir relative to local FreeCAD file if output dir does not exists
        #   if outputDir is set to same value
        #   if outputStr is None then folder with name as FreeCAD file with suffix _openEMS_simulation is created
        outputDir = self.createOuputDir(outputDir)

        # Update status bar to inform user that exporting has begun.
        if self.statusBar is not None:
            self.statusBar.showMessage("Generating OpenEMS script and geometry files ...", 5000)
            QtWidgets.QApplication.processEvents()

        # Constants and variable initialization.

        refUnit = self.getUnitLengthFromUI_m()  # Coordinates need to be given in drawing units
        refUnitStr = self.form.simParamsDeltaUnitList.currentText()
        sf = self.getFreeCADUnitLength_m() / refUnit  # scaling factor for FreeCAD units to drawing units

        # List categories and items.

        itemsByClassName = self.getItemsByClassName()

        # Write script header.

        genScript = ""

        genScript += "# OpenEMS FDTD Analysis Automation Script\n"
        genScript += "#\n"

        genScript += self.getInitScriptLines()

        genScript += "## switches & options\n"
        genScript += "draw_3d_pattern = 0  # this may take a while...\n"
        genScript += "use_pml = 0          # use pml boundaries instead of mur\n"
        genScript += "\n"
        genScript += "currDir = os.getcwd()\n"
        genScript += "print(currDir)\n"
        genScript += "\n"

        genScript += "# setup_only : dry run to view geometry, validate settings, no FDTD computations\n"
        genScript += "# debug_pec  : generated PEC skeleton (use ParaView to inspect)\n"
        genScript += f"debug_pec = {'True' if self.form.generateDebugPECCheckbox.isChecked() else 'False'}\n"
        genScript += f"setup_only = {'True' if self.form.generateJustPreviewCheckbox.isChecked() else 'False'}\n"
        genScript += "\n"

        # Write simulation settings.

        genScript += "## prepare simulation folder\n"
        genScript += "Sim_Path = os.path.join(currDir, 'simulation_output')\n"
        genScript += "Sim_CSX = '" + os.path.splitext(os.path.basename(self.cadHelpers.getCurrDocumentFileName()))[0] + ".xml'\n"

        genScript += "if os.path.exists(Sim_Path):\n"
        genScript += "\tshutil.rmtree(Sim_Path)   # clear previous directory\n"
        genScript += "\tos.mkdir(Sim_Path)    # create empty simulation folder\n"
        genScript += "\n"

        genScript += "## setup FDTD parameter & excitation function\n"
        genScript += "max_timesteps = " + str(self.form.simParamsMaxTimesteps.value()) + "\n"
        genScript += "min_decrement = " + str(self.form.simParamsMinDecrement.value()) + " # 10*log10(min_decrement) dB  (i.e. 1E-5 means -50 dB)\n"

        if (self.getModelCoordsType() == "cylindrical"):
            genScript += "CSX = CSXCAD.ContinuousStructure(CoordSystem=1)\n"
            genScript += "FDTD = openEMS(NrTS=max_timesteps, EndCriteria=min_decrement, CoordSystem=1)\n"
        else:
            genScript += "CSX = CSXCAD.ContinuousStructure()\n"
            genScript += "FDTD = openEMS(NrTS=max_timesteps, EndCriteria=min_decrement)\n"

        genScript += "FDTD.SetCSX(CSX)\n"
        genScript += "\n"

        print("======================== REPORT BEGIN ========================\n")

        self.reportFreeCADItemSettings(itemsByClassName.get("FreeCADSettingsItem", None))

        # Write boundary conditions definitions.
        genScript += self.getBoundaryConditionsScriptLines()

        # Write coordinate system definitions.
        genScript += self.getCoordinateSystemScriptLines()

        # Write excitation definition.
        genScript += self.getExcitationScriptLines()

        # Write material definitions.
        genScript += self.getMaterialDefinitionsScriptLines(itemsByClassName.get("MaterialSettingsItem", None), outputDir)

        # Write grid definitions.
        genScript += self.getOrderedGridDefinitionsScriptLines(itemsByClassName.get("GridSettingsItem", None))

        # Write port definitions.
        genScript += self.getPortDefinitionsScriptLines(itemsByClassName.get("PortSettingsItem", None))

        # Write lumped part definitions.
        genScript += self.getLumpedPartDefinitionsScriptLines(itemsByClassName.get("LumpedPartSettingsItem", None))

        # Write probes definitions
        genScript += self.getProbeDefinitionsScriptLines(itemsByClassName.get("ProbeSettingsItem", None))

        # Write NF2FF probe grid definitions.
        genScript += self.getNF2FFDefinitionsScriptLines(itemsByClassName.get("ProbeSettingsItem", None))

        # Write scriptlines which removes gridline too close, must be enabled in GUI, it's checking checkbox inside
        genScript += self.getMinimalGridlineSpacingScriptLines()

        print("======================== REPORT END ========================\n")

        # Finalize script.

        genScript += "#######################################################################################################################################\n"
        genScript += "# RUN\n"
        genScript += "#######################################################################################################################################\n"

        genScript += "### Run the simulation\n"
        genScript += "CSX_file = os.path.join(Sim_Path, Sim_CSX)\n"
        genScript += "if not os.path.exists(Sim_Path):\n"
        genScript += "\tos.mkdir(Sim_Path)\n"
        genScript += "CSX.Write2XML(CSX_file)\n"
        genScript += "from CSXCAD import AppCSXCAD_BIN\n"
        genScript += "os.system(AppCSXCAD_BIN + ' \"{}\"'.format(CSX_file))\n"
        genScript += "\n"
        genScript += "FDTD.Run(Sim_Path, verbose=3, cleanup=True, setup_only=setup_only, debug_pec=debug_pec)\n"

        # Write _OpenEMS.py script file to current directory.
        currDir, nameBase = self.getCurrDir()

        if (not outputDir is None):
            fileName = f"{outputDir}/{nameBase}_openEMS.py"
        else:
            fileName = f"{currDir}/{nameBase}_openEMS.py"

        f = open(fileName, "w", encoding='utf-8')
        f.write(genScript)
        f.close()

        # Show message or update status bar to inform user that exporting has finished.

        self.guiHelpers.displayMessage('Simulation script written to: ' + fileName, forceModal=True)
        print('Simulation script written to: ' + fileName)

        return

    #
    #	Write NF2FF Button clicked, generate script to display far field pattern
    #
    def writeNf2ffButtonClicked(self, outputDir=None, nf2ffBoxName="", nf2ffBoxInputPortName="", plotFrequency=0, freqCount=501):
        genScript = ""
        genScript += "# Plot far field for structure.\n"
        genScript += "#\n"

        genScript += self.getInitScriptLines()

        genScript += "currDir = os.getcwd()\n"
        genScript += "Sim_Path = os.path.join(currDir, r'simulation_output')\n"
        genScript += "print(currDir)\n"
        genScript += "\n"

        genScript += "## setup FDTD parameter & excitation function\n"
        genScript += "max_timesteps = " + str(self.form.simParamsMaxTimesteps.value()) + "\n"
        genScript += "min_decrement = " + str(self.form.simParamsMinDecrement.value()) + " # 10*log10(min_decrement) dB  (i.e. 1E-5 means -50 dB)\n"

        if (self.getModelCoordsType() == "cylindrical"):
            genScript += "CSX = CSXCAD.ContinuousStructure(CoordSystem=1)\n"
            genScript += "FDTD = openEMS(NrTS=max_timesteps, EndCriteria=min_decrement, CoordSystem=1)\n"
        else:
            genScript += "CSX = CSXCAD.ContinuousStructure()\n"
            genScript += "FDTD = openEMS(NrTS=max_timesteps, EndCriteria=min_decrement)\n"

        genScript += "FDTD.SetCSX(CSX)\n"
        genScript += "\n"

        # List categories and items.
        itemsByClassName = self.getItemsByClassName()

        # Write boundary conditions definitions.
        genScript += self.getBoundaryConditionsScriptLines()

        # Write coordinate system definitions.
        genScript += self.getCoordinateSystemScriptLines()

        # Write excitation definition.
        genScript += self.getExcitationScriptLines(definitionsOnly=True)

        # Write material definitions.
        genScript += self.getMaterialDefinitionsScriptLines(itemsByClassName.get("MaterialSettingsItem", None), outputDir, generateObjects=False)

        # Write grid definitions.
        genScript += self.getOrderedGridDefinitionsScriptLines(itemsByClassName.get("GridSettingsItem", None))

        # Write port definitions:
        #    - must be after gridlines definitions
        #    - must be before nf2ff
        genScript += self.getPortDefinitionsScriptLines(itemsByClassName.get("PortSettingsItem", None))

        # Write probes definitions
        genScript += self.getProbeDefinitionsScriptLines(itemsByClassName.get("ProbeSettingsItem", None))

        # Write NF2FF probe grid definitions. THIS NEEDS TO BE DONE TO FILL self.internalNF2FFIndexNamesList[] with keys and indexes, key = "[nf2ff probe category name] - [object label]"
        genScript += self.getNF2FFDefinitionsScriptLines(itemsByClassName.get("ProbeSettingsItem", None))

        # Write scriptlines which removes gridline too close, must be enabled in GUI, it's checking checkbox inside
        genScript += self.getMinimalGridlineSpacingScriptLines()

        #
        #   Current NF2FF box index
        #
        print(f"writeNf2ffButtonClicked() > generate script, getting nf2ff box index for '{nf2ffBoxName}'")
        currentNF2FFBoxIndex = self.internalNF2FFIndexNamesList[nf2ffBoxName.replace(" ", "_")]
        currentNF2FFInputPortIndex = self.internalPortIndexNamesList[nf2ffBoxInputPortName]

        thetaStart = str(self.form.portNf2ffThetaStart.value())
        thetaStop = str(self.form.portNf2ffThetaStop.value())
        thetaStep = str(self.form.portNf2ffThetaStep.value())

        phiStart = str(self.form.portNf2ffPhiStart.value())
        phiStop = str(self.form.portNf2ffPhiStop.value())
        phiStep = str(self.form.portNf2ffPhiStep.value())

        #
        #   ATTENTION THIS IS SPECIFIC FOR FAR FIELD PLOTTING, plotFrequency and frequencies count
        #       port is calculated to get P_in (input power)
        #
        genScript += f"""
#######################################################################################################################################
# Farfield plot and 3D gain generated
#######################################################################################################################################

def generatorFunc_DumpFF2VTK(farfield, t, a, filename):
    '''
       Create .vtk file
       params:
           farfield: 2D array of values of field
           t:        theta angles in radians
           a:        phi angles in radians
           filename: output file name
    '''

    with (open(filename, 'w') as outFile):
         outFile.write(f"# vtk DataFile Version 3.0\\n")
         outFile.write(f"Structured Grid by python-interface of openEMS\\n")
         outFile.write(f"ASCII\\n")
         outFile.write(f"DATASET STRUCTURED_GRID\\n")

         outFile.write(f"DIMENSIONS 1 {{len(t)}} {{len(a)}}\\n")
         outFile.write(f"POINTS {{len(t)*len(a)}} double\\n")

         for na in range(len(a)):
             for nt in range(len(t)):
                 val1 = farfield[nt][na]*math.sin(t[nt])*math.cos(a[na])
                 val2 = farfield[nt][na]*math.sin(t[nt])*math.sin(a[na])
                 val3 = farfield[nt][na]*math.cos(t[nt])
                 outFile.write(f"{{val1}} {{val2}} {{val3}}\\n")

         outFile.write(f'\\n\\n');
         outFile.write(f'POINT_DATA {{len(t)*len(a)}}\\n');
         outFile.write(f'SCALARS gain double 1\\n');
         outFile.write(f'LOOKUP_TABLE default\\n');
         for na in range(len(a)):
             for nt in range(len(t)):
                 outFile.write(f"{{farfield[nt][na]}}\\n")

#
# Frequency range
#
freq = np.linspace(max([0, f0-fc]), f0+fc, {freqCount})
plotFrequency = {plotFrequency}
port[{currentNF2FFInputPortIndex}].CalcPort(Sim_Path, freq)
P_in_0 = np.interp(f0, freq, port[{currentNF2FFInputPortIndex}].P_acc)

#
# Calculate the far field at phi=0 degrees and at phi=90 degrees
#   Using angles in degrees.
#
thetaRange = arangeWithEndpoint({thetaStart}, {thetaStop}, {thetaStep})
phiRange = arangeWithEndpoint({phiStart}, {phiStop}, {phiStep}) - 180

print( 'calculating the 3D far field...' )

#
#	nf2ffBoxList[<name>] - NF2FF box structure which should be calculated
#       INPUT ANGLES ARE IN DEGREES for python interface!
#
nf2ff = nf2ffBoxList['{nf2ffBoxName.replace(" ", "_")}'].CalcNF2FF(Sim_Path, plotFrequency, thetaRange, phiRange, outfile='3D_Pattern.h5', verbose=True, read_cached=False)

Dmax_dB = 10*log10(nf2ff.Dmax[0])
E_norm = 20.0*log10(nf2ff.E_norm[0]/np.max(nf2ff.E_norm[0])) + 10*log10(nf2ff.Dmax[0])

theta_HPBW = thetaRange[ np.where(squeeze(E_norm[:,phiRange==0])<Dmax_dB-3)[0][0] ]

# display power and directivity
print('radiated power: Prad = ' + str(nf2ff.Prad[0]) + ' Watt')
print('directivity: Dmax = ' + str(Dmax_dB) + ' dBi)')
print('efficiency: nu_rad = ' + str(100*nf2ff.Prad[0]/P_in_0) + ' %')
print('theta_HPBW = ' + str(theta_HPBW) + '°')

with (open('openEMS_simulation_nf2ff_info.txt', 'w') as outFile):
    outFile.write(f'radiated power: Prad = {{nf2ff.Prad[0]}} Watt\\n')
    outFile.write(f'directivity: Dmax = {{Dmax_dB}} dBi)\\n')
    outFile.write(f'efficiency: nu_rad = {{100*nf2ff.Prad[0]/P_in_0}} %\\n')
    outFile.write(f'theta_HPBW = {{theta_HPBW}}°\\n')
    outFile.write(f'\\n')

##
E_norm = 20.0*log10(nf2ff.E_norm[0]/np.max(nf2ff.E_norm[0])) + 10*log10(nf2ff.Dmax[0])
E_CPRH = 20.0*log10(np.abs(nf2ff.E_cprh[0])/np.max(nf2ff.E_norm[0])) + 10*log10(nf2ff.Dmax[0])
E_CPLH = 20.0*log10(np.abs(nf2ff.E_cplh[0])/np.max(nf2ff.E_norm[0])) + 10*log10(nf2ff.Dmax[0])

##
figure()
plot(thetaRange, E_norm[:,phiRange==0],'k-' , linewidth=2, label='$|E|$')
plot(thetaRange, E_CPRH[:,phiRange==0],'g--', linewidth=2, label='$|E_{{CPRH}}|$')
plot(thetaRange, E_CPLH[:,phiRange==0],'r-.', linewidth=2, label='$|E_{{CPLH}}|$')
grid()
xlabel('theta (deg)')
ylabel('directivity (dBi)')
title('Frequency: {{}} GHz'.format(nf2ff.freq[0]/1e9))
legend()

show()
  
#
# Dump radiation field to vtk file
#
directivity = nf2ff.P_rad[0]/nf2ff.Prad*4*pi
directivity_CPRH = np.abs(nf2ff.E_cprh[0])**2/np.max(nf2ff.E_norm[0][:])**2*nf2ff.Dmax[0]
directivity_CPLH = np.abs(nf2ff.E_cplh[0])**2/np.max(nf2ff.E_norm[0][:])**2*nf2ff.Dmax[0]

generatorFunc_DumpFF2VTK(directivity, nf2ff.theta, nf2ff.phi, os.path.join(Sim_Path, '3D_Pattern_GAIN.vtk'))
generatorFunc_DumpFF2VTK(directivity_CPRH, nf2ff.theta, nf2ff.phi, os.path.join(Sim_Path, '3D_Pattern_CPRH.vtk'))
generatorFunc_DumpFF2VTK(directivity_CPLH, nf2ff.theta, nf2ff.phi, os.path.join(Sim_Path, '3D_Pattern_CPLH.vtk'))

E_far_normalized = E_norm / np.max(E_norm) * nf2ff.Dmax[0]
generatorFunc_DumpFF2VTK(E_far_normalized, nf2ff.theta, nf2ff.phi, os.path.join(Sim_Path, '3D_Pattern_Efield_norm.vtk'))
"""

        #
        # WRITE OpenEMS Script file into current dir
        #
        currDir, nameBase = self.getCurrDir()

        self.createOuputDir(outputDir)
        if (not outputDir is None):
            fileName = f"{outputDir}/{nameBase}_draw_NF2FF.py"
        else:
            fileName = f"{currDir}/{nameBase}_draw_NF2FF.py"

        f = open(fileName, "w", encoding='utf-8')
        f.write(genScript)
        f.close()
        print('Script to display far field written into: ' + fileName)
        self.guiHelpers.displayMessage('Script to display far field written into: ' + fileName, forceModal=False)

    def drawS11ButtonClicked(self, outputDir=None, portName=""):
        genScript = ""
        genScript += "# Plot S11\n"
        genScript += "#\n"

        genScript += self.getInitScriptLines()

        genScript += "currDir = os.getcwd()\n"
        genScript += "Sim_Path = os.path.join(currDir, r'simulation_output')\n"
        genScript += "print(currDir)\n"
        genScript += "\n"

        genScript += "## setup FDTD parameter & excitation function\n"
        genScript += "max_timesteps = " + str(self.form.simParamsMaxTimesteps.value()) + "\n"
        genScript += "min_decrement = " + str(self.form.simParamsMinDecrement.value()) + " # 10*log10(min_decrement) dB  (i.e. 1E-5 means -50 dB)\n"

        if (self.getModelCoordsType() == "cylindrical"):
            genScript += "CSX = CSXCAD.ContinuousStructure(CoordSystem=1)\n"
            genScript += "FDTD = openEMS(NrTS=max_timesteps, EndCriteria=min_decrement, CoordSystem=1)\n"
        else:
            genScript += "CSX = CSXCAD.ContinuousStructure()\n"
            genScript += "FDTD = openEMS(NrTS=max_timesteps, EndCriteria=min_decrement)\n"

        genScript += "FDTD.SetCSX(CSX)\n"
        genScript += "\n"

        # List categories and items.
        itemsByClassName = self.getItemsByClassName()

        # Write coordinate system definitions.
        genScript += self.getCoordinateSystemScriptLines()

        # Write excitation definition.
        genScript += self.getExcitationScriptLines(definitionsOnly=True)

        # Write material definitions.
        genScript += self.getMaterialDefinitionsScriptLines(itemsByClassName.get("MaterialSettingsItem", None),
                                                            outputDir, generateObjects=False)

        # Write grid definitions.
        genScript += self.getOrderedGridDefinitionsScriptLines(itemsByClassName.get("GridSettingsItem", None))

        # Write scriptlines which removes gridline too close, must be enabled in GUI, it's checking checkbox inside
        genScript += self.getMinimalGridlineSpacingScriptLines()

        # Write port definitions.
        genScript += self.getPortDefinitionsScriptLines(itemsByClassName.get("PortSettingsItem", None))

        genScript += f"""## postprocessing & do the plots
freq = np.linspace(max(1e6,f0-fc), f0+fc, 501)
port[{self.internalPortIndexNamesList[portName]}].CalcPort(Sim_Path, freq)

Zin = port[{self.internalPortIndexNamesList[portName]}].uf_tot / port[{self.internalPortIndexNamesList[portName]}].if_tot
s11 = port[{self.internalPortIndexNamesList[portName]}].uf_ref / port[{self.internalPortIndexNamesList[portName]}].uf_inc
s11_dB = 20.0*np.log10(np.abs(s11))

# plot the feed point impedance
figure()
plot(freq / 1e6, np.real(Zin), 'k-', linewidth=2, label=r'$\Re(Z_{{in}})$')
grid()
plot(freq / 1e6, np.imag(Zin), 'r--', linewidth=2, label=r'$\Im(Z_{{in}})$')
title('impedance of {portName}')
xlabel('frequency (MHz)')
ylabel('$Z (\\Omega)$')
legend()

# plot S11 parameter
figure()
plot(freq/1e6, s11_dB, 'k-', linewidth=2, label='$S_{{11}}$')
grid()
legend()
title('S11-Parameter (dB) of {portName}')
ylabel('S11 (dB)')
xlabel('Frequency (MHz)')

show()  #show all figures at once

#
#   Write S11, real and imag Z_in into CSV file separated by ';'
#
filename = 'openEMS_simulation_s11_dB.csv'

with open(filename, 'w', newline='') as csvfile:
\twriter = csv.writer(csvfile, delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL)
\twriter.writerow(['freq (MHz)', 's11 (dB)', 'real Z_in', 'imag Z_in', 'Z_in total'])
\twriter.writerows(np.array([
\t\t(freq/1e6),
\t\ts11_dB,
\t\tnp.real(Zin),
\t\tnp.imag(Zin),
\t\tnp.abs(Zin)
\t]).T) #creates array with 1st row frequencies, 2nd row S11, ... and transpose it
"""

        #
        # WRITE OpenEMS Script file into current dir
        #
        currDir, nameBase = self.getCurrDir()

        self.createOuputDir(outputDir)
        if (not outputDir is None):
            fileName = f"{outputDir}/{nameBase}_draw_S11.py"
        else:
            fileName = f"{currDir}/{nameBase}_draw_S11.py"

        f = open(fileName, "w", encoding='utf-8')
        f.write(genScript)
        f.close()
        print('Draw result from simulation file written into: ' + fileName)
        self.guiHelpers.displayMessage('Draw result from simulation file written into: ' + fileName, forceModal=False)

    def drawS21ButtonClicked(self, outputDir=None, sourcePortName="", targetPortName=""):
        genScript = ""
        genScript += "# Plot S11, S21 parameters from OpenEMS results.\n"
        genScript += "#\n"

        genScript += self.getInitScriptLines()

        genScript += "currDir = os.getcwd()\n"
        genScript += "Sim_Path = os.path.join(currDir, r'simulation_output')\n"
        genScript += "print(currDir)\n"
        genScript += "\n"

        genScript += "## setup FDTD parameter & excitation function\n"
        genScript += "max_timesteps = " + str(self.form.simParamsMaxTimesteps.value()) + "\n"
        genScript += "min_decrement = " + str(self.form.simParamsMinDecrement.value()) + " # 10*log10(min_decrement) dB  (i.e. 1E-5 means -50 dB)\n"

        if (self.getModelCoordsType() == "cylindrical"):
            genScript += "CSX = CSXCAD.ContinuousStructure(CoordSystem=1)\n"
            genScript += "FDTD = openEMS(NrTS=max_timesteps, EndCriteria=min_decrement, CoordSystem=1)\n"
        else:
            genScript += "CSX = CSXCAD.ContinuousStructure()\n"
            genScript += "FDTD = openEMS(NrTS=max_timesteps, EndCriteria=min_decrement)\n"

        genScript += "FDTD.SetCSX(CSX)\n"
        genScript += "\n"

        # List categories and items.
        itemsByClassName = self.getItemsByClassName()

        # Write coordinate system definitions.
        genScript += self.getCoordinateSystemScriptLines()

        # Write excitation definition.
        genScript += self.getExcitationScriptLines(definitionsOnly=True)

        # Write material definitions.
        genScript += self.getMaterialDefinitionsScriptLines(itemsByClassName.get("MaterialSettingsItem", None), outputDir, generateObjects=False)

        # Write grid definitions.
        genScript += self.getOrderedGridDefinitionsScriptLines(itemsByClassName.get("GridSettingsItem", None))

        # Write scriptlines which removes gridline too close, must be enabled in GUI, it's checking checkbox inside
        genScript += self.getMinimalGridlineSpacingScriptLines()

        # Write port definitions.
        genScript += self.getPortDefinitionsScriptLines(itemsByClassName.get("PortSettingsItem", None))

        # Post-processing and plot generation.
        genScript += "#######################################################################################################################################\n"
        genScript += "# POST-PROCESSING AND PLOT GENERATION\n"
        genScript += "#######################################################################################################################################\n"
        genScript += "\n"
        genScript += "freq = np.linspace(max(1e6, f0 - fc), f0 + fc, 501)\n"
        genScript += f"port[{self.internalPortIndexNamesList[sourcePortName]}].CalcPort(Sim_Path, freq)\n"
        genScript += f"port[{self.internalPortIndexNamesList[targetPortName]}].CalcPort(Sim_Path, freq)\n"
        genScript += "\n"
        genScript += f"s11 = port[{self.internalPortIndexNamesList[sourcePortName]}].uf_ref / port[{self.internalPortIndexNamesList[sourcePortName]}].uf_inc\n"
        genScript += f"s21 = port[{self.internalPortIndexNamesList[targetPortName]}].uf_ref / port[{self.internalPortIndexNamesList[sourcePortName]}].uf_inc\n"
        genScript += "\n"
        genScript += "s11_dB = 20*log10(abs(s11))\n"
        genScript += "s21_dB = 20*log10(abs(s21))\n"
        genScript += "\n"
        genScript += "plot(freq/1e9,s11_dB,'k-', linewidth=2)\n"
        genScript += "grid()\n"
        genScript += "plot(freq/1e9,s21_dB,'r--', linewidth=2)\n"
        genScript += "legend(('$S_{11}$','$S_{21}$'))\n"
        genScript += f"title('S21-Parameter\\n{sourcePortName} $\\\\rightarrow$ {targetPortName}', fontsize=12)\n"
        genScript += "ylabel('S21(dB)', fontsize=12)\n"
        genScript += "xlabel('frequency (GHz)', fontsize=12)\n"
        genScript += "ylim([-40, 2])\n"
        genScript += "show()\n"
        genScript += "\n"

        genScript += "#######################################################################################################################################\n"
        genScript += "# SAVE PLOT DATA\n"
        genScript += "#######################################################################################################################################\n"
        genScript += "\n"
        genScript += "#\n"
        genScript += "#   Write S11, real and imag Z_in into CSV file separated by ';'\n"
        genScript += "#\n"
        genScript += "filename = 'openEMS_simulation_s11_dB.csv'\n"
        genScript += "\n"
        genScript += "with open(filename, 'w', newline='') as csvfile:\n"
        genScript += "\twriter = csv.writer(csvfile, delimiter=';', quotechar='|', quoting=csv.QUOTE_MINIMAL)\n"
        genScript += "\twriter.writerow(['freq (Hz)', 's11 (dB)', 's21 (dB)'])\n"
        genScript += "\twriter.writerows(np.array([freq, s11_dB, s21_dB]).T)  # creates array with 1st row frequencies, 2nd row S11 and transpose it\n"
        genScript += "\n"

        # Write OpenEMS Script file into current dir.

        currDir, nameBase = self.getCurrDir()

        self.createOuputDir(outputDir)
        if (not outputDir is None):
            fileName = f"{outputDir}/{nameBase}_draw_S21.py"
        else:
            fileName = f"{currDir}/{nameBase}_draw_S21.py"

        f = open(fileName, "w", encoding='utf-8')
        f.write(genScript)
        f.close()
        print('Draw result from simulation file written to: ' + fileName)
        self.guiHelpers.displayMessage('Draw result from simulation file written to: ' + fileName, forceModal=False)
