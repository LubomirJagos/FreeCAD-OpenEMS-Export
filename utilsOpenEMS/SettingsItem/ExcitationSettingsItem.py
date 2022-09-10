from .SettingsItem import SettingsItem

# Excitation settings, for input power where energy is floating into model
#	Sinusodial - input port is excitated by sinusodial electric field
#	Gaussian   - gaussian impulse at input port
#	Custom     - user has to define function of electric field at input port
#

class ExcitationSettingsItem(SettingsItem):
	def __init__(self, name = "", type = "", sinusodial = {'f0': 0}, gaussian = {'f0': 0, 'fc': 0}, custom = {'functionStr': '0', 'f0': 0}, units = "Hz"):
		SettingsItem.__init__(self)
		self.name = name
		self.type = type
		self.sinusodial = sinusodial
		self.gaussian = gaussian
		self.custom = custom
		self.units = units
		return

	def getType(self):
		return self.type

