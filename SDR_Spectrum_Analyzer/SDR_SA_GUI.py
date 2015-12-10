#!/usr/bin/python2
#
# Copyright 2012 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# GNU Radio is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# GNU Radio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GNU Radio; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#

from gnuradio import blocks
from PyQt4 import Qt
from gnuradio import eng_notation
from gnuradio import gr
from gnuradio import uhd
from gnuradio.filter import firdes
from optparse import OptionParser
from remote_configurator import remote_configurator
import sip
import sys
import RadioGIS

try:
    from gnuradio import qtgui
    from PyQt4 import QtGui, QtCore
    import sip
except ImportError:
    sys.stderr.write("Error: Program requires PyQt4 and gr-qtgui.\n")
    sys.exit(1)

try:
    from gnuradio import channels
except ImportError:
    sys.stderr.write("Error: Program requires gr-channels.\n")
    sys.exit(1)

class dialog_box(QtGui.QWidget):
    def __init__(self, header, display, display2, control):
        QtGui.QWidget.__init__(self, None)
        self.setWindowTitle('SDR Spectrum Analyzer')
	self.showMaximized()

        self.vertlayout = QtGui.QVBoxLayout(self)
        self.vertlayout.addWidget(header)
        self.body = QtGui.QWidget()
        self.boxlayout = QtGui.QHBoxLayout()
        self.boxlayout.addWidget(control, 1)

        self.tabs = QtGui.QTabWidget()
        self.tab1 = QtGui.QWidget()
        self.tab1layout = QtGui.QHBoxLayout()
        self.tab2 = QtGui.QWidget()
        self.tab2layout = QtGui.QHBoxLayout()

        self.tab1layout.addWidget(display)
        self.tab2layout.addWidget(display2)

        self.tab1.setLayout(self.tab1layout)
        self.tab2.setLayout(self.tab2layout)

        self.tabs.addTab(self.tab1, "Espectro")
        self.tabs.addTab(self.tab2, "Waterfall")

        self.boxlayout.addWidget(self.tabs)

        self.body.setLayout(self.boxlayout)
        self.vertlayout.addWidget(self.body)


class header(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle('Header')

        self.hbox = QtGui.QHBoxLayout(self)
        self.image = QtGui.QLabel()
        self.image.setPixmap(QtGui.QPixmap(QtCore.QString.fromUtf8('image.jpeg')))
        self.hbox.addWidget(self.image)
        self.title = QtGui.QLabel()
        font = QtGui.QFont( "Helvetica", 30, QtGui.QFont.Bold)
        self.title.setText("SDR Spectrum Analyzer")
        self.title.setFont(font)
        self.hbox.addWidget(self.title)

class display_box(QtGui.QWidget):
    def __init__(self, plot_handler, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle('Display')

        self.vbox = QtGui.QVBoxLayout(self)
        self.vbox.addWidget(plot_handler)

class control_box(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setMaximumWidth(300)
        self.setWindowTitle('Control Panel')

        self.tabs = QtGui.QTabWidget()
        self.tab1 = QtGui.QWidget()
        self.tab2 = QtGui.QWidget()

        self.startButton = QtGui.QPushButton("Iniciar")
        self.connect(self.startButton, QtCore.SIGNAL('clicked()'), self.send_start_signal)

        self.stopButton = QtGui.QPushButton("Parar")
        self.connect(self.stopButton, QtCore.SIGNAL('clicked()'), self.send_stop_signal)

        self.hbox = QtGui.QHBoxLayout()
        self.hbox.addWidget(self.configButton)
        self.hbox.addWidget(self.stopButton)

        self.vbox = QtGui.QVBoxLayout(self)
        self.vbox_2 = QtGui.QWidget()
        self.vbox_2.setLayout(self.hbox)
        self.vbox.addWidget(self.vbox_2)

        self.conf_an = QtGui.QFormLayout()
        self.conf_usrp = QtGui.QFormLayout()

        self.sel_fc = QtGui.QLineEdit(self)
        self.sel_fc.setMinimumWidth(100)
        self.conf_an.addRow("Frecuencia Central:", self.sel_fc)
        self.connect(self.sel_fc, QtCore.SIGNAL("editingFinished()"),
                     self.fc_edit_text)

        self.sel_span = QtGui.QLineEdit(self)
        self.sel_span.setMinimumWidth(100)
        self.conf_an.addRow("SPAN:", self.sel_span)
        self.connect(self.sel_span, QtCore.SIGNAL("editingFinished()"),
                     self.span_edit_text)

        self.sel_ganancia = QtGui.QLineEdit(self)
        self.sel_ganancia.setMinimumWidth(100)
        self.conf_an.addRow("Ganancia:", self.sel_ganancia)
        self.connect(self.sel_ganancia, QtCore.SIGNAL("editingFinished()"),
                     self.ganancia_edit_text)

        self.sel_ventana = QtGui.QComboBox(self)
        ventanas = ["Bartlett",
                  "Blackman",
                  "Blackman Harris",
                  "Flat top",
                  "Hamming",
                  "Hanning",
                  "Kaiser",
                  "Rectangular"]
        self.sel_ventana.addItems(ventanas)
        self.sel_ventana.setMinimumWidth(100)
        self.conf_an.addRow("Ventana:", self.sel_ventana)
        self.connect(self.sel_ventana, QtCore.SIGNAL("currentTextChanged(const QString & text)"),
                     self.ventana_edit_text)
        self.sel_ventana.currentIndexChanged.connect(self.ventana_edit_text)

        self.sel_base = QtGui.QComboBox(self)
        bases = ["Exponencial Compleja",
                  "Triangular",
                  "Potencia",
                   "Binomial"]
        self.sel_base.addItems(bases)
        self.sel_base.setMinimumWidth(100)
        self.conf_an.addRow("Base:", self.sel_base)
        self.connect(self.sel_base, QtCore.SIGNAL("currentTextChanged(const QString & text)"),
                     self.base_edit_text)
        self.sel_base.currentIndexChanged.connect(self.base_edit_text)

        self.sel_escala = QtGui.QComboBox(self)
        escalas = ["dBm",
                  "Lineal"]
        self.sel_escala.addItems(escalas)
        self.sel_escala.setMinimumWidth(100)
        self.conf_an.addRow("Escala:", self.sel_escala)

        self.sel_promedio = QtGui.QLineEdit(self)
        self.sel_promedio.setMinimumWidth(100)
        self.conf_an.addRow("Promediado:", self.sel_promedio)
        self.connect(self.sel_promedio, QtCore.SIGNAL("editingFinished()"),
                     self.promedio_edit_text)

        self.sel_IP = QtGui.QLineEdit(self)
        self.sel_IP.setMinimumWidth(100)
        self.conf_usrp.addRow("IP:", self.sel_IP)
        self.connect(self.sel_IP, QtCore.SIGNAL("editingFinished()"),
                     self.IP_edit_text)

        self.sel_puerto = QtGui.QLineEdit(self)
        self.sel_puerto.setMinimumWidth(100)
        self.conf_usrp.addRow("Puerto:", self.sel_puerto)
        self.connect(self.sel_puerto, QtCore.SIGNAL("editingFinished()"),
                     self.puerto_edit_text)

        self.sel_y1 = QtGui.QLineEdit(self)
        self.sel_y1.setMaximumWidth(50)
        self.conf_an.addRow("y1:", self.sel_y1)
        self.connect(self.sel_y1, QtCore.SIGNAL("editingFinished()"),
                     self.y1_edit_text)

        self.sel_y0 = QtGui.QLineEdit(self)
        self.sel_y0.setMaximumWidth(50)
        self.conf_an.addRow("y0:", self.sel_y0)
        self.connect(self.sel_y0, QtCore.SIGNAL("editingFinished()"),
                     self.y0_edit_text)

        self.tab1.setLayout(self.conf_an)
        self.tab2.setLayout(self.conf_usrp)
        self.vbox.addWidget(self.tabs)

        self.tabs.addTab(self.tab1, "Analizador de Espectro")
        self.tabs.addTab(self.tab2, "USRP")

    def attach_signal(self, signal):
        self.signal = signal
        self.sel_IP.setText(QtCore.QString("%1").arg(self.signal.get_IP()))
        self.sel_puerto.setText(QtCore.QString("%1").arg(self.signal.get_port()))
        self.sel_span.setText(QtCore.QString("%1").arg(self.signal.get_ab()))
        self.sel_fc.setText(QtCore.QString("%1").arg(self.signal.get_fc()))
        self.sel_ganancia.setText(QtCore.QString("%1").arg(self.signal.get_gan()))
        self.sel_promedio.setText(QtCore.QString("%1").arg(self.signal.get_n()))
        self.sel_y0.setText(QtCore.QString("%1").arg(self.signal.get_y0()))
        self.sel_y1.setText(QtCore.QString("%1").arg(self.signal.get_y1()))

    def send_start_signal(self):
        try:
            conf_ini = {"n": self.signal.get_n(), "start": True}
            self.signal.get_dino().send(conf_ini)
            print("Application successfully started")
        except:
            print("Something went wrong while starting the application")

    def send_stop_signal(self):
        try:
            self.signal.get_dino().send({"stop": True})
            print("Application successfully stopped")
        except:
            print("Unable to stop the application D:")

    def IP_edit_text(self):
        try:
	    newIP = str(self.sel_IP.text())
            self.signal.set_IP(newIP)
        except ValueError:
	    print("Wrong IP format")

    def puerto_edit_text(self):
        try:
	    newPuerto = str(self.sel_IP.text())
            self.signal.set_puerto(newPuerto)
        except ValueError:
	    print("Invalid port")

    def span_edit_text(self):
        try:
	    newSpan = float(self.sel_span.text())
            self.signal.set_ab(newSpan)
        except ValueError:
	    print("Unsupported span value")

    def fc_edit_text(self):
        try:
	    newFc = float(self.sel_fc.text())
            self.signal.set_fc(newFc)
        except ValueError:
	    print("Invalid center frequency")
        self.sel_fc.setText("{0:.0f}".format(self.signal.get_fc()))

    def ganancia_edit_text(self):
        try:
	    newGanancia = float(self.sel_ganancia.text())
            self.signal.set_gan(newGanancia)
        except ValueError:
	    print("Gain out of range")

    def ventana_edit_text(self):
        try:
	    newVentana = str(self.sel_ventana.currentText())
            self.signal.set_ventana(newVentana)
        except ValueError:
	    print("Something went wrong with the selected window")

    def base_edit_text(self):
        try:
	    newBase = str(self.sel_base.currentText())
            self.signal.set_base(newBase)
        except ValueError:
	    print("Something went wrong with the selected base")

    def promedio_edit_text(self):
        try:
	    newPromedio = int(self.sel_promedio.text())
            self.signal.set_n(newPromedio)
        except ValueError:
	    print("Gain out of range")

    def y0_edit_text(self):
        try:
	    newy0 = float(self.sel_y0.text())
            self.signal.set_y0(newy0)
        except ValueError:
	    print("Invalid amplitude value")

    def y1_edit_text(self):
        try:
	    newy1 = float(self.sel_y1.text())
            self.signal.set_y1(newy1)
        except ValueError:
	    print("Invalid frequency value")


class sdr_spectrum_analyzer(gr.top_block):
    def __init__(self):
        gr.top_block.__init__(self)

        self.qapp = QtGui.QApplication(sys.argv)
        ss = open('style.qss')
        sstext = ss.read()
        ss.close()
        self.qapp.setStyleSheet(sstext)

        ##################################################
        # Variables
        ##################################################
        self.port = port = 9999
        self.gan = gan = 10
        self.fc = fc = 99700000
        self.ab = ab = 20000000
        self.N = N = 1024
        self.n = n = 512
        self.IP = IP = "192.168.1.103"
        self.Antena = Antena = "RX2"
	self.remote_IP = "192.168.1.127"
        self.dino = remote_configurator(self.remote_IP, self.port)
        self.ventana = "Hamming"
        self.base = "exponencial"
        self.y0 = y0 = -100
        self.y1 = y1 = 0
        self.frequencies = frequencies = [0, 200, 600, 700, 900, 1000]
        self.amplitudes = amplitudes = [0, -20, -20, -15, -15, -34]

        ##################################################
        # Blocks
        ##################################################
        self.qtgui_vector_sink_f_0 = qtgui.vector_sink_f(
            N,
            (fc - ab / 2) / 1e6,
            (ab / N) / 1e6,
            "Frecuencia (MHz)",
            "Amplitud",
            "",
            2 # Number of inputs
        )
        self.qtgui_vector_sink_f_0.set_update_time(0.1)
        self.qtgui_vector_sink_f_0.set_y_axis(y0, y1)
        self.qtgui_vector_sink_f_0.enable_autoscale(False)
        self.qtgui_vector_sink_f_0.enable_grid(True)
        self.qtgui_vector_sink_f_0.set_vec_average(0.1)
        self.qtgui_vector_sink_f_0.set_x_axis_units("Hz")
        self.qtgui_vector_sink_f_0.set_y_axis_units("dBm")
        self.qtgui_vector_sink_f_0.set_ref_level(-90)
        
        labels = ["Espectro", "Mascara", "", "", "",
                  "", "", "", "", ""]
        widths = [1, 3, 1, 1, 1,
                  1, 1, 1, 1, 1]
        colors = ["blue", "red", "yellow", "black", "cyan",
                  "magenta", "green", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]
        for i in xrange(2):
            if len(labels[i]) == 0:
                self.qtgui_vector_sink_f_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_vector_sink_f_0.set_line_label(i, labels[i])
            self.qtgui_vector_sink_f_0.set_line_width(i, widths[i])
            self.qtgui_vector_sink_f_0.set_line_color(i, colors[i])
            self.qtgui_vector_sink_f_0.set_line_alpha(i, alphas[i])

        self._qtgui_vector_sink_f_0_win = sip.wrapinstance(self.qtgui_vector_sink_f_0.pyqwidget(), Qt.QWidget)
        
        self.qtgui_waterfall_sink_x_0 = qtgui.waterfall_sink_f(
        	N, #size
        	firdes.WIN_BLACKMAN_hARRIS, #wintype
        	fc - ab / 2, #fc
        	ab / N, #bw
        	"", #name
                1 #number of inputs
        )

        self.qtgui_waterfall_sink_x_0.set_update_time(0.10)
        self.qtgui_waterfall_sink_x_0.enable_grid(False)
        
        if float == type(float()):
          self.qtgui_waterfall_sink_x_0.set_plot_pos_half(not True)
        
        labels = ["", "", "", "", "",
                  "", "", "", "", ""]
        colors = [0, 0, 0, 0, 0,
                  0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]
        for i in xrange(1):
            if len(labels[i]) == 0:
                self.qtgui_waterfall_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_waterfall_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_waterfall_sink_x_0.set_color_map(i, colors[i])
            self.qtgui_waterfall_sink_x_0.set_line_alpha(i, alphas[i])
        
        self.qtgui_waterfall_sink_x_0.set_intensity_range(-140, 10)
        
        self._qtgui_waterfall_sink_x_0_win = sip.wrapinstance(self.qtgui_waterfall_sink_x_0.pyqwidget(), Qt.QWidget)

        self.blocks_stream_to_vector_0 = blocks.stream_to_vector(gr.sizeof_float*1, N)
        self.udp_source_0 = blocks.udp_source(gr.sizeof_float*1, IP, port, 1472, True)
        self.RadioGIS_mask_0 = RadioGIS.mask(frequencies, amplitudes, N)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.RadioGIS_mask_0, 0), (self.qtgui_vector_sink_f_0, 1))
        self.connect((self.udp_source_0, 0), (self.blocks_stream_to_vector_0, 0))    
        self.connect((self.blocks_stream_to_vector_0, 0), (self.qtgui_vector_sink_f_0, 0))    
        self.connect((self.udp_source_0, 0), (self.qtgui_waterfall_sink_x_0, 0)) 

        self.ctrl_win = control_box()
        self.head_win = header()
        self.ctrl_win.attach_signal(self)

        self.main_box = dialog_box(self.head_win, display_box(self._qtgui_vector_sink_f_0_win), (self._qtgui_waterfall_sink_x_0_win), self.ctrl_win)
        self.main_box.show()

    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "SDR_SA_GUI")
        self.settings.setValue("geometry", self.saveGeometry())
        event.accept()

    def get_port(self):
        return self.port

    def set_port(self, port):
        self.port = port

    def get_gan(self):
        return self.gan

    def set_gan(self, gan):
        self.gan = gan
	self.dino.send({"gan": self.gan})

    def get_fc(self):
        return self.fc

    def set_fc(self, fc):
        if(34000000 + self.ab / 2 < fc < 6016000000 - self.ab / 2):
            self.fc = fc
            self.update_x_axis()
            self.dino.send({"fc": self.fc})

    def get_ab(self):
        return self.ab

    def set_ab(self, ab):
        self.ab = ab
        self.update_x_axis()
	self.dino.send({"ab": self.ab})

    def get_N(self):
        return self.N

    def set_N(self, N):
        self.N = N

    def get_n(self):
        return self.n

    def set_n(self, n):
        self.n = n

    def get_IP(self):
        return self.IP

    def set_IP(self, IP):
        self.IP = IP
	self.dino.send({"IP": self.IP})

    def get_Antena(self):
        return self.Antena

    def set_Antena(self, Antena):
        self.Antena = Antena

    def get_ventana(self):
        return self.ventana

    def set_ventana(self, ventana):
        self.ventana = ventana
	self.dino.send({"ventana": self.ventana})

    def get_base(self):
        return self.base

    def set_base(self, base):
        self.base = base
	self.dino.send({"base": self.base})

    def get_y0(self):
        return self.y0

    def set_y0(self, y0):
        self.y0 = y0
        self.update_y_axis()

    def get_y1(self):
        return self.y1

    def set_y1(self, y1):
        self.y1 = y1
        self.update_y_axis()

    def update_x_axis(self):
        self.qtgui_vector_sink_f_0.set_x_axis((self.fc - self.ab / 2) / 1e6, (self.ab / self.N) / 1e6)
        self.qtgui_waterfall_sink_x_0.set_frequency_range(self.fc - self.ab / 2, self.ab / self.N)

    def update_y_axis(self):
        self.qtgui_vector_sink_f_0.set_y_axis(self.y0, self.y1)
        self.qtgui_waterfall_sink_x_0.set_intensity_range(self.y0, self.y1)

if __name__ == "__main__":
    tb = sdr_spectrum_analyzer();
    tb.start()
    tb.qapp.exec_()
    tb.stop()
