#  Project: MXCuBE
#  https://github.com/mxcube.
#
#  This file is part of MXCuBE software.
#
#  MXCuBE is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  MXCuBE is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with MXCuBE.  If not, see <http://www.gnu.org/licenses/>.
"""

--------------------------------------------
Description
--------------------------------------------

AbstractSampleChanger is a base class to help in the implementation of
Hardware Objects for SampleChangers following the
"SampleChanger Standard Interface".

If this class is used as base class a standard class is then provided for
its use by generic bricks or by MXCuBE itself.  This class exposes the
following API for bricks and MXCuBE:

--------------------------------------------
SampleChanger - Standard Interface
--------------------------------------------

Sample Changer States
----------------------

    SampleChangerState.Unknown
    SampleChangerState.Ready
    SampleChangerState.Loaded
    SampleChangerState.Loading
    SampleChangerState.Unloading
    SampleChangerState.Selecting
    SampleChangerState.Scanning
    SampleChangerState.Resetting
    SampleChangerState.Charging
    SampleChangerState.Moving
    SampleChangerState.ChangingMode
    SampleChangerState.StandBy
    SampleChangerState.Disabled
    SampleChangerState.Alarm
    SampleChangerState.Fault
    SampleChangerState.Initializing
    SampleChangerState.Closing

Commands
----------------------

load()
unload()
select()
abort()
change_mode()

get_state()
get_status()
is_ready()
wait_ready()
has_loaded_sample()
get_loaded_sample()

Specifying sample locations
-----------------------------
The sample model in a sample changer is based
in the model:
   SampleChanger
      Container
         [Container...]
            Sample

Typically for a sample changer with Pucks and Sample
there is a single level for Container. Specifying
a sample location will consist in giving the puck (basket)
number followed by the sample number. In the location
example `3:5` the fifth sample in the third puck is specified.

For other more complex constructions (for example for
a plate manipulator) each nested container will be specified
until getting to the sample:

In the example for a location in a plate manipulator like `1:5:2`
the location specifies first plate well, fifth drop, second crystal.


Events emitted
----------------------

SampleChanger.STATE_CHANGED_EVENT
SampleChanger.STATUS_CHANGED_EVENT
SampleChanger.INFO_CHANGED_EVENT
SampleChanger.LOADED_SAMPLE_CHANGED_EVENT
SampleChanger.SELECTION_CHANGED_EVENT
SampleChanger.TASK_FINISHED_EVENT

Tools for SC Classes
----------------------

- useUpdateTimer (xml property):
   This property can accept a boolean value (True/False)

   If this property is set the HardwareObject will
   poll itself for state changes, information change and
   other needed values.

   Include a line like `<useUpdateTimer>True</useUpdateTimer`
   in the xml file



--------------------------------------------
How to implement derived SC Classes
--------------------------------------------

"""

import abc
import logging
import time
import gevent
import types


from HardwareRepository.TaskUtils import task
from HardwareRepository.BaseHardwareObjects import HardwareObject
from HardwareRepository.HardwareObjects.abstract.sample_changer.Container import (
    Container,
    Sample,
)


class SampleChangerState:
    """
    Enumeration of sample changer states
    """

    Unknown = 0
    Ready = 1
    Loaded = 2
    Loading = 3
    Unloading = 4
    Selecting = 5
    Scanning = 6
    Resetting = 7
    Charging = 8
    Moving = 9
    ChangingMode = 10
    StandBy = 11
    Disabled = 12
    Alarm = 13
    Fault = 14
    Initializing = 15
    Closing = 16

    STATE_DESC = {
        Ready: "Ready",
        Loaded: "Loaded",
        Alarm: "Alarm",
        Charging: "Charging",
        Disabled: "Disabled",
        Fault: "Fault",
        Loading: "Loading",
        Resetting: "Resetting",
        Scanning: "Scanning",
        Selecting: "Selecting",
        Unloading: "Unloading",
        Moving: "Moving",
        ChangingMode: "Changing Mode",
        StandBy: "StandBy",
        Initializing: "Initializing",
        Closing: "Closing",
    }

    @staticmethod
    def tostring(state):
        return SampleChangerState.STATE_DESC.get(state, "Unknown")


class SampleChangerMode:
    """
    Enumeration of sample changer operating modes
    """

    Unknown = 0
    Normal = 1
    Charging = 8
    Disabled = 11


class SampleChanger(Container, HardwareObject):
    """
    Abstract base class for sample changers
    """

    __metaclass__ = abc.ABCMeta

    # ########################    EVENTS    #########################
    STATE_CHANGED_EVENT = "stateChanged"
    STATUS_CHANGED_EVENT = "statusChanged"
    INFO_CHANGED_EVENT = "infoChanged"
    LOADED_SAMPLE_CHANGED_EVENT = "loadedSampleChanged"
    SELECTION_CHANGED_EVENT = "selectionChanged"
    TASK_FINISHED_EVENT = "taskFinished"
    CONTENTS_UPDATED_EVENT = "contentsUpdated"

    def __init__(self, type, scannable, *args, **kwargs):
        super(SampleChanger, self).__init__(type, None, type, scannable)
        if len(args) == 0:
            args = (type,)
        HardwareObject.__init__(self, *args, **kwargs)
        self.state = -1
        self.status = ""
        self._set_state(SampleChangerState.Unknown)
        self.task = None
        self.task_proc = None
        self.task_error = None
        self._transient = False
        self._token = None
        self._timer_update_inverval = 5  # interval in periods of 100 ms
        self._timer_update_counter = 0

    def init(self):
        use_update_timer = self.getProperty("useUpdateTimer")

        if use_update_timer is None:
            use_update_timer = True

        logging.getLogger("HWR").info(
            "SampleChanger: Using update timer is %s " % use_update_timer
        )

        if use_update_timer:
            task1s = self.__timer_1s_task(wait=False)
            task1s.link(self._on_timer_1s_exit)
            updateTask = self.__update_timer_task(wait=False)
            updateTask.link(self._on_timer_update_exit)

        self.use_update_timer = use_update_timer

        self.update_info()

    def _on_timer_1s_exit(self, task):
        logging.warning("Exiting Sample Changer 1s timer task")

    def _on_timer_update_exit(self, task):
        logging.warning("Exiting Sample Changer update timer task")

    @task
    def __timer_1s_task(self, *args):
        while True:
            gevent.sleep(1.0)
            try:
                if self.is_enabled():
                    self._on_timer_1s()
            except BaseException:
                pass

    @task
    def __update_timer_task(self, *args):
        while True:
            gevent.sleep(0.1)
            try:
                if self.is_enabled():
                    self._timer_update_counter += 1
                    if self._timer_update_counter >= self._timer_update_counter:
                        self._on_timer_update()
                        self._timer_update_counter = 0
            except BaseException:
                pass

    # ########################    TIMER    #########################
    def _set_timer_update_interval(self, value):
        self._timer_update_inverval = value

    def _on_timer_update(self):
        # if not self.is_executing_task():
        self.update_info()

    def _on_timer_1s(self):
        pass

    # #######################    HardwareObject    #######################

    def connectNotify(self, signal):
        logging.getLogger().info("connectNotify " + str(signal))

    # ########################    PUBLIC    #########################

    def get_state(self):
        """
        Returns sample changer state
        :rtype: SampleChangerState
        """
        return self.state

    def get_status(self):
        """
        Returns textual description of state
        :rtype: str
        """
        return self.status

    def get_task_error(self):
        """
        Description of the error of last executed task (or None if success).
        :rtype: str
        """
        return self.task_error

    def is_ready(self):
        """
        Description of the error of last executed task (or None if success).
        :rtype: str
        """
        return (
            self.state == SampleChangerState.Ready
            or self.state == SampleChangerState.Loaded
            or self.state == SampleChangerState.Charging
            or self.state == SampleChangerState.StandBy
        )

    def wait_ready(self, timeout=-1):
        start = time.clock()
        while not self.is_ready():
            if timeout > 0:
                if (time.clock() - start) > timeout:
                    raise Exception("Timeout waiting ready")
            gevent.sleep(0.01)

    def is_normal_state(self):
        """
        Description of the error of last executed task (or None if success).
        :rtype: str
        """
        return (
            self.state != SampleChangerState.Disabled
            and self.state != SampleChangerState.Alarm
            and self.state != SampleChangerState.Fault
            and self.state != SampleChangerState.Unknown
        )

    def is_enabled(self):
        return self.state != SampleChangerState.Disabled

    def assert_enabled(self):
        if not self.is_enabled():
            raise Exception("Sample Changer is disabled")

    def assert_not_charging(self):
        if self.state == SampleChangerState.Charging:
            raise Exception("Sample Changer is in Charging mode")

    def assert_can_execute_task(self):
        if not self.is_ready():
            raise Exception(
                "Cannot execute task: bad state ("
                + SampleChangerState.tostring(self.state)
                + ")"
            )

    def is_task_finished(self):
        """
        Description of the error of last executed task (or None if success).
        :rtype: str
        """
        return self.is_ready() or (
            (not self.is_normal_state()) and (self.state != SampleChangerState.Unknown)
        )

    def is_executing_task(self):
        """
        Description of the error of last executed task (or None if success).
        :rtype: str
        """
        return self.task is not None

    def wait_task_finished(self, timeout=-1):
        start = time.clock()
        while not self.is_task_finished():
            if timeout > 0:
                if (time.clock() - start) > timeout:
                    raise Exception("Timeout waiting end of task")
            gevent.sleep(0.01)

    def get_loaded_sample(self):
        """
        Returns current loaded sample
        :rtype: str
        """
        for s in self.get_sample_list():
            if s.is_loaded():
                return s
        return None

    def has_loaded_sample(self):
        """
        Returns current loaded sample
        :rtype: str
        """
        return self.get_loaded_sample() is not None

    def is_mounted_sample(self, sample_location):
        try:
            return self.get_loaded_sample().get_coords() == sample_location
        except AttributeError:
            return False

    def abort(self):
        """
        Aborts current task and puts device in safe state
        """
        self._do_abort()
        if self.task_proc is not None:
            self.task_proc.join(1.0)
            if self.task_proc is not None:
                self.task_proc.kill(Exception("Task aborted"))
                self.task = None
                self.task_proc = None
                self.task_error = None

    def update_info(self):
        """
        """
        former_loaded = self.get_loaded_sample()
        self._do_update_info()
        if self._is_dirty():
            self._trigger_info_changed_event()

        loaded = self.get_loaded_sample()
        if loaded != former_loaded:
            if (
                (loaded is None)
                or (former_loaded is None)
                or (loaded.get_address() != former_loaded.get_address())
            ):
                self._trigger_loaded_sample_changed_event(loaded)

        self._reset_dirty()

    def is_transient(self):
        return self._transient

    def _set_transient(self, value):
        self._transient = value

    def get_token(self):
        return self._token

    def set_token(self, token):
        self._token = token

    def get_sample_properties(self):
        return ()

    # ########################    TASKS    #########################
    def change_mode(self, mode, wait=True):
        """
        Change the mode (SC specific, imply change of the State)
        Modes:
            Unknown     = 0
            Normal      = 1
            Charging    = 2
            Disabled    = 3
        """
        if mode == SampleChangerMode.Unknown:
            return
        elif mode == self.get_state():
            return
        if self.get_state() == SampleChangerState.Disabled:
            self._set_state(SampleChangerState.Unknown)
            self.update_info()
        elif mode == SampleChangerMode.Disabled:
            self._set_state(SampleChangerState.Disabled)
        return self._execute_task(
            SampleChangerState.ChangingMode, wait, self._do_change_mode, mode
        )

    @task
    def scan(self, component=None, recursive=False):
        if isinstance(component, types.ListType):
            for c in component:
                self._scan_one(c, recursive)
        else:
            return self._scan_one(component, recursive)

    def _scan_one(self, component, recursive):
        self.assert_not_charging()
        if component is None:
            component = self
        component = self._resolve_component(component)
        component.assert_is_scannable()
        return self._execute_task(
            SampleChangerState.Scanning, True, self._do_scan, component, recursive
        )

    def select(self, component, wait=True):
        component = self._resolve_component(component)
        ret = self._execute_task(
            SampleChangerState.Selecting, wait, self._do_select, component
        )
        self._trigger_selection_changed_event()
        return ret

    def chained_load(self, sample_to_unload, sample_to_load):
        self.unload(sample_to_unload)
        self.wait_ready(timeout=10)
        return self.load(sample_to_load)

    def load(self, sample=None, wait=True):
        """
        Load a sample.
        """
        sample = self._resolve_component(sample)
        self.assert_not_charging()
        # Do a chained load in this case
        if self.has_loaded_sample():
            # Do a chained load in this case
            if (sample is None) or (sample == self.get_loaded_sample()):
                raise Exception(
                    "The sample "
                    + str(self.get_loaded_sample().get_address())
                    + " is already loaded"
                )
            return self.chained_load(self.get_loaded_sample(), sample)
        else:
            return self._execute_task(
                SampleChangerState.Loading, wait, self._do_load, sample
            )

    def unload(self, sample_slot=None, wait=True):
        """
        Unload the sample.
        If sample_slot=None, unloads to the same slot it was loaded from.
        """
        sample_slot = self._resolve_component(sample_slot)
        self.assert_not_charging()
        # In case we have manually mounted we can command an unmount
        if not self.has_loaded_sample():
            raise Exception("No sample is loaded")
        return self._execute_task(
            SampleChangerState.Unloading, wait, self._do_unload, sample_slot
        )

    def reset(self, wait=True):
        """
        Reset the SC.
        If sample_slot=None, unloads to the same slot it was loaded from.
        """
        return self._execute_task(SampleChangerState.Resetting, wait, self._do_reset)

    def _load(self, sample=None):
        self._do_load(sample)

    def _unload(self, sample_slot=None):
        self._do_unload(sample_slot)

    def _resolve_component(self, component):
        if component is not None and isinstance(component, basestring):
            c = self.get_component_by_address(component)
            if c is None:
                raise Exception("Invalid component: " + component)
            return c
        return component

    # ########################    ABSTRACTS    #########################

    @abc.abstractmethod
    def _do_abort(self):
        """
        Aborts current task and puts device in safe state
        """
        return

    @abc.abstractmethod
    def _do_update_info(self):
        return

    @abc.abstractmethod
    def _do_change_mode(self, mode):
        return

    @abc.abstractmethod
    def _do_scan(self, component, recursive):
        return

    @abc.abstractmethod
    def _do_select(self, component):
        return

    @abc.abstractmethod
    def _do_load(self, sample):
        return

    @abc.abstractmethod
    def _do_unload(self, sample_slot=None):
        return

    @abc.abstractmethod
    def _do_reset(self):
        return

    # ########################    PROTECTED    #########################

    def _execute_task(self, task, wait, method, *args):
        self.assert_can_execute_task()
        logging.debug("Start " + SampleChangerState.tostring(task))
        self.task = task
        self.task_error = None
        self._set_state(task)
        ret = self._run(task, method, wait=False, *args)
        self.task_proc = ret

        ret.link(self._on_task_ended)
        if wait:
            return ret.get()
        else:
            return ret

    @task
    def _run(self, task, method, *args):
        """
        method(self,*arguments)
        exeption=None
        try:
            while !_is_task_finished(state):
              time.sleep(0.1)
            exeption=_getTaskException(state)
        finally:
            _trigger_task_finished_event(state,exeption)
            self._set_state(SampleChangerState.Ready)
        """
        exception = None
        ret = None
        try:
            ret = method(*args)
        except Exception as ex:
            exception = ex
        # if self.get_state()==self.task:
        #    self._set_state(SampleChangerState.Ready)
        self.update_info()
        task = self.task
        self.task = None
        self.task_proc = None
        self._trigger_task_finished_event(task, ret, exception)
        if exception is not None:
            self._on_task_failed(task, exception)
            raise exception
        return ret

    def _on_task_failed(self, task, exception):
        pass

    def _on_task_ended(self, task):
        try:
            e = task.get()
            logging.debug("Task ended. Return value: " + str(e))
        except Exception as errmsg:
            logging.error("Error while executing sample changer task: %s", str(errmsg))

    def _set_state(self, state=None, status=None):
        if (state is not None) and (self.state != state):
            former = self.state
            self.state = state
            if status is None:
                status = SampleChangerState.tostring(state)
            self._trigger_state_changed_event(former)

        if (status is not None) and (self.status != status):
            self.status = status
            self._trigger_status_changed_event()

    def _reset_loaded_sample(self):
        for s in self.get_sample_list():
            s._set_loaded(False)
        self._trigger_loaded_sample_changed_event(None)

    def _set_loaded_sample(self, sample):
        for s in self.get_sample_list():
            if s != sample:
                s._set_loaded(False)
            else:
                s._set_loaded(True)
        self._trigger_loaded_sample_changed_event(sample)

    def _set_selected_sample(self, sample):
        cur = self.get_selected_sample()
        if cur != sample:
            Container._set_selected_sample(self, sample)
            self._trigger_selection_changed_event()

    def _set_selected_component(self, component):
        cur = self.get_selected_component()
        if cur != component:
            Container._set_selected_component(self, component)
            self._trigger_selection_changed_event()

    # ########################    PRIVATE    #########################

    def _trigger_state_changed_event(self, former):
        self.emit(self.STATE_CHANGED_EVENT, (self.state, former))

    def _trigger_status_changed_event(self):
        self.emit(self.STATUS_CHANGED_EVENT, (str(self.status),))

    def _trigger_loaded_sample_changed_event(self, sample):
        self.emit(self.LOADED_SAMPLE_CHANGED_EVENT, (sample,))

    def _trigger_selection_changed_event(self):
        self.emit(self.SELECTION_CHANGED_EVENT, ())

    def _trigger_info_changed_event(self):
        self.emit(self.INFO_CHANGED_EVENT, ())

    def _trigger_task_finished_event(self, task, ret, exception):
        self.emit(self.TASK_FINISHED_EVENT, (task, ret, exception))

    def _trigger_contents_updated_event(self):
        self.emit(self.CONTENTS_UPDATED_EVENT)
