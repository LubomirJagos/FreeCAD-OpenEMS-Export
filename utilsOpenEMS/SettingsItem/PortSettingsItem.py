from .  SettingsItem import SettingsItem

# Port settings
#	There are just few types of ports defined in OpenEMS:
#		- lumped
#		- microstrip
#		- circular waveguide
#		- rectangular waveguide
class PortSettingsItem(SettingsItem):
    def __init__(self, name="", type="", R=0, RUnits="", isActive=False, direction="z", mslPropagation="x",
                 mslFeedShift="", mslMeasPlaneShift=""):
        self.name = name
        self.type = type
        self.R = R
        self.RUnits = RUnits
        self.isActive = isActive
        self.mslPropagation = mslPropagation
        self.direction = direction
        self.mslFeedShift = mslFeedShift
        self.mslMeasPlaneShift = mslMeasPlaneShift
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
            jsonString += ", 'mslPropagation': " + self.mslPropagation
            jsonString += ", 'mslFeedShift': " + self.mslFeedShift
            jsonString += ", 'mslMeasPlaneShift': " + self.mslMeasPlaneShift
        if (self.type == "circular waveguide"):
            jsonString += ", 'type': 'circular waveguide'"
        if (self.type == "rectangular waveguide"):
            jsonString += ", 'type': 'rectangular waveguide'"
        if (self.type == "nf2ff box"):
            jsonString += ", 'type': 'nf2ff box'"
        jsonString += "}"
        return jsonString

    def getRUnits(self):
        return self.getUnitsAsNumber(self.RUnits)


