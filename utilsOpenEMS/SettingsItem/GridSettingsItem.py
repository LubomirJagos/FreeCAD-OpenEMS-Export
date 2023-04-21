from .SettingsItem import SettingsItem

# Grid settings class
#	Fixed Count    - fixed number per axes
#	Fixed Distance - gridlines have fixed distance between them
#	User Defined   - user has to provide coordinates where lines should be
#
class GridSettingsItem(SettingsItem):
    def __init__(self, name="", type="", fixedCount={'x': 0, 'y': 0, 'z': 0}, fixedDistance={'x': 0, 'y': 0, 'z': 0},
                 userDefined={'data': ""}, units="", xenabled=False, yenabled=False, zenabled=False,
                 smoothMeshDefault={'xMaxRes': 0, 'yMaxRes': 0, 'zMaxRes': 0},
                 coordsType='rectangular'):
        self.name = name
        self.type = type
        self.coordsType = coordsType
        self.units = units
        self.xenabled = xenabled
        self.yenabled = yenabled
        self.zenabled = zenabled
        self.fixedCount = fixedCount
        self.fixedDistance = fixedDistance
        self.smoothMesh = smoothMeshDefault
        self.userDefined = userDefined
        self.generateLinesInside = False
        self.topPriorityLines = True


    # Return xyz distances, count or user defined array based what user asked for.
    def getXYZ(self, referenceUnit=1):
        if (self.type == "Fixed Count"):
            return self.fixedCount
        if (self.type == "Fixed Distance"):
            dict_mult = lambda d, x: {n: d[n] * x for n in d.keys()}
            return dict_mult(self.fixedDistance, self.getUnitsAsNumber(self.units) / referenceUnit)
        if (self.type == "User Defined"):
            return self.userDefined['data']
        if (self.type == "Smooth Mesh"):
            return self.smoothMesh

    def getUnitAsScriptLine(self):
        return str(self.getUnitsAsNumber(self.units))

    def getSettingsUnitAsNumber(self):
        """
        :return: Self units as float number, ie.:
                mm -> 1.0e-3
                m  -> 1.0
        """
        return self.getUnitsAsNumber(self.units)

