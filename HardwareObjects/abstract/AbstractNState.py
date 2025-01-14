#
#  Project: MXCuBE
#  https://github.com/mxcube.
#
#  This file is part of MXCuBE software.
#
#  MXCuBE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  MXCuBE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with MXCuBE.  If not, see <http://www.gnu.org/licenses/>.

"""
Defines the interface for N state devices
"""

import abc
import ast
from enum import Enum, unique
from HardwareRepository.HardwareObjects.abstract.AbstractActuator import (
    AbstractActuator,
)


__copyright__ = """ Copyright 2020 by the MXCuBE collaboration """
__license__ = "LGPLv3+"


@unique
class BaseValueEnum(Enum):
    """defines only the compulsory unknown."""

    UNKNOWN = "UNKNOWN"


class AbstractNState(AbstractActuator):
    """
    Abstract base class for N state objects.
    """

    __metaclass__ = abc.ABCMeta
    VALUES = BaseValueEnum

    def __init__(self, name):
        AbstractActuator.__init__(self, name)

    def init(self):
        """Initilise the predefined values"""
        AbstractActuator.init(self)
        self.initialise_values()

    def validate_value(self, value):
        """Check if the value is within the predefined values.
        Args:
            value(Enum): value to check
        Returns:
            (bool): True if within the values.
        """
        return value in self.VALUES

    def set_limits(self, limits):
        """Set the low and high limits.
        Args:
            limits (tuple): two element (low limit, high limit) tuple.
        """
        raise NotImplementedError

    def update_limits(self, limits=None):
        """Check if the limits have changed. Emits signal limitsChanged.
        Args:
            limits(tuple): two element (low limit, high limit) tuple.
        """
        raise NotImplementedError

    def initialise_values(self):
        """Initialise the ValueEnum with the values from the config.
        """
        try:
            values = ast.literal_eval(self.getProperty("values"))
            self.VALUES = Enum(
                "ValueEnum",
                dict(values, **{item.name: item.value for item in BaseValueEnum}),
            )
        except (ValueError, TypeError):
            pass

    def value_to_enum(self, value):
        """Tranform a value to Enum
        Args:
           value(str, int, float, tuple): value
        Returns:
            (Enum): Enum member, corresponding to the value or UNKNOWN.
        """
        for enum_var in self.VALUES.__members__.values():
            if value == enum_var.value:
                return enum_var
            if isinstance(enum_var.value, tuple) and value == enum_var.value[0]:
                return enum_var

        return self.VALUES.UNKNOWN
