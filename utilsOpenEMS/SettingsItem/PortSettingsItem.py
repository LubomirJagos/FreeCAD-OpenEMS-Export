from .  SettingsItem import SettingsItem

# Port settings
#	There are just few types of ports defined in OpenEMS:
#		- lumped
#		- microstrip
#		- circular waveguide
#		- rectangular waveguide
class PortSettingsItem(SettingsItem):
    def __init__(self, name="", type="", R=0, RUnits="", isActive=False, direction="z",
                 lumpedExcitationAmplitude=0,
                 mslFeedShiftValue="", mslFeedShiftUnits="", mslMeasPlaneShiftValue="", mslMeasPlaneShiftUnits="", mslMaterial="", mslPropagation="",
                 waveguideRectDir = "", waveguideCircDir="",
                 coaxialConductorMaterial = "", coaxialMaterial = "", coaxialPropagation = "", coaxialInnerRadiusValue = 0, coaxialInnerRadiusUnits = "", coaxialShellThicknessValue = 0, coaxialShellThicknessUnits = "", coaxialFeedpointShiftValue = 0, coaxialFeedpointShiftUnits = "", coaxialMeasPlaneShiftValue = 0, coaxialMeasPlaneShiftUnits = "", coaxialExcitationAmplitude = 0,
                 coplanarMaterial = "", coplanarPropagation = "", coplanarGapValue = 0, coplanarGapUnits = "", coplanarFeedpointShiftValue = 0, coplanarFeedpointShiftUnits = "", coplanarMeasPlaneShiftValue = 0, coplanarMeasPlaneShiftUnits = "",
                 striplineMaterial = "", striplinePropagation = "", striplineHeightValue = 0, striplineHeightUnits = "", striplineFeedpointShiftValue = 0, striplineFeedpointShiftUnits = "", striplineMeasPlaneShiftValue = 0, striplineMeasPlaneShiftUnits = "",
                 probeType="", probeDomain="", probeFrequencyList=[],
                 dumpboxType="", dumpboxDomain="", dumpboxFileType="", dumpboxFrequencyList=[]
                 ):
        self.name = name
        self.type = type

        self.R = R
        self.RUnits = RUnits
        self.isActive = isActive
        self.direction = direction

        self.lumpedExcitationAmplitude = lumpedExcitationAmplitude

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
        self.coaxialExcitationAmplitude = coaxialExcitationAmplitude

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

        self.probeType = probeType
        self.probeDomain = probeDomain
        self.probeFrequencyList = probeFrequencyList

        self.dumpboxType = dumpboxType
        self.dumpboxDomain = dumpboxDomain
        self.dumpboxFileType = dumpboxFileType
        self.dumpboxFrequencyList = dumpboxFrequencyList

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


