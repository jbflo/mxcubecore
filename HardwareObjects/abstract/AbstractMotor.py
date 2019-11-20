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
#  You should have received a copy of the GNU General Lesser Public License
#  along with MXCuBE.  If not, see <http://www.gnu.org/licenses/>.

from warnings import warn
from HardwareRepository.BaseHardwareObjects import HardwareObject


class MotorStates(object):
    """Enumeration of the motor states
    """

    INITIALIZING = 0
    ON = 1
    OFF = 2
    READY = 3
    BUSY = 4
    MOVING = 5
    STANDBY = 6
    DISABLED = 7
    UNKNOWN = 8
    ALARM = 9
    FAULT = 10
    INVALID = 11
    OFFLINE = 12
    LOWLIMIT = 13
    HIGHLIMIT = 14
    NOTINITIALIZED = 15
    MOVESTARTED = 16
    UNUSABLE = 17
    ONLIMIT = 18

    STATE_DESC = {
        INITIALIZING: "Initializing",
        ON: "On",
        OFF: "Off",
        READY: "Ready",
        BUSY: "Busy",
        MOVING: "Moving",
        STANDBY: "Standby",
        DISABLED: "Disabled",
        UNKNOWN: "Unknown",
        ALARM: "Alarm",
        FAULT: "Fault",
        INVALID: "Invalid",
        OFFLINE: "Offline",
        LOWLIMIT: "LowLimit",
        HIGHLIMIT: "HighLimit",
        NOTINITIALIZED: "NotInitialized",
        MOVESTARTED: "MoveStarted",
        UNUSABLE: "Unusable",
        ONLIMIT: "OnLimit"
    }

    DESC_TO_STATE = {
        "Initializing": INITIALIZING,
        "On": ON,
        "Off": OFF,
        "Ready": READY,
        "Busy": BUSY,
        "Moving": MOVING,
        "Standby": STANDBY,
        "Disabled": DISABLED,
        "Unknown": UNKNOWN,
        "Alarm": ALARM,
        "Fault": FAULT,
        "Invalid": INVALID,
        "Offline": OFFLINE,
        "LowLimit": LOWLIMIT,
        "HighLimit": HIGHLIMIT,
        "NotInitialized": NOTINITIALIZED,
        "MoveStarted": MOVESTARTED,
        "Unusable": UNUSABLE,
        "OnLimit": ONLIMIT
    }

    @staticmethod
    def tostring(state):
        return MotorStates.STATE_DESC.get(state, "Unknown")

    @staticmethod
    def fromstring(state_str):
        for key, value in MotorStates.STATE_DESC.items():
            if value == state_str:
                return key
        return MotorStates.STATE_DESC[MotorStates.UNKNOWN]


class AbstractMotor(HardwareObject):
    def __init__(self, name):
        HardwareObject.__init__(self, name)

        self.motor_name = ""
        self.motor_states = MotorStates()
        self.__state = self.motor_states.INITIALIZING
        self.__position = None
        self.__limits = (None, None)
        self.__default_limits = (None, None)
        self.__velocity = None

    def home_motor(self, timeout=None):
        """ Motor homing sequence """
        pass

    def home(self, timeout=None):
        self.home_motor(timeout)

    def get_motor_mnemonic(self):
        return self.motor_name

    def is_ready(self):
        """ Check if the motor state is READY
        Returns:
            bool: True if ready, otherwise False
        """
        return self.__state == self.motor_states.READY

    def set_ready(self, task=None):
        """Sets motor state to ready"""
        self.set_state(self.motor_states.READY)

    def get_state(self):
        """Returns motor state

        Returns:
            str: Motor state.
        """
        return self.__state

    def set_state(self, state):
        """Sets motor state

        Args:
            state (str): motor state
        """
        self.__state = state
        self.emit("stateChanged", (state,))

    def get_position(self):
        """Read the motor user position.

        Returns:
            float: Motor position.
        """
        return self.__position

    def set_position(self, position):
        """Sets the motor position.

        Keyword Args:
            state (str): motor state
        """
        self.__position = position
        self.emit("positionChanged", (position,))

    def get_limits(self):
        """Returns motor limits as (float, float)

        Returns:
            tuple: limits as two floats tuple
        """
        return self.__limits

    def set_limits(self, limits):
        """Set motor limits

        Args:
            limits(tuple): two floats tuple
        """
        self.__limits = limits
        self.emit("limitsChanged", (limits,))

    def get_velocity(self):
        """Returns motor velocity

        Returns:
            float: velocity
        """
        return self.__velocity

    def set_velocity(self, velocity):
        """Set the motor velocity

        Args:
            velocity (float): target velocity
        """
        self.__velocity = velocity

    def move(self, position, wait=False, timeout=None):
        """Move motor to absolute position.
        Args:
            position (float): target position
        Kwargs:
            wait (bool): optional wait till motor finishes the movement
            timeout (float): optional seconds to wait till move finishes
        """
        return

    def move_relative(self, relative_position, wait=False, timeout=None):
        """Move to relative position. Wait the move to finish (True/False)
        Args:
            relative_position (float): relative position to be moved by
        Kwargs:
            wait (bool): optional wait till motor finishes the movement
            timeout (float): optional seconds to wait till move finishes
        """
        self.move(self.get_position() + relative_position, wait, timeout)

    def stop(self):
        """Stop the motor movement
        """
        return

    def update_values(self):
        self.emit("stateChanged", (self.get_state(),))
        self.emit("positionChanged", (self.get_position(),))
        self.emit("limitsChanged", (self.get_limits(),))

    """ obsolete, keep for backward compatibility """

    def isReady(self):
        warn("isReady is deprecated. Use is_ready instead", DeprecationWarning)
        return self.is_ready()

    def getPosition(self):
        warn("getPosition is deprecated. Use get_position instead", DeprecationWarning)
        return self.get_position()

    def getState(self):
        warn("getState is deprecated. Use get_state instead", DeprecationWarning)
        return self.get_state()

    def getLimits(self):
        warn("getLimits is deprecated. Use get_limits instead", DeprecationWarning)
        return self.get_limits()

    def getMotorMnemonic(self):
        warn(
            "getMotorMnemonic is deprecated. Use get_motor_mnemonic instead",
            DeprecationWarning,
        )
        return self.get_motor_mnemonic()

    def syncMove(self, position, timeout=None):
        warn("syncMove is deprecated. Use move wait=True instead", DeprecationWarning)
        self.move(position, wait=True, timeout=timeout)

    def moveRelative(self, relative_position, wait=False, timeout=None):
        warn(
            "moveRelative is deprecated. Use move_relative instead", DeprecationWarning
        )
        self.move_relative(relative_position, wait, timeout)

    def syncMoveRelative(self, position, timeout=None):
        warn(
            "syncMoveRelative is deprecated. Use move_relative wait=True instead",
            DeprecationWarning,
        )
        self.move_relative(position, wait=True, timeout=timeout)

    def homeMotor(self, timeout=None):
        warn("homeMotor is deprecated. Use home_motor instead", DeprecationWarning)
        self.home_motor(timeout)