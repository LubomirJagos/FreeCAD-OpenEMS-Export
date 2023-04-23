from .SettingsItem import SettingsItem

# Excitation settings, for input power where energy is floating into model
#	Sinusodial - input port is excitated by sinusodial electric field
#	Gaussian   - gaussian impulse at input port
#	Custom     - user has to define function of electric field at input port
#

class ExcitationSettingsItem(SettingsItem):
	def __init__(self, name="", type="", sinusodial=None, gaussian=None, custom=None, units = "Hz"):
		SettingsItem.__init__(self)
		self.name = name
		self.type = type
		self.sinusodial = {'f0': 0} if sinusodial is None else sinusodial
		self.gaussian = {'f0': 0, 'fc': 0} if gaussian is None else gaussian
		self.custom = {'functionStr': '0', 'f0': 0} if custom is None else custom
		self.units = units
		return

	def getType(self):
		return self.type

