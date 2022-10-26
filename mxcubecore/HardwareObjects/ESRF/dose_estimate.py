import logging
import sys
import subprocess

from mxcubecore import HardwareRepository as HWR

class DoseEstimate:
    def __init__(self, fname=None):
        self.dose_rate = 0.0
        self.total_dose_estimate = 0.0
                
    def init(self, fname="/opt/pxsoft/bin/flux2dose", transmission=None):
       self.dose_rate = self.get_current_dose(fname, transmission)
       self.fname = fname
    
    def get_current_dose(fname, transmission):
        fullbeam = 1e13  # photons/sec

        if transmission is None:
            transmission = HWR.beamline.transmission.get_value()

        beamx, beamy = HWR.beamline.detector.get_beam_position()

        real_flux = fullbeam * (float(transmission)/100)
        try:
            dose_cmd = "{fname} -bh %f -bv %f -w 0.873 -f %f" % (beamx, beamy, real_flux)
            dose_rate_str = subprocess.check_output(dose_cmd, shell=True)
            dose_rate_str = dose_rate_str.decode('ascii')
            dose_rate = float(dose_rate_str.split()[2])
        except Exception:
            print("flux2dose program not installed in /opt/pxsoft, please check\n")
            dose_rate = 0.0
        
        return dose_rate

    def dose_estimate(self, transmission, exposure_time,  oscillation_range, nb_images):
        try:
            self.init(transmission=transmission)
            wedge = float(nb_images * oscillation_range) 
                
            nframes = wedge / oscillation_range
            total_time =  exposure_time * nframes  # Value in Seconds
            self.total_dose_estimate = self.dose_rate * total_time

            return self.total_dose_estimate

        except Exception:
            print("Could not Calculate dose estimation")
            return self.total_dose_estimate
