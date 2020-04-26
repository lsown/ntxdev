#simulation of drv8830 for non-local hardware

#from i2cdevice import Device, Register, BitField
#from i2cdevice.adapter import Adapter, LookupAdapter
from collections import namedtuple

__version__ = '0.0.1'

I2C_ADDR1 = 0x60  # Default, both select jumpers bridged (not cut)
I2C_ADDR2 = 0x61  # Cut A0
I2C_ADDR3 = 0x63  # Cut A1
I2C_ADDR4 = 0x64  # Cut A0 and A1


class BitField():
	"""Store information about a field or flag in an i2c register"""
	def __init__(self, name, mask, adapter=None, bit_width=8, read_only=False):
		self.name = name
		self.mask = mask
		self.adapter = adapter
		self.bit_width = bit_width
		self.read_only = read_only

class Adapter:
	"""
	Must implement `_decode()` and `_encode()`.
	"""
	def _decode(self, value):
		raise NotImplementedError

	def _encode(self, value):
		raise NotImplementedError


class LookupAdapter(Adapter):
	"""Adaptor with a dictionary of values.
	:param lookup_table: A dictionary of one or more key/value pairs where the key is the human-readable value and the value is the bitwise register value
	"""
	def __init__(self, lookup_table, snap=True):
		self.lookup_table = lookup_table
		self.snap = snap

	def _decode(self, value):
		for k, v in self.lookup_table.items():
			if v == value:
				return k
		raise ValueError("{} not in lookup table".format(value))

	def _encode(self, value):
		if self.snap and type(value) in [int, float]:
			value = min(list(self.lookup_table.keys()), key=lambda x: abs(x - value))
		return self.lookup_table[value]

class VoltageAdapter(Adapter):
	# Calculation is ostensibly 4 * 1.285V (vref) * (vset + 1) / 64
	# But appears closer to round(4 * 1.285 * i / 64.0 + 0.0001, 2)
	# Then the datasheet goes on to detail individual voltages that
	# neither of these formulae round consistently to.
	# So we'll take some liberties with them instead.
	def _decode(self, i):  # index to voltage
		if i <= 5:
			return 0
		offset = 0.01 if i >= 16 else 0
		offset += 0.01 if i >= 48 else 0
		return round(offset + i * 0.08, 2)

	def _encode(self, v):  # voltage to index
		if v < 0.48:
			return 0
		offset = -0.01 if v >= 1.29 else 0
		offset -= 0.01 if v >= 3.86 else 0
		return int(offset + v / 0.08)

class Register():
	"""Store information about an i2c register"""
	def __init__(self, name, address, fields=None, bit_width=8, read_only=False, volatile=True):
		self.name = name
		self.address = address
		self.bit_width = bit_width
		self.read_only = read_only
		self.volatile = volatile
		self.is_read = False
		self.fields = {}

		for field in fields:
			self.fields[field.name] = field

		self.namedtuple = namedtuple(self.name, sorted(self.fields))
		 
class Device:
		#self.CONtuple = namedtuple('CONTROL', 'direction out1 out2 voltage')
		#self.FAULTtuple = namedtuple('FAULT', 'clear current_limit fault over_current over_temperature under_voltage')
		#self.CONTROL = self.CONtuple(direction = 'simfwd', out1=1, out2=1, voltage=3)
		#self.FAULT = self.FAULTtuple('FAULT', 'clear current_limit fault over_current over_temperature under_voltage')
		#self.registers{'CONTROL' : }


	def __init__(self, i2c_address, i2c_dev=None, bit_width=8, registers=None):
		self._bit_width = bit_width

		self.locked = {}
		self.registers = {}
		self.values = {}

		if type(i2c_address) is list:
			self._i2c_addresses = i2c_address
			self._i2c_address = i2c_address[0]
		else:
			self._i2c_addresses = [i2c_address]
			self._i2c_address = i2c_address

		for register in registers:
			self.locked[register.name] = False
			self.values[register.name] = 0
			self.registers[register.name] = register
			self.__dict__[register.name] = _RegisterProxy(self, register)

class Devicesim:
	def __init__(self):
		self.CONtuple = namedtuple('CONTROL', 'direction out1 out2 voltage')
		self.FAULTtuple = namedtuple('FAULT', 'clear current_limit fault over_current over_temperature under_voltage')
		self.CONTROL = self.CONtuple(direction = 'simfwd', out1=1, out2=1, voltage=3)
		#self.FAULT = self.FAULTtuple('FAULT', 'clear current_limit fault over_current over_temperature under_voltage')

	def get(self, register):
		"""Get a namedtuple containing register fields.
		:param register: Name of register to retrieve
		"""
		result = {}
		self.read_register(register)
		self.lock_register(register)
		for field in self.registers[register].fields:
			result[field] = self.get_field(register, field)
		self.unlock_register(register)
		return self.registers[register].namedtuple(**result)


class DRV8830:
	def __init__(self, i2c_addr=I2C_ADDR1, i2c_dev=None):
		self._i2c_addr = i2c_addr
		self._i2c_dev = i2c_dev
		self._drv8830 = Device([I2C_ADDR1, I2C_ADDR2, I2C_ADDR3, I2C_ADDR4], i2c_dev=self._i2c_dev, 
			registers=(Devicesim.CONTROL)
			,
			Register('FAULT', 0x01, fields=(
				BitField('clear', 0b10000000),			 # Clears fault status bits when written to 1
				BitField('current_limit', 0b00010000),	 # Fault caused by external current limit
				BitField('over_temperature', 0b00001000),  # Fault caused by over-temperature condition
				BitField('under_voltage', 0b00000100),	 # Fault caused by undervoltage lockout
				BitField('over_current', 0b00000010),	  # Fault caused by overcurrent event
				BitField('fault', 0b00000001)			  # Fault condition exists
			))
		))

		#self._drv8830.select_address(self._i2c_addr)

	def select_i2c_address(self, i2c_addr):
		self._i2c_addr = i2c_addr
		self._drv8830.select_address(self._i2c_addr)

	def set_outputs(self, out1, out2):
		self._drv8830.set('CONTROL', out1=out1, out2=out2)

	def brake(self):
		self.set_direction('brake')

	def coast(self):
		self.set_direction('coast')

	def forward(self):
		self.set_direction('forward')

	def reverse(self):
		self.set_direction('reverse')

	def set_direction(self, direction):
		"""Set the motor driver direction.
		Basically does the same thing as set_outputs, but takes
		a string name for directione, one of: coast, reverse,
		forward or brake.
		:param direction: string name of direction: coast, reverse, forward or brake
		"""
		self._drv8830.set('CONTROL', direction=direction)

	def set_voltage(self, voltage):
		"""Set the motor driver voltage.
		Roughly corresponds to motor speed depending upon the characteristics of your motor.
		:param voltage: from 0.48v to 5.06v
		"""
		self._drv8830.set('CONTROL', voltage=voltage)

	def get_voltage(self):
		return self._drv8830.get('CONTROL').voltage

	def get_fault(self):
		"""Get motor driver fault information.
		Returns a namedtuple of the fault flags:
		current_limit - external current limit exceeded (ilimit resistor), must clear fault or disable motor to reactivate
		over_temperature - driver has overheated, device resumes once temperature has dropped
		under_voltage - driver is below operating voltage (brownout), resumes once voltage has stabalised
		over_current - over-current protection activated, device disabled, must clear fault to reactivate
		fault - one or more fault flags is set
		"""
		return self._drv8830.get('FAULT')

	def clear_fault(self):
		self._drv8830.set('FAULT', clear=True)
