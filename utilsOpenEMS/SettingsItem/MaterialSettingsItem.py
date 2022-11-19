from .SettingsItem import SettingsItem

# Material settings, basic are epsilon and mue, kappa and sigma are extended
#	epsilon - permitivity
#	mue     - permeability
#	kappa   - susceptibility, coupling coefficient
#	sigma   - VSWR, coductivity, surface charfe
#
class MaterialSettingsItem(SettingsItem):
    def __init__(self, name="", type="", constants={'epsilon': 1.0, 'mue': 1.0, 'kappa': 0.0, 'sigma': 0.0}):
        self.name = name
        self.type = type
        self.constants = constants

# def getAllItems(self):
#	return super(MaterialSettingItem, self).getAllItems()

