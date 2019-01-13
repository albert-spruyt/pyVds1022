#!/usr/bin/python3
from vds1022 import VDS1022,hexAscii,printBytes
from scope import Scope
from Trace import TraceSet,Trace 
import sys
    
from PyQt5.QtChart import QChart, QChartView, QLineSeries
from PyQt5.QtGui import QPolygonF, QPainter
from PyQt5.QtWidgets import QMainWindow, QHBoxLayout, QVBoxLayout, QPushButton,QWidget,QLabel,QComboBox, QApplication, QCheckBox
from PyQt5.QtCore import pyqtSlot,Qt
import numpy as np

class LabeledComboBox(QComboBox):
    def __init__(self,label='Label',parent=None,items=[],itemLabels=None):
        super(LabeledComboBox, self).__init__(parent=parent)

        layout = QHBoxLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel(label))

        layout.margin =0
        layout.setContentsMargins(0,0,0,0)
    
        self.comboBox = QComboBox()
        layout.addWidget(self.comboBox)
        
        self.hasLabels = False
        if not itemLabels:
            self.comboBox.addItems(items)
        else:
            for item in zip(itemLabels,items):
                self.comboBox.addItem(item[0],item[1])
                self.hasLabels = True

    def getInt(self):
        if self.hasLabels:
            return int(str(self.comboBox.currentData()))
        return int(str(self.comboBox.currentText()))

def series_to_polyline(xdata, ydata):
    """Convert series data to QPolygon(F) polyline
    
    This code is derived from PythonQwt's function named 
    `qwt.plot_curve.series_to_polyline`"""
    size = len(xdata)
    polyline = QPolygonF(size)
    pointer = polyline.data()
    dtype, tinfo = np.float, np.finfo  # integers: = np.int, np.iinfo
    pointer.setsize(2*polyline.size()*tinfo(dtype).dtype.itemsize)
    memory = np.frombuffer(pointer, dtype)
    memory[:(size-1)*2+1:2] = xdata
    memory[1:(size-1)*2+2:2] = ydata
    return polyline    
    
class TestWindow(QMainWindow):
    def __init__(self,scope,parent=None):
        super(TestWindow, self).__init__(parent=parent)

        self.scope = scope
        self.ncurves = 0
        self.chart = QChart()
        self.chart.legend().hide()
        self.view = QChartView(self.chart)
        self.view.setRenderHint(QPainter.Antialiasing)

        controlLayout = QHBoxLayout()
        controlLayout.setContentsMargins(0,0,0,0)
        controlWidget = QWidget()
        controlWidget.setLayout(controlLayout)

        self.runButton = QPushButton("Get")
        controlLayout.addWidget(self.runButton)

        self.voltage1ComboBox = LabeledComboBox(label='Voltage 1',
                items=[ str(x) for x in range(len(VDS1022.vdivs))],
                itemLabels= [ str(x[0]/x[1])+'v' for x in  VDS1022.vdivs ] )

        controlLayout.addWidget(self.voltage1ComboBox)

        self.channel1 = QCheckBox("Channel1")
        controlLayout.addWidget(self.channel1)

        self.voltage2ComboBox = LabeledComboBox(label='Voltage 2',
                items=[ str(x) for x in range(len(VDS1022.vdivs))],
                itemLabels= [ str(x[0]/x[1])+'v' for x in  VDS1022.vdivs ] )

        controlLayout.addWidget(self.voltage2ComboBox)

        self.channel2 = QCheckBox("Channel2")
        controlLayout.addWidget(self.channel2)


        speedVals =  [ 2**x for x in list(range(0,11))]
        self.speedsComboBox = LabeledComboBox(label='Timebase',
                items=[ str(x) for x in speedVals],
                itemLabels=[ str(100. / (x+1)) for x in speedVals] )
        controlLayout.addWidget(self.speedsComboBox)

        self.layout = QVBoxLayout()
        self.layout.addWidget(controlWidget)
        self.layout.addWidget(self.view)

        self.layoutWidget = QWidget()
        self.layoutWidget.setLayout(self.layout)

        self.runButton.clicked.connect(self.on_get)

        self.setCentralWidget(self.layoutWidget)

        self.show()

    @pyqtSlot()
    def on_get(self):
        self.chart.removeAllSeries()

        scope.configure_timebase( self.speedsComboBox.getInt() )

        scope.channel_on(0,self.channel1.isChecked() )
        scope.channel_on(1,self.channel2.isChecked() )

        scope.setVoltage(0,self.voltage1ComboBox.getInt() )
        scope.setVoltage(1,self.voltage2ComboBox.getInt() )

        scope.configure_channel(0)
        scope.configure_channel(1)

        (ch1data,ch2data) = scope_getSamples(self.scope)
        
        if self.channel1.isChecked() :
            self.add_data(range(len(ch1data)),ch1data, color=Qt.red)
        if self.channel2.isChecked() :
            self.add_data(range(len(ch2data)),ch2data, color=Qt.blue)

        self.set_title("Semi live Scope")
        
    def set_title(self, title):
        self.chart.setTitle(title)

    def add_data(self, xdata, ydata,color):
        curve = QLineSeries()
        pen = curve.pen()
        pen.setColor(color)
        pen.setWidthF(.1)
        curve.setPen(pen)
        curve.setUseOpenGL(True)
        curve.append(series_to_polyline(xdata, ydata))
        self.chart.addSeries(curve)
        self.chart.createDefaultAxes()
        self.ncurves += 1

def scope_getSamples(scope):
    scope.capture_start()
    return scope.get_data()

if __name__ == '__main__':
    app = QApplication(sys.argv)

    scope = Scope(voltage=[6,6])
    scope.capture_init()

    window = TestWindow(scope)

    npoints = 1000000
    window.setWindowTitle("Simple performance example")

    window.show()
    window.resize(500, 400)

    sys.exit(app.exec_())
