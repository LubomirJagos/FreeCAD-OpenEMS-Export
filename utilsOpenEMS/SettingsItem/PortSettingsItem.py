from .  SettingsItem import SettingsItem
from utilsOpenEMS.GlobalFunctions.GlobalFunctions import _bool, _r, _getFreeCADUnitLength_m

# Port settings
#	There are just few types of ports defined in OpenEMS:
#		- lumped
#		- microstrip
#		- circular waveguide
#		- rectangular waveguide
class PortSettingsItem(SettingsItem):
    def __init__(self, name="", type="", R=0, RUnits="", isActive=False, direction="z", excitationAmplitude=1, infiniteResistance=False,
                 mslFeedShiftValue="", mslFeedShiftUnits="", mslMeasPlaneShiftValue="", mslMeasPlaneShiftUnits="", mslMaterial="", mslPropagation="",
                 waveguideRectDir = "", waveguideCircDir="",
                 coaxialConductorMaterial = "", coaxialMaterial = "", coaxialPropagation = "", coaxialInnerRadiusValue = 0, coaxialInnerRadiusUnits = "", coaxialShellThicknessValue = 0, coaxialShellThicknessUnits = "", coaxialFeedpointShiftValue = 0, coaxialFeedpointShiftUnits = "", coaxialMeasPlaneShiftValue = 0, coaxialMeasPlaneShiftUnits = "",
                 coplanarMaterial = "", coplanarPropagation = "", coplanarGapValue = 0, coplanarGapUnits = "", coplanarFeedpointShiftValue = 0, coplanarFeedpointShiftUnits = "", coplanarMeasPlaneShiftValue = 0, coplanarMeasPlaneShiftUnits = "",
                 striplineMaterial = "", striplinePropagation = "", striplineHeightValue = 0, striplineHeightUnits = "", striplineFeedpointShiftValue = 0, striplineFeedpointShiftUnits = "", striplineMeasPlaneShiftValue = 0, striplineMeasPlaneShiftUnits = "",
                 ):
        self.name = name
        self.type = type

        self.R = R
        self.RUnits = RUnits
        self.isActive = isActive
        self.direction = direction
        self.excitationAmplitude = excitationAmplitude
        self.infiniteResistance = infiniteResistance

        self.mslFeedShiftValue = mslFeedShiftValue
        self.mslFeedShiftUnits = mslFeedShiftUnits
        self.mslMeasPlaneShiftValue = mslMeasPlaneShiftValue
        self.mslMeasPlaneShiftUnits = mslMeasPlaneShiftUnits
        self.mslMaterial = mslMaterial
        self.mslPropagation = mslPropagation

        self.waveguideRectDir = waveguideRectDir
        self.waveguideCircDir = waveguideCircDir

        self.coaxialConductorMaterial = coaxialConductorMaterial
        self.coaxialMaterial = coaxialMaterial
        self.coaxialPropagation = coaxialPropagation
        self.coaxialInnerRadiusValue = coaxialInnerRadiusValue
        self.coaxialInnerRadiusUnits = coaxialInnerRadiusUnits
        self.coaxialShellThicknessValue = coaxialShellThicknessValue
        self.coaxialShellThicknessUnits = coaxialShellThicknessUnits
        self.coaxialFeedpointShiftValue = coaxialFeedpointShiftValue
        self.coaxialFeedpointShiftUnits = coaxialFeedpointShiftUnits
        self.coaxialMeasPlaneShiftValue = coaxialMeasPlaneShiftValue
        self.coaxialMeasPlaneShiftUnits = coaxialMeasPlaneShiftUnits

        self.coplanarMaterial = coplanarMaterial
        self.coplanarPropagation = coplanarPropagation
        self.coplanarGapValue = coplanarGapValue
        self.coplanarGapUnits = coplanarGapUnits
        self.coplanarFeedpointShiftValue = coplanarFeedpointShiftValue
        self.coplanarFeedpointShiftUnits = coplanarFeedpointShiftUnits
        self.coplanarMeasPlaneShiftValue = coplanarMeasPlaneShiftValue
        self.coplanarMeasPlaneShiftUnits = coplanarMeasPlaneShiftUnits

        self.striplineMaterial = striplineMaterial
        self.striplinePropagation = striplinePropagation
        self.striplineHeightValue = striplineHeightValue
        self.striplineHeightUnits = striplineHeightUnits
        self.striplineFeedpointShiftValue = striplineFeedpointShiftValue
        self.striplineFeedpointShiftUnits = striplineFeedpointShiftUnits
        self.striplineMeasPlaneShiftValue = striplineMeasPlaneShiftValue
        self.striplineMeasPlaneShiftUnits = striplineMeasPlaneShiftUnits

        return

    def serializeToString(self):
        jsonString = "{'name': '" + self.name
        jsonString += ", 'R': " + self.R
        jsonString += ", 'RUnits': '" + self.RUnits + "'"
        jsonString += ", 'isActive': " + str(self.isActive)
        if (self.type == "lumped"):
            jsonString += ", 'type': 'lumped'"
        if (self.type == "microstrip"):
            jsonString += ", 'type': 'microstrip'"
            jsonString += ", 'mslFeedShiftValue': " + self.mslFeedShiftValue
            jsonString += ", 'mslFeedShiftUnits': " + self.mslFeedShiftUnits
            jsonString += ", 'mslMeasPlaneShiftValue': " + self.mslMeasPlaneShiftValue
            jsonString += ", 'mslMeasPlaneShiftUnits': " + self.mslMeasPlaneShiftUnits
            jsonString += ", 'mslMaterial': " + self.mslMaterial
            jsonString += ", 'mslPhysicalOrientation': " + self.mslPhysicalOrientation
        if (self.type == "circular waveguide"):
            jsonString += ", 'type': 'circular waveguide'"
        if (self.type == "rectangular waveguide"):
            jsonString += ", 'type': 'rectangular waveguide'"
            jsonString += ", 'waveguideDirection': " + self.waveguideRectDir
        if (self.type == "nf2ff box"):
            jsonString += ", 'type': 'nf2ff box'"
        jsonString += "}"
        return jsonString

    def getRUnits(self):
        return self.getUnitsAsNumber(self.RUnits)

    def getMicrostripStartStopCoords(self, bbCoords, sf):
        #
        #   It's important to generate microstrip port right, that means where is placed microstrip line, because microstrip consists from ground plane and trace
        #       This is just playing with X,Y,Z coordinates of boundary box for microstrip port for min, max coordinates.
        #
        portStartX = _r(sf * bbCoords.XMin)
        portStartY = _r(sf * bbCoords.YMin)
        portStartZ = _r(sf * bbCoords.ZMin)
        portStopX = _r(sf * bbCoords.XMax)
        portStopY = _r(sf * bbCoords.YMax)
        portStopZ = _r(sf * bbCoords.ZMax)

        if (self.direction.startswith(("XY plane, top layer", "r-theta, top layer"))):
            portStartZ = _r(sf * bbCoords.ZMax)
            portStopZ = _r(sf * bbCoords.ZMin)
        elif (self.direction.startswith(("YZ plane, right layer", "z-theta, outside layer"))):
            portStartX = _r(sf * bbCoords.XMax)
            portStopX = _r(sf * bbCoords.XMin)
        elif (self.direction.startswith(("XZ plane, front layer", "z-theta, outside layer"))):
            portStartY = _r(sf * bbCoords.YMax)
            portStopY = _r(sf * bbCoords.YMin)

        if (self.mslPropagation.startswith("z-")):
            portStartZ = _r(sf * bbCoords.ZMax)
            portStopZ = _r(sf * bbCoords.ZMin)
        elif (self.mslPropagation.startswith(("x-", "r-"))):
            portStartX = _r(sf * bbCoords.XMax)
            portStopX = _r(sf * bbCoords.XMin)
        elif (self.mslPropagation.startswith(("y-", "theta-"))):
            portStartY = _r(sf * bbCoords.YMax)
            portStopY = _r(sf * bbCoords.YMin)

        return portStartX, portStartY, portStartZ, portStopX, portStopY, portStopZ

    def getCircularWaveguidStartStopRadius(self, bbCoords, sf):
        portStartX = _r(sf * bbCoords.XMin)
        portStartY = _r(sf * bbCoords.YMin)
        portStartZ = _r(sf * bbCoords.ZMin)
        portStopX = _r(sf * bbCoords.XMax)
        portStopY = _r(sf * bbCoords.YMax)
        portStopZ = _r(sf * bbCoords.ZMax)

        if (self.waveguideCircDirstartswith("z-")):
            portStartZ = _r(sf * bbCoords.ZMax)
            portStopZ = _r(sf * bbCoords.ZMin)
        elif (self.waveguideCircDir.startswith(("x-", "r-"))):
            portStartX = _r(sf * bbCoords.XMax)
            portStopX = _r(sf * bbCoords.XMin)
        elif (self.waveguideCircDir.startswith(("y-", "theta-"))):
            portStartY = _r(sf * bbCoords.YMax)
            portStopY = _r(sf * bbCoords.YMin)

        #
        #   Based on port excitation direction which is not used at waveguide due it has modes, but based on that height and width are resolved.
        #
        waveguideRadius = 0
        if (self.direction.startswith("z")):
            waveguideRadius = min(abs(portStartX - portStopX), abs(portStartY - portStopY))
        elif (self.direction.startswith(("x", "r"))):
            waveguideRadius = min(abs(portStartY - portStopY), abs(portStartZ - portStopZ))
        elif (self.direction.startswith(("y", "theta"))):
            waveguideRadius = min(abs(portStartX - portStopX), abs(portStartZ - portStopZ))

        return portStartX, portStartY, portStartZ, portStopX, portStopY, portStopZ, waveguideRadius

    def getRectangularWaveguideStartStopWidthHeight(self, bbCoords, sf):
        portStartX = _r(sf * bbCoords.XMin)
        portStartY = _r(sf * bbCoords.YMin)
        portStartZ = _r(sf * bbCoords.ZMin)
        portStopX = _r(sf * bbCoords.XMax)
        portStopY = _r(sf * bbCoords.YMax)
        portStopZ = _r(sf * bbCoords.ZMax)

        if (self.waveguideRectDir in ["z-"]):
            portStartZ = _r(sf * bbCoords.ZMax)
            portStopZ = _r(sf * bbCoords.ZMin)
        elif (self.waveguideRectDir in ["x-", "r-"]):
            portStartX = _r(sf * bbCoords.XMax)
            portStopX = _r(sf * bbCoords.XMin)
        elif (self.waveguideRectDir in ["y-", "theta-"]):
            portStartY = _r(sf * bbCoords.YMax)
            portStopY = _r(sf * bbCoords.YMin)

        #
        #   Based on port excitation direction which is not used at waveguide due it has modes, but based on that height and width are resolved.
        #
        waveguideWidth = 0
        waveguideHeight = 0
        if (self.direction.startswith("z")):
            waveguideWidth = abs(portStartX - portStopX)
            waveguideHeight = abs(portStartY - portStopY)
        elif (self.direction.startswith(("x", "r"))):
            waveguideWidth = abs(portStartY - portStopY)
            waveguideHeight = abs(portStartZ - portStopZ)
        elif (self.direction.startswith(("y", "theta"))):
            waveguideWidth = abs(portStartX - portStopX)
            waveguideHeight = abs(portStartZ - portStopZ)

        return portStartX, portStartY, portStartZ, portStopX, portStopY, portStopZ, waveguideWidth, waveguideHeight

    def getCoaxialStartStopAndRadius(self, bbCoords, sf):
        portStartX = _r(sf * bbCoords.XMin)
        portStartY = _r(sf * bbCoords.YMin)
        portStartZ = _r(sf * bbCoords.ZMin)
        portStopX = _r(sf * bbCoords.XMax)
        portStopY = _r(sf * bbCoords.YMax)
        portStopZ = _r(sf * bbCoords.ZMax)

        if (self.direction.endswith("-")):
            portStartX = _r(sf * bbCoords.XMax)
            portStartY = _r(sf * bbCoords.YMax)
            portStartZ = _r(sf * bbCoords.ZMax)
            portStopX = _r(sf * bbCoords.XMin)
            portStopY = _r(sf * bbCoords.YMin)
            portStopZ = _r(sf * bbCoords.ZMin)

        # calculate coaxial port radius, it's smaller dimension from width, height
        coaxialDiameter = 0.0
        if (self.direction.startswith("z")):
            coaxialDiameter = min(abs(portStartX - portStopX), abs(portStartY - portStopY))
        elif (self.direction.startswith(("x", "r"))):
            coaxialDiameter = min(abs(portStartY - portStopY), abs(portStartZ - portStopZ))
        elif (self.direction.startswith(("y", "theta"))):
            coaxialDiameter = min(abs(portStartX - portStopX), abs(portStartZ - portStopZ))

        coaxialRadius = coaxialDiameter / 2

        #
        #   Port start and end need to be shifted into middle of feed plane
        #
        if (self.direction.startswith("z")):
            calcPortStartX = (portStartX + portStopX) / 2
            calcPortStartY = (portStartY + portStopY) / 2
            calcPortStartZ = portStartZ
            calcPortStopX = (portStartX + portStopX) / 2
            calcPortStopY = (portStartY + portStopY) / 2
            calcPortStopZ = portStopZ

        elif (self.direction.startswith(("x", "r"))):
            calcPortStartX = portStartX
            calcPortStartY = (portStartY + portStopY) / 2
            calcPortStartZ = (portStartZ + portStopZ) / 2
            calcPortStopX = portStopX
            calcPortStopY = (portStartY + portStopY) / 2
            calcPortStopZ = (portStartZ + portStopZ) / 2

        elif (self.direction.startswith(("y", "theta"))):
            calcPortStartX = (portStartX + portStopX) / 2
            calcPortStartY = portStartY
            calcPortStartZ = (portStartZ + portStopZ) / 2
            calcPortStopX = (portStartX + portStopX) / 2
            calcPortStopY = portStopY
            calcPortStopZ = (portStartZ + portStopZ) / 2

        return calcPortStartX, calcPortStartY, calcPortStartZ, calcPortStopX, calcPortStopY, calcPortStopZ, coaxialRadius

    def getCoaxialInnerRadiusShellThicknessFeedShiftMeasShift(self):
        coaxialInnerRadius = self.coaxialInnerRadiusValue * self.getUnitsAsNumber(self.coaxialInnerRadiusUnits)
        coaxialShellThickness = self.coaxialShellThicknessValue * self.getUnitsAsNumber(self.coaxialShellThicknessUnits)
        coaxialFeedShift = self.coaxialFeedpointShiftValue * self.getUnitsAsNumber(self.coaxialFeedpointShiftUnits)
        coaxialMeasPlaneShift = self.coaxialMeasPlaneShiftValue * self.getUnitsAsNumber(self.coaxialMeasPlaneShiftUnits)

        return coaxialInnerRadius, coaxialShellThickness, coaxialFeedShift, coaxialMeasPlaneShift

    def getCoplanarStartStopAndGapWidthAndEVecStr(self, bbCoords, sf):
        #
        #   1. set all coords to max or min, this means where coplanar waveguide is placed if on top or bottom of object but we don't know orientation now
        #
        portStartX = _r(sf * bbCoords.XMin)
        portStartY = _r(sf * bbCoords.YMin)
        portStartZ = _r(sf * bbCoords.ZMin)
        portStopX = _r(sf * bbCoords.XMax)
        portStopY = _r(sf * bbCoords.YMax)
        portStopZ = _r(sf * bbCoords.ZMax)

        #
        #   2. set coordinates of coplanar based on plane, height must be same
        #
        if (currSetting.direction in ["XY plane, top layer", "r-theta, top layer"]):
            portStartZ = _r(sf * bbCoords.ZMax)
            portStopZ = _r(sf * bbCoords.ZMax)
        elif (currSetting.direction in ["XY plane, bottom layer", "r-theta, bottom layer"]):
            portStartZ = _r(sf * bbCoords.ZMin)
            portStopZ = _r(sf * bbCoords.ZMin)
        elif (currSetting.direction in ["YZ plane, right layer", "z-theta, outside layer"]):
            portStartX = _r(sf * bbCoords.XMax)
            portStopX = _r(sf * bbCoords.XMax)
        elif (currSetting.direction in ["YZ plane, left layer", "z-theta, inside layer"]):
            portStartX = _r(sf * bbCoords.XMin)
            portStopX = _r(sf * bbCoords.XMin)
        elif (currSetting.direction in ["XZ plane, front layer", "z-theta, outside layer"]):
            portStartY = _r(sf * bbCoords.YMax)
            portStopY = _r(sf * bbCoords.YMax)
        elif (currSetting.direction in ["XZ plane, back layer", "z-theta, inside layer"]):
            portStartY = _r(sf * bbCoords.YMin)
            portStopY = _r(sf * bbCoords.YMin)

        #
        #   3. set coplanar direcion based on propagation
        #
        if (currSetting.coplanarPropagation == "z-"):
            portStartZ = _r(sf * bbCoords.ZMax)
            portStopZ = _r(sf * bbCoords.ZMin)
        elif (currSetting.coplanarPropagation in ["x-", "r-"]):
            portStartX = _r(sf * bbCoords.XMax)
            portStopX = _r(sf * bbCoords.XMin)
        elif (currSetting.coplanarPropagation in ["y-", "theta-"]):
            portStartY = _r(sf * bbCoords.YMax)
            portStopY = _r(sf * bbCoords.YMin)
        elif (currSetting.coplanarPropagation == "z+"):
            portStartZ = _r(sf * bbCoords.ZMin)
            portStopZ = _r(sf * bbCoords.ZMax)
        elif (currSetting.coplanarPropagation in ["x+", "r+"]):
            portStartX = _r(sf * bbCoords.XMin)
            portStopX = _r(sf * bbCoords.XMax)
        elif (currSetting.coplanarPropagation in ["y+", "theta+"]):
            portStartY = _r(sf * bbCoords.YMin)
            portStopY = _r(sf * bbCoords.YMax)

        gapWidth = currSetting.coplanarGapValue * currSetting.getUnitsAsNumber(currSetting.coplanarGapUnits)
        gapWidth_freeCAD_units = currSetting.coplanarGapValue * currSetting.getUnitsAsNumber(currSetting.coplanarGapUnits) / self.getFreeCADUnitLength_m()

        if (currSetting.direction.startswith(("XY", "r-theta")) and currSetting.coplanarPropagation.startswith(("x", "r"))):
            coplanarEVecStr = '[0 1 0]'
            portStartY += gapWidth_freeCAD_units
            portStopY -= gapWidth_freeCAD_units
        elif (currSetting.direction.startswith(("XY", "r-theta")) and currSetting.coplanarPropagation.startswith(("y", "theta"))):
            coplanarEVecStr = '[1 0 0]'
            portStartX += gapWidth_freeCAD_units
            portStopX -= gapWidth_freeCAD_units
        elif (currSetting.direction.startswith(("XZ", "z-theta")) and currSetting.coplanarPropagation.startswith(("x", "r"))):
            coplanarEVecStr = '[0 0 1]'
            portStartZ += gapWidth_freeCAD_units
            portStopZ -= gapWidth_freeCAD_units
        elif (currSetting.direction.startswith(("XZ", "z-theta")) and currSetting.coplanarPropagation.startswith("z")):
            coplanarEVecStr = '[1 0 0]'
            portStartX += gapWidth_freeCAD_units
            portStopX -= gapWidth_freeCAD_units
        elif (currSetting.direction.startswith(("XZ", "z-theta")) and currSetting.coplanarPropagation.startswith(("y", "theta"))):
            coplanarEVecStr = '[0 0 1]'
            portStartZ += gapWidth_freeCAD_units
            portStopZ -= gapWidth_freeCAD_units
        elif (currSetting.direction.startswith(("XZ", "z-theta")) and currSetting.coplanarPropagation.startswith("z")):
            coplanarEVecStr = '[0 1 0]'
            portStartY += gapWidth_freeCAD_units
            portStopY -= gapWidth_freeCAD_units
        else:
            coplanarEVecStr = None

        return portStartX, portStartY, portStartZ, portStopX, portStopY, portStopZ, gapWidth, coplanarEVecStr

    def getStriplineStartStopAndHeight(self, bbCoords, sf):
        portStartX = _r(sf * (bbCoords.XMin + bbCoords.XMax) / 2)
        portStartY = _r(sf * (bbCoords.YMin + bbCoords.YMax) / 2)
        portStartZ = _r(sf * (bbCoords.ZMin + bbCoords.ZMax) / 2)
        portStopX = _r(sf * (bbCoords.XMin + bbCoords.XMax) / 2)
        portStopY = _r(sf * (bbCoords.YMin + bbCoords.YMax) / 2)
        portStopZ = _r(sf * (bbCoords.ZMin + bbCoords.ZMax) / 2)

        if (self.striplinePropagation in ["x+", "y+", "r+", "theta+"] and self.direction in ["XY plane", "r-theta plane"]):
            portStartX = _r(sf * bbCoords.XMin)
            portStopX = _r(sf * bbCoords.XMax)
            portStartY = _r(sf * bbCoords.YMin)
            portStopY = _r(sf * bbCoords.YMax)
        elif (self.striplinePropagation in ["x+", "z+", "r+"] and self.direction == "XZ plane"):
            portStartX = _r(sf * bbCoords.XMin)
            portStopX = _r(sf * bbCoords.XMax)
            portStartZ = _r(sf * bbCoords.ZMin)
            portStopZ = _r(sf * bbCoords.ZMax)
        elif (self.striplinePropagation in ["y+", "z+", "theta+"] and self.direction == "YZ plane"):
            portStartY = _r(sf * bbCoords.YMin)
            portStopY = _r(sf * bbCoords.YMax)
            portStartZ = _r(sf * bbCoords.ZMin)
            portStopZ = _r(sf * bbCoords.ZMax)
        elif (self.striplinePropagation in ["x-", "y-", "r-", "theta-"] and self.direction == "XY plane"):
            portStartX = _r(sf * bbCoords.XMax)
            portStopX = _r(sf * bbCoords.XMin)
            portStartY = _r(sf * bbCoords.YMax)
            portStopY = _r(sf * bbCoords.YMin)
        elif (self.striplinePropagation in ["x-", "z-", "r-"] and self.direction == "XZ plane"):
            portStartX = _r(sf * bbCoords.XMax)
            portStopX = _r(sf * bbCoords.XMin)
            portStartZ = _r(sf * bbCoords.ZMax)
            portStopZ = _r(sf * bbCoords.ZMin)
        elif (self.striplinePropagation in ["y-", "z-", "theta-"] and self.direction == "YZ plane"):
            portStartY = _r(sf * bbCoords.YMax)
            portStopY = _r(sf * bbCoords.YMin)
            portStartZ = _r(sf * bbCoords.ZMax)
            portStopZ = _r(sf * bbCoords.ZMin)

        striplineHeight = 0
        if (self.direction == "YZ plane"):
            striplineHeight = _r(sf * (bbCoords.XMax - bbCoords.XMin) / 2)
        elif (self.direction == "XZ plane"):
            striplineHeight = _r(sf * (bbCoords.YMax - bbCoords.YMin) / 2)
        elif (self.direction == "XY plane"):
            striplineHeight = _r(sf * (bbCoords.ZMax - bbCoords.ZMin) / 2)

        return portStartX, portStartY, portStartZ, portStopX, portStopY, portStopZ, striplineHeight

    def getCurveStartStop(self, bbCoords, sf):
        if (_bool(self.direction) == False):
            portStartX = _r(sf * bbCoords.XMin)
            portStartY = _r(sf * bbCoords.YMin)
            portStartZ = _r(sf * bbCoords.ZMin)
            portStopX = _r(sf * bbCoords.XMax)
            portStopY = _r(sf * bbCoords.YMax)
            portStopZ = _r(sf * bbCoords.ZMax)
        else:
            portStartX = _r(sf * bbCoords.XMax)
            portStartY = _r(sf * bbCoords.YMax)
            portStartZ = _r(sf * bbCoords.ZMax)
            portStopX = _r(sf * bbCoords.XMin)
            portStopY = _r(sf * bbCoords.YMin)
            portStopZ = _r(sf * bbCoords.ZMin)

        return portStartX, portStartY, portStartZ, portStopX, portStopY, portStopZ


