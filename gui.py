#!/usr/bin/python3
from vds1022 import VDS1022,printBytes
from scope import Scope
from Trace import TraceSet,Trace 
import sys
    
from PyQt5.QtGui import QPolygonF, QPainter, QPen
from PyQt5.QtWidgets import QMainWindow, QHBoxLayout, QVBoxLayout, QPushButton,QWidget,QLabel,QComboBox, QApplication, QCheckBox, QLineEdit
from PyQt5.QtCore import pyqtSlot, Qt, QTimer
import numpy as np
import pyqtgraph as pg

class LabeledComboBox(QWidget):
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

    def setCurrentIndex(self,index):
        self.comboBox.setCurrentIndex(index)

class LabeledLineEdit(QWidget):
    def __init__(self,label='Label',parent=None,text='text'):
        super(LabeledLineEdit, self).__init__(parent=parent)

        layout = QHBoxLayout()
        self.setLayout(layout)
        layout.addWidget(QLabel(label))

        layout.margin =0
        layout.setContentsMargins(0,0,0,0)
    
        self.lineEdit = QLineEdit()
        self.lineEdit.setText(text)
        layout.addWidget(self.lineEdit)

    def getText(self):
        return self.lineEdit.text()
        

def series_to_polyline(xdata, ydata,timebase):
    """Convert series data to QPolygon(F) polyline
    
    This code is derived from PythonQwt's function named 
    `qwt.plot_curve.series_to_polyline`"""
    size = len(xdata)
    polyline = QPolygonF(size)
    pointer = polyline.data()
    dtype, tinfo = np.float, np.finfo  # integers: = np.int, np.iinfo
    pointer.setsize(2*polyline.size()*tinfo(dtype).dtype.itemsize)
    memory = np.frombuffer(pointer, dtype)
    memory[:(size-1)*2+1:2] = np.array(xdata) / timebase
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
        self.channelOn.setChecked(True)
        layout.addWidget(self.channelOn)

        self.voltageComboBox = LabeledComboBox(label='Voltage',
                items=[ str(x) for x in range(len(VDS1022.vdivs))],
                itemLabels= [ str(x[0]/x[1])+'v per div' for x in  VDS1022.vdivs ],
                parent=self,
            )
        self.voltageComboBox.setCurrentIndex(6)

        self.couplingComboBox = LabeledComboBox(label='Coupling',
                items=map(str,scope.couplingOrdinals),
                itemLabels=scope.couplingNames,
                parent=self,
            ) 

        layout.addWidget(self.voltageComboBox)
        layout.addWidget(self.couplingComboBox)

    def getParams(self):
        return {
                'on': self.channelOn.isChecked(),
                'voltage': self.voltageComboBox.getInt(),
                'coupling': self.couplingComboBox.getInt(),
            }

class ScopeTriggerWidget(QWidget):
    def __init__(self,name):
        super(ScopeTriggerWidget, self).__init__()

        layout = QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)
        layout.addWidget(QLabel(name))

        self.triggerTypeComboBox = LabeledComboBox(label='Trigger Mode',
                items=map(str,scope.trgTypeOrdinals),
                itemLabels=scope.trgTypeNames,
                parent=self,
            )
#        self.triggerType.setCurrentIndex(3)

        self.triggerChannelComboBox = LabeledComboBox(label='Trigger Channel',
                items=map(str,scope.trgChannelOrdinals),
                itemLabels=scope.trgChannelNames,
                parent=self,
            )
        self.triggerPulseLow = LabeledComboBox(label='Pulse low',
                items=[ str(x) for x in range(-128,127,10)],
                itemLabels=[ str(x) for x in range(-128,127,10)],
                parent=self,
            )
        self.triggerPulseHigh = LabeledComboBox(label='Pulse high',
                items=[ str(x) for x in range(-128,127,10)],
                itemLabels=[ str(x) for x in range(-128,127,10)],
                parent=self,
            )

        layout.addWidget(self.triggerChannelComboBox)
        layout.addWidget(self.triggerTypeComboBox)
        layout.addWidget(self.triggerPulseLow)
        layout.addWidget(self.triggerPulseHigh)

    def getParams(self):
        return {
                'triggerChannel': self.triggerChannelComboBox.getInt(),
                'triggerMode': self.triggerTypeComboBox.getInt(),
                'pulseHigh': self.triggerPulseHigh.getInt(),
                'pulseLow': self.triggerPulseLow.getInt(),
            }


    
class TestWindow(QMainWindow):
    def __init__(self,scope,parent=None):
        super(TestWindow, self).__init__(parent=parent)

        self.scope = scope
        self.chart = pg.GraphicsLayoutWidget()
        self.plot = self.chart.addPlot()
        self.plot1 = self.plot.plot([], [], pen=(255,0,0))
        self.plot2 = self.plot.plot([], [], pen=(0,255,0))

        controlLayout = QHBoxLayout()
        controlLayout.setContentsMargins(0,0,0,0)
        controlWidget = QWidget()
        controlWidget.setLayout(controlLayout)

        self.runButton = QPushButton("Get")
        controlLayout.addWidget(self.runButton)

        self.autoCheckBox = QCheckBox("Auto")
        controlLayout.addWidget(self.autoCheckBox)

        self.speedsComboBox = LabeledComboBox(label='Timebase',
                items= self.scope.timebaseValues,
                itemLabels=[str(x) for x in self.scope.timebaseNames],
            )
        controlLayout.addWidget(self.speedsComboBox)

        self.trg_pre = LabeledComboBox(label='trg_pre',
                items= [ str(x) for x in range(0,100000,1000) ],
                itemLabels= [ str(x) for x in range(0,100000,1000) ],
            )
        self.trg_suf = LabeledComboBox(label='trg_suf',
                items= [ str(x) for x in range(0,100000,1000) ],
                itemLabels= [ str(x) for x in range(0-5000,100000-5000,1000) ],
            )
        self.trg_suf.setCurrentIndex(5)

        self.trg = ScopeTriggerWidget('trigger') 

        controlLayout.addWidget(self.speedsComboBox)
        controlLayout.addWidget(self.trg_suf)
        controlLayout.addWidget(self.trg_pre)

        self.timeout = LabeledLineEdit(label="Timeout",text="1.0")
        controlLayout.addWidget(self.timeout)

        self.layout = QVBoxLayout()
        self.layout.addWidget(controlWidget)
        self.channels = [ ScopeChannelWidget('1'), ScopeChannelWidget('2') ]
        self.layout.addWidget(self.channels[0])
        self.layout.addWidget(self.channels[1])
        self.layout.addWidget(self.trg)
        self.layout.addWidget(self.chart)

        self.layoutWidget = QWidget()
        self.layoutWidget.setLayout(self.layout)

        self.runButton.clicked.connect(self.on_get)

        self.setCentralWidget(self.layoutWidget)

        self.show()

    @pyqtSlot()
    def on_get(self):
        #self.chart.removeAllSeries() # FIXME
        self.plot1.setData([],[])
        self.plot2.setData([],[])

        # Configure Scope
        scope.configure_timebase( self.speedsComboBox.getInt() )

        scope.configure_trg_pre(self.trg_pre.getInt() )
        scope.configure_trg_suf(self.trg_suf.getInt() )

        scope.timeout = float(self.timeout.getText())

        for i in [0,1]:
            params = self.channels[i].getParams() 
            scope.setVoltage(i,params['voltage'])
            scope.setCoupling(i,params['coupling'])

            scope.configure_channel(i)

        trgParams = self.trg.getParams()

        scope.configure_trg(trgParams['triggerMode'],trgParams['triggerChannel'])
        scope.configure_trg_edge_level( (trgParams['pulseHigh'] << 8) | trgParams['pulseLow'] )


        self.scope.capture_start()


        # Get the data and plot it
        (ch1data,ch2data) = self.scope.get_data()
       
        # TODO: set it only when user changes vdiv?
        range1 = self.scope.scope.get_range(0)
        range2 = self.scope.scope.get_range(1)
        self.plot.getViewBox().setYRange(min(range1[0], range2[0]), max(range1[1], range2[1]))

        timebaseVal = scope.timebaseDiv[scope.timebaseValues.index(self.speedsComboBox.getInt())] 

        if self.channels[0].getParams()['on']:
            self.add_data(self.plot1, ch1data, Qt.red,timebaseVal)
        if self.channels[1].getParams()['on']:
            self.add_data(self.plot2, ch2data, Qt.blue,timebaseVal)

        if self.autoCheckBox.isChecked():
            QTimer.singleShot(200,self.on_get)
        
    def add_data(self, plot, ydata,color,timebase):
        plot.setData(np.array(range(len(ydata))) / timebase, np.array(ydata))

if __name__ == '__main__':
    app = QApplication(sys.argv)

    scope = Scope()

    window = TestWindow(scope)

    window.setWindowTitle("Owon VDS1022 GUI")
    window.show()
    window.resize(1000, 400)

    ret = app.exec_()
    scope.close() # close background thread
    sys.exit(ret)
