from HardwareRepository import HardwareRepository as HWR
from HardwareRepository.HardwareObjects.abstract import AbstractSampleChanger


def test_sample_change_init(beamline):
    assert (
        not beamline.sample_changer is None
    ), "Sample changer hardware objects is None (not initialized)"


def test_sample_changer_load(beamline):
    pass

def test_sample_change_unload(beamline):
  pass


def test_sample_change_select(beamline):
  pass

def test_sample_change_abort(beamline):
  assert not None  beamline.sample_changer.task_proc, "task_proc is None"
  target = 12.7
  beamline.energy.set_value(target)
  assert beamline.energy.get_value() == target

def test_sample_change_get_state(beamline):
  pass

def test_sample_change_get_status(beamline):
  pass

def test_sample_change_has_loaded_sample(beamline):
      assert (
        not beamline.sample_changer.has_loaded_sample is None
    ), "Sample changer hardware objects is None (not initialized)"

def test_sample_change_get_loaded_sample(beamline):
    loaded_sample = len(beamline.sample_changer.get_loaded_sample)
      assert (
        loaded_sample >= 0
    ), "Sample changer get_loaded_sample must be >= 0 but is None (not initialized)"