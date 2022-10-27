import gevent
from datetime import datetime
import time
import logging
import ast

from mxcubecore.HardwareObjects.abstract import AbstractSampleChanger


from mxcubecore.HardwareObjects.abstract.sample_changer import (
    Container,
)

from mxcubecore.HardwareObjects.EMBLFlexHCD import Basket
class Cell(Container.Container):
    __TYPE__ = "Cell"

    def __init__(self, container, number, puck_type="SC3"):
        super(Cell, self).__init__(
            self.__TYPE__, container, Cell.get_cell_address(number), True
        )
        self.present = True

        if puck_type=="SC3":
            for i in range(3):
                self._add_component(
                    Basket(self, number, i + 1, unipuck=False)
                )
        else:
            for i in range(3):
                self._add_component(
                    Basket(self, number, i + 1, unipuck=True)
                )

    @staticmethod
    def get_cell_address(cell_number):
        return str(cell_number)

    def _reset_basket_info(self, basket_no):
        pass

    def clear_info(self):
        self.get_container()._reset_cell_info(self.get_index() + 1)
        self.get_container()._trigger_info_changed_event()

    def get_cell(self):
        return self


class SampleChangerMockup(AbstractSampleChanger.SampleChanger):

    __TYPE__ = "Mockup"
    NO_OF_BASKETS = 5
    NO_OF_PUCK_IN_BASKET = 3
    NO_OF_SAMPLES_IN_BASKET = 10

    def __init__(self, *args, **kwargs):
        super(SampleChangerMockup, self).__init__(self.__TYPE__, False, *args, **kwargs)

    def init(self):
        self._selected_sample = -1
        self._selected_basket = -1
        self._scIsCharging = None

        self.no_of_baskets = self.get_property(
            "no_of_baskets", SampleChangerMockup.NO_OF_BASKETS
        )

        self.no_of_samples_in_basket = self.get_property(
            "no_of_samples_in_basket", SampleChangerMockup.NO_OF_SAMPLES_IN_BASKET
        )

        _pucks = '["UNI", "UNI", "UNI", "UNI", "UNI", "UNI", "UNI", "UNI"]'
        pucks = ast.literal_eval(self.get_property("puck_configuration", _pucks))

        for i in range(8):
            cell = Cell(self, i + 1, pucks[i])
            self._add_component(cell)

        self._init_sc_contents()
        self.signal_wait_task = None
        AbstractSampleChanger.SampleChanger.init(self)

        self.log_filename = self.get_property("log_filename")

    def get_log_filename(self):
        return self.log_filename

    def load_sample(self, holder_length, sample_location=None, wait=False):
        self.load(sample_location, wait)

    def load(self, sample, wait=False):
        self.emit("fsmConditionChanged", "sample_mounting_sample_changer", True)
        self._set_state(AbstractSampleChanger.SampleChangerState.Loading)
        self._reset_loaded_sample()

        if isinstance(sample, tuple):
            basket, sample = sample
        else:
            basket, sample = sample.split(":")

        self._selected_basket = basket = int(basket)
        self._selected_sample = sample = int(sample)

        msg = "Loading sample %d:%d" % (basket, sample)
        logging.getLogger("user_level_log").info(
            "Sample changer: %s. Please wait..." % msg
        )

        self.emit("progressInit", (msg, 100))
        for step in range(2 * 100):
            self.emit("progressStep", int(step / 2.0))
            time.sleep(0.01)

        mounted_sample = self.get_component_by_address(
            Container.Pin.get_sample_address(basket, sample)
        )
        mounted_sample._set_loaded(True, False)
        self._set_state(AbstractSampleChanger.SampleChangerState.Ready)

        self._set_loaded_sample(mounted_sample)
        self.update_info()
        logging.getLogger("user_level_log").info("Sample changer: Sample loaded")
        self.emit("progressStop", ())

        self.emit("fsmConditionChanged", "sample_is_loaded", True)
        self.emit("fsmConditionChanged", "sample_mounting_sample_changer", False)

        return self.get_loaded_sample()

    def unload(self, sample_slot=None, wait=None):
        logging.getLogger("user_level_log").info("Unloading sample")
        sample = self.get_loaded_sample()
        sample._set_loaded(False, True)
        self._selected_basket = -1
        self._selected_sample = -1
        self._trigger_loaded_sample_changed_event(self.get_loaded_sample())
        self.emit("fsmConditionChanged", "sample_is_loaded", False)

    def get_loaded_sample(self):
        return self.get_component_by_address(
            Container.Pin.get_sample_address(
                self._selected_basket, self._selected_sample
            )
        )

    def is_mounted_sample(self, sample):
        return (
            self.get_component_by_address(
                Container.Pin.get_sample_address(sample[0], sample[1])
            )
            == self.get_loaded_sample()
        )

    def _do_abort(self):
        return

    def _do_change_mode(self):
        return

    def _do_update_info(self):
        return

    def _do_select(self, component):
        return

    def _do_scan(self, component, recursive):
        return

    def _do_load(self, sample=None):
        return

    def _do_unload(self, sample_slot=None):
        return

    def _do_reset(self):
        return

    def _init_sc_contents(self):
        """
        Initializes the sample changer content with default values.

        :returns: None
        :rtype: None
        """
        named_samples = {}
        if self.has_object("test_sample_names"):
            for tag, val in self["test_sample_names"].get_properties().items():
                named_samples[val] = tag

        for basket_index in range(self.no_of_baskets):
            basket = self.get_components()[basket_index]
            datamatrix = None
            present = True
            scanned = False
            if basket is not None:
                basket._set_info(present, datamatrix, scanned)

        sample_list = []
        for basket_index in range(self.no_of_baskets):
            for sample_index in range(self.no_of_samples_in_basket):
                sample_list.append(
                    (
                        "",
                        basket_index + 1,
                        sample_index + 1,
                        1,
                        Container.Pin.STD_HOLDERLENGTH,
                    )
                )
        for spl in sample_list:
            address = Container.Pin.get_sample_address(spl[1], spl[2])
            sample = self.get_component_by_address(address)
            sample_name = named_samples.get(address)
            if sample_name is not None:
                sample._name = sample_name
            datamatrix = "matr%d_%d" % (spl[1], spl[2])
            present = scanned = loaded = has_been_loaded = False
            if sample is not None:
                sample._set_info(present, datamatrix, scanned)
                sample._set_loaded(loaded, has_been_loaded)
                sample._set_holder_length(spl[4])

        self._set_state(AbstractSampleChanger.SampleChangerState.Ready)
