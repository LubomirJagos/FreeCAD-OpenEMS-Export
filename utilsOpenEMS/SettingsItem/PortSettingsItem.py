from .  SettingsItem import SettingsItem

# Port settings
#	There are just few types of ports defined in OpenEMS:
#		- lumped
#		- microstrip
#		- circular waveguide
#		- rectangular waveguide
class PortSettingsItem(SettingsItem):
    def __init__(self, name="", type="", R=0, RUnits="", isActive=False, direction="z",
                 mslFeedShiftValue="", mslFeedShiftUnits="", mslMeasPlaneShiftValue="", mslMeasPlaneShiftUnits="", mslMaterial="", mslPropagation="",
                 waveguideRectDir = ""):
        self.name = name
        self.type = type
        self.R = R
        self.RUnits = RUnits
        self.isActive = isActive
        self.direction = direction
        self.mslFeedShiftValue = mslFeedShiftValue
        self.mslFeedShiftUnits = mslFeedShiftUnits
        self.mslMeasPlaneShiftValue = mslMeasPlaneShiftValue
        self.mslMeasPlaneShiftUnits = mslMeasPlaneShiftUnits
        self.mslMaterial = mslMaterial
        self.mslPropagation = mslPropagation
        self.waveguideRectDir = waveguideRectDir
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


