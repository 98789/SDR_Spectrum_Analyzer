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

from gnuradio import gr
from gnuradio import blocks
from PyQt4 import Qt
from gnuradio import analog
from gnuradio import eng_notation
from gnuradio import fft
from gnuradio import gr
from gnuradio import uhd
from gnuradio.eng_option import eng_option
from gnuradio.fft import window
from gnuradio.filter import firdes
from optparse import OptionParser
from remote_configurator import remote_configurator
import baz
import sip
import sys

try:
    from gnuradio import qtgui
    from PyQt4 import QtGui, QtCore
    import sip
except ImportError:
    sys.stderr.write("Error: Program requires PyQt4 and gr-qtgui.\n")
    sys.exit(1)

try:
    from gnuradio import analog
except ImportError:
    sys.stderr.write("Error: Program requires gr-analog.\n")
    sys.exit(1)

try:
    from gnuradio import channels
except ImportError:
    sys.stderr.write("Error: Program requires gr-channels.\n")
    sys.exit(1)

class dialog_box(QtGui.QWidget):
    def __init__(self, header, display, control):
        QtGui.QWidget.__init__(self, None)
        self.setWindowTitle('SDR Spectrum Analyzer')
	self.showMaximized()

        self.vertlayout = QtGui.QVBoxLayout(self)
        self.vertlayout.addWidget(header)
        self.body = QtGui.QWidget()
        self.boxlayout = QtGui.QHBoxLayout()
        self.boxlayout.addWidget(control, 1)
        self.boxlayout.addWidget(display)
        self.body.setLayout(self.boxlayout)
        self.vertlayout.addWidget(self.body)

#        self.resize(800, 500)

class header(QtGui.QWidget):
    def __init__(self, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setWindowTitle('Header')

        self.hbox = QtGui.QHBoxLayout(self)
        self.hbox.setObjectName("BlueSquare")
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
        self.tab1.setObjectName("BlueSquare")
        self.tab2 = QtGui.QWidget()
        self.tab2.setObjectName("BlueSquare")

        self.configButton = QtGui.QPushButton("Configuracion")
        self.stopButton = QtGui.QPushButton("Stop")

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

        self.sel_base = QtGui.QComboBox(self)
        bases = ["Exponencial Compleja",
                  "Triangular",
                  "Funcion de Potencia",
                   "Binomial"]
        for base in bases:
            self.sel_base.addItem(base)
        self.sel_base.setMinimumWidth(100)
        self.conf_an.addRow("Base:", self.sel_base)

        self.sel_escala = QtGui.QComboBox(self)
        escalas = ["dBm",
                  "Lineal"]
        for escala in escalas:
            self.sel_escala.addItem(escala)
        self.sel_escala.setMinimumWidth(100)
        self.conf_an.addRow("Escala:", self.sel_escala)

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
#            self.amp2Edit.setText(QtCore.QString("%1").arg(self.signal2.amplitude()))

    def IP_edit_text(self):
        try:
	    newIP = str(self.sel_IP.text())
            self.signal.set_IP(newIP)
        except ValueError:
	    print "Wrong IP format"

    def puerto_edit_text(self):
        try:
	    newPuerto = str(self.sel_IP.text())
            self.signal.set_puerto(newPuerto)
        except ValueError:
	    print "Invalid port"

    def span_edit_text(self):
        try:
	    newSpan = float(self.sel_span.text())
            self.signal.set_ab(newSpan)
        except ValueError:
	    print "Unsupported span value"

    def fc_edit_text(self):
        try:
	    newFc = float(self.sel_fc.text())
            self.signal.set_fc(newFc)
        except ValueError:
	    print "Invalid center frequency"

    def ganancia_edit_text(self):
        try:
	    newGanancia = float(self.sel_ganancia.text())
            self.signal.set_gan(newGanancia)
        except ValueError:
	    print "Gain out of range"

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
        self.IP = IP = "192.168.0.104"
        self.Antena = Antena = "RX2"
	self.remote_IP = "192.168.0.103"
        self.dino = remote_configurator(self.remote_IP, self.port)

        ##################################################
        # Blocks
        ##################################################
        self.qtgui_time_sink_x_0 = qtgui.time_sink_f(
        	1024, #size
        	fc, #samp_rate
        	"", #name
        	1 #number of inputs
        )
        self.qtgui_time_sink_x_0.set_update_time(0.10)
        self.qtgui_time_sink_x_0.set_y_axis(-1, 1)

#        self.qtgui_time_sink_x_0.set_x_label("Frecuencia", "")
        self.qtgui_time_sink_x_0.set_y_label("Amplitud", "Hz")
        
        self.qtgui_time_sink_x_0.enable_tags(-1, True)
        self.qtgui_time_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_time_sink_x_0.enable_autoscale(True)
        self.qtgui_time_sink_x_0.enable_grid(False)
        self.qtgui_time_sink_x_0.enable_control_panel(False)
        
        if not True:
          self.qtgui_time_sink_x_0.disable_legend()
        
        labels = ["", "", "", "", "",
                  "", "", "", "", ""]
        widths = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
                  "magenta", "yellow", "dark red", "dark green", "blue"]
        styles = [1, 1, 1, 1, 1,
                  1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
                   -1, -1, -1, -1, -1]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
                  1.0, 1.0, 1.0, 1.0, 1.0]
        
        for i in xrange(1):
            if len(labels[i]) == 0:
                self.qtgui_time_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_time_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_time_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_time_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_time_sink_x_0.set_line_style(i, styles[i])
            self.qtgui_time_sink_x_0.set_line_marker(i, markers[i])
            self.qtgui_time_sink_x_0.set_line_alpha(i, alphas[i])
        
        self._qtgui_time_sink_x_0_win = sip.wrapinstance(self.qtgui_time_sink_x_0.pyqwidget(), Qt.QWidget)
        self.baz_udp_source_0 = baz.udp_source(gr.sizeof_float*1, IP, port, 1472, True, True, False, False)

        ##################################################
        # Connections
        ##################################################
        self.connect((self.baz_udp_source_0, 0), (self.qtgui_time_sink_x_0, 0))   

        self.ctrl_win = control_box()
        self.head_win = header()
        self.ctrl_win.attach_signal(self)

        self.main_box = dialog_box(self.head_win, display_box(self._qtgui_time_sink_x_0_win), self.ctrl_win)
        self.main_box.show()

    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "GUI_test")
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
	self.dino.send({"gan":self.gan})

    def get_fc(self):
        return self.fc

    def set_fc(self, fc):
        self.fc = fc
	self.dino.send({"fc":self.fc})

    def get_ab(self):
        return self.ab

    def set_ab(self, ab):
        self.ab = ab
	self.dino.send({"ab":self.ab})

    def get_N(self):
        return self.N

    def set_N(self, N):
        self.N = N

    def get_IP(self):
        return self.IP

    def set_IP(self, IP):
        self.IP = IP
	self.dino.send({"IP":self.IP})

    def get_Antena(self):
        return self.Antena

    def set_Antena(self, Antena):
        self.Antena = Antena


if __name__ == "__main__":
    tb = sdr_spectrum_analyzer();
    tb.start()
    tb.qapp.exec_()
    tb.stop()
