#!/usr/bin/python3
from vds1022 import VDS1022,printBytes
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

class ScopeChannelWidget(QWidget):
    def __init__(self,name):
        super(ScopeChannelWidget, self).__init__()

        layout = QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)
        layout.addWidget(QLabel(name))

        self.channelOn = QCheckBox("on")
        layout.addWidget(self.channelOn)

        self.voltageComboBox = LabeledComboBox(label='Voltage',
                items=[ str(x) for x in range(len(VDS1022.vdivs))],
                itemLabels= [ str(x[0]/x[1])+'v' for x in  VDS1022.vdivs ]
            )

        items = [ str(x) for x in [1,0,2]]
        self.couplingComboBox = LabeledComboBox(label='Coupling',
                items=items,
                itemLabels=items,
            ) 

        items = [str(x) for x in [0,1,2,3]]
        self.lowpassComboBox = LabeledComboBox(label='Lowpass',
                items=items,
                itemLabels=items
            )

        layout.addWidget(self.voltageComboBox)
        layout.addWidget(self.couplingComboBox)
        layout.addWidget(self.lowpassComboBox)

    def getParams(self):
        return {
                'on': self.channelOn.isChecked(),
                'voltage': self.voltageComboBox.getInt(),
                'coupling': self.couplingComboBox.getInt(),
                'lowpass': self.lowpassComboBox.getInt(),
            }

    
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

        speedVals =  [ 2**x for x in list(range(0,11))]
        self.speedsComboBox = LabeledComboBox(label='Timebase',
                items=[ str(x) for x in speedVals],
                itemLabels=[ str(100. / (x+1)) for x in speedVals]
            )
        controlLayout.addWidget(self.speedsComboBox)

        self.trg_pre = LabeledComboBox(label='trg_pre',
                items= [ str(x) for x in range(0,50000,1000) ],
                itemLabels= [ str(x) for x in range(0,50000,1000) ],
            )
        self.trg_suf = LabeledComboBox(label='trg_suf',
                items= [ str(x) for x in range(0,50000,1000) ],
                itemLabels= [ str(x) for x in range(0,50000,1000) ],
            )
        controlLayout.addWidget(self.speedsComboBox)
        controlLayout.addWidget(self.trg_suf)
        controlLayout.addWidget(self.trg_pre)

        self.layout = QVBoxLayout()
        self.layout.addWidget(controlWidget)
        self.channels = [ ScopeChannelWidget('1'), ScopeChannelWidget('2') ]
        self.layout.addWidget(self.channels[0])
        self.layout.addWidget(self.channels[1])
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

        scope.configure_trg_pre(self.trg_pre.getInt() )
        scope.configure_trg_suf(self.trg_suf.getInt() )

        for i in [0,1]:
            params = self.channels[i].getParams() 
            scope.setVoltage(i,params['voltage'])
            scope.setCoupling(i,params['coupling'])
            scope.setLowpass(i,params['lowpass'])

            scope.configure_channel(i)

        (ch1data,ch2data) = scope_getSamples(self.scope)
        
        if self.channels[0].getParams()['on']:
            self.add_data(range(len(ch1data)),ch1data, color=Qt.red)
        if self.channels[1].getParams()['on']:
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

    scope = Scope()
    scope.capture_init()

    window = TestWindow(scope)

    window.setWindowTitle("Simple performance example")
    window.show()
    window.resize(1000, 400)

    sys.exit(app.exec_())
