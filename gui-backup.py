from vds1022 import VDS1022,hexAscii,printBytes
from Trace import TraceSet,Trace 
import sys

#ts.close()
    
from PyQt5.QtChart import QChart, QChartView, QLineSeries
from PyQt5.QtGui import QPolygonF, QPainter
from PyQt5.QtWidgets import QMainWindow, QHBoxLayout, QVBoxLayout, QPushButton,QWidget
from PyQt5.QtCore import pyqtSlot
import numpy as np


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

        self.runButton = QPushButton("Get")

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.runButton)
        self.layout.addWidget(self.view)

        self.layoutWidget = QWidget()
        self.layoutWidget.setLayout(self.layout)

        self.runButton.clicked.connect(self.on_get)

        self.setCentralWidget(self.layoutWidget)

        self.show()

    @pyqtSlot()
    def on_get(self):
        print("clicked run")

        self.chart.removeAllSeries()
        (ch1data,ch2data) = scope_getSamples(self.scope)
        self.add_data(range(len(ch1data)),ch1data,  color=Qt.red)
        self.add_data(range(len(ch2data)),ch2data,  color=Qt.blue)
        self.set_title("Semi live Scope")

        
    def set_title(self, title):
        self.chart.setTitle(title)

    def add_data(self, xdata, ydata, color=None):
        curve = QLineSeries()
        pen = curve.pen()
        if color is not None:
            pen.setColor(color)
        pen.setWidthF(.1)
        curve.setPen(pen)
        curve.setUseOpenGL(True)
        curve.append(series_to_polyline(xdata, ydata))
        self.chart.addSeries(curve)
        self.chart.createDefaultAxes()
        self.ncurves += 1

    def clear(self):
        self.chart.clear()
        self.chart.draw()




def init_scope():
    print("making scope")
    scope = VDS1022(voltage=[6,6])

    print("capture init")
    scope.capture_init()
    return scope


def scope_getSamples(scope):
    scope.capture_start()

    while scope.get_data_ready() == 0:
        pass

    return scope.get_data()

    #        ts.addTrace(Trace('',[],data[0]))
    #        #ts.addTrace(Trace('',[],data[1]))
    #except Exception as e:
    #    scope.close()


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt
    app = QApplication(sys.argv)


    scope = init_scope()
    window = TestWindow(scope)


    npoints = 1000000
    window.setWindowTitle("Simple performance example")


    window.show()
    window.resize(500, 400)

    sys.exit(app.exec_())

 
