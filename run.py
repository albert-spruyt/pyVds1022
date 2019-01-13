#!/usr/bin/python3
from vds1022 import VDS1022,hexAscii,printBytes
from Trace import TraceSet,Trace 
import sys

scope = VDS1022(voltage=[6,6])

outputFile=sys.argv[1]

ts = TraceSet()
titleLen=0
dataLen=0
numSamples=5098
ts.new(outputFile,titleLen,TraceSet.CodingFloat,dataLen,int(numSamples),[0,0])
scope.capture_init()

try:
    for i in range(3):
        scope.configure_timebase(0xc)
        scope.capture_start()

        while scope.get_data_ready() == 0:
            pass

        print('i',i)
        data  = scope.get_data()

        ts.addTrace(Trace('',[],data[0]))
        #ts.addTrace(Trace('',[],data[1]))
except Exception as e:
    scope.close()

ts.close()
