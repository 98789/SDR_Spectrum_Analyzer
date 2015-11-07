#!/usr/bin/env python2
##################################################
# GNU Radio Python Flow Graph
# Title: Gui Test
# Generated: Fri Oct 16 18:12:32 2015
##################################################

from gnuradio import blocks
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from gnuradio.fft import window
from gnuradio.filter import firdes
from optparse import OptionParser
from remote_configurator import remote_configurator
import RadioGIS
import baz
import time


class GUI_test(gr.top_block):

    def __init__(self):
        gr.top_block.__init__(self, "Gui Test")

        ##################################################
        # Variables
        ##################################################
        self.port = port = 9999
        self.gan = gan = 10
        self.fc = fc = 99700000
        self.ab = ab = 20000000
        self.N = N = 1024
        self.IP = IP = "192.168.1.127"
        self.Antena = Antena = "RX2"
        self.ventana = ventana = window.blackmanharris
        self.base = base = "exponencial"

        ##################################################
        # Blocks
        ##################################################
        self.src = uhd.usrp_source(
        	",".join(("", "")),
        	uhd.stream_args(
        		cpu_format="fc32",
        		channels=range(1),
        	),
        )
        self.src.set_samp_rate(ab)
        self.src.set_center_freq(fc, 0)
        self.src.set_gain(gan, 0)
        self.src.set_antenna("RX2", 0)
        self.dbm = RadioGIS.dbm()
        self.blocks_vector_to_stream_0 = blocks.vector_to_stream(gr.sizeof_float*1, N)
        self.blocks_stream_to_vector_0 = blocks.stream_to_vector(gr.sizeof_gr_complex*1, N)
        self.blocks_complex_to_mag_0 = blocks.complex_to_mag(N)
        self.baz_udp_sink_0 = baz.udp_sink(gr.sizeof_float*1, IP, port, 1472, True, False)
        self.RadioGIS_fft_0 = RadioGIS.fft(N, base, (ventana(N)))

        ##################################################
        # Connections
        ##################################################
        self.connect((self.RadioGIS_fft_0, 0), (self.blocks_complex_to_mag_0, 0))    
        self.connect((self.blocks_complex_to_mag_0, 0), (self.blocks_vector_to_stream_0, 0))    
        self.connect((self.blocks_stream_to_vector_0, 0), (self.RadioGIS_fft_0, 0))    
        self.connect((self.blocks_vector_to_stream_0, 0), (self.dbm, 0))    
        self.connect((self.dbm, 0), (self.baz_udp_sink_0, 0))    
        self.connect((self.src, 0), (self.blocks_stream_to_vector_0, 0))


    def get_port(self):
        return self.port

    def set_port(self, port):
        self.port = port

    def get_gan(self):
        return self.gan

    def set_gan(self, gan):
        self.gan = gan
        self.src.set_gain(self.gan, 0)

    def get_fc(self):
        return self.fc

    def set_fc(self, fc):
        fc_range = self.src.get_freq_range(0)
        if self.ab / 2 + fc_range.start() < fc < fc_range.stop() - self.ab / 2:
            self.fc = fc
            self.src.set_center_freq(self.fc, 0)

    def get_ab(self):
        return self.ab

    def set_ab(self, ab):
        self.ab = ab
        self.src.set_samp_rate(self.ab)

    def get_N(self):
        return self.N

    def set_N(self, N):
        self.N = N

    def get_IP(self):
        return self.IP

    def set_IP(self, IP):
        self.IP = IP

    def get_Antena(self):
        return self.Antena

    def set_Antena(self, Antena):
        self.Antena = Antena
        self.src.set_antenna(self.Antena, 0)

    def get_ventana(self):
        return self.ventana

    def set_ventana(self, ventana):
        self.ventana = getattr(window, ventana.replace(" ", "").lower())
        if ventana != "Kaiser":
            self.RadioGIS_fft_0.set_window(self.ventana(self.N))
        else:
            self.RadioGIS_fft_0.set_window(self.ventana(self.N, 6.76))

    def get_base(self):
        return self.base

    def set_base(self, base):
        self.base = base.split()[0].lower()
        self.RadioGIS_fft_0.set_W(self.base)


if __name__ == '__main__':
    parser = OptionParser(option_class=eng_option, usage="%prog: [options]")
    (options, args) = parser.parse_args()
    tb = GUI_test()
    tb.start()
    dino = remote_configurator("192.168.1.100", 9999)
    dino.bind()
    while 1:
    	data = dino.listen()
        if "gan" in data:
            tb.set_gan(data.get("gan"))
        elif "fc" in data:
            tb.set_fc(data.get("fc"))
        elif "ab" in data:
            tb.set_ab(data.get("ab"))
        elif "IP" in data:
            tb.set_IP(data.get("IP"))
        elif "base" in data:
            tb.set_base(data.get("base"))
        else:
            tb.set_ventana(data.get("ventana"))
    try:
        raw_input('Press Enter to quit: ')
    except EOFError:
        pass
    tb.stop()
    tb.wait()
