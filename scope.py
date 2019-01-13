from queue import Queue
from threading import Thread
from vds1022  import VDS1022 
import time

def runThread(scope,cmdQueue,outQueue):
    #while no commands
    try:
        scope.capture_init()
        while True:
            if not cmdQueue.empty():
                (cmd,args) = cmdQueue.get()
                print( "Thread Received",cmd)

                if cmd == 'configure_timebase':
                    scope.configure_timebase(args[0])
                elif cmd == 'configure_channel':
                    print ("Configureing channel,",args[0] )
                    scope.configure_channel(args[0])
                elif cmd == 'capture_init':
                    scope.capture_init()
                    pass
                elif cmd == 'capture_start':
                    scope.capture_start()
                elif cmd ==  'get_data':
                    print("waiting for data ready")
                    timeout = time.time() + 3
                    timedOut = False
                    while scope.get_data_ready() == 0:
                        if timeout < time.time():
                            timedOut = True
                            break
                    if not timedOut:
                        print("Data ready")
                        outQueue.put(scope.get_data())
                    else:
                        print("Timedout")
                        scope.force_trigger()
                        outQueue.put([ [],[] ])
                elif cmd == 'close':
                    break
                else:
                    print("Received an unknown command",cmd)
                    break

            else:
                # Wait 10ms so as not to use too much CPU time.
                time.sleep(0.01)
                #print("check bitstream")
                scope.checkBitstreamUpload()

    except Exception as e:
        print("Exception in thread",e)
    scope.close()

class Scope():
    def __init__(self,
            voltage=[7,1],
            lowpass=[0,0],
            coupling=[0,0],
            channelOn=[True,False],
            timebase = 0x190,
            ):
   
        print("making a scope")
        self.scope = VDS1022(voltage,lowpass,coupling,channelOn,timebase)
        print("made a scope")

        self.cmdQueue = Queue(10)
        self.outQueue = Queue(10)


        try:
            print("Trying to make new thread")
            self.thread = Thread(target=runThread,args=(self.scope,self.cmdQueue,self.outQueue))
            self.thread.start()
            
        except Exception as e:
            print("Unable to start thread",e)

    def configure_timebase(self,speed):
        self.cmdQueue.put(['configure_timebase',[speed]])

    def configure_channel(self,channel):
        self.cmdQueue.put(['configure_channel',[channel]])

    def close():
        self.cmdQueue.put(['close',[]])

    def capture_init(self):
        self.cmdQueue.put(['capture_init',[]])

    def capture_start(self):
        self.cmdQueue.put(['capture_start',[]])

    def get_data(self):
        self.cmdQueue.put(['get_data',[]])

        return self.outQueue.get()
      
    def channel_on(self,channelIdx,on):
        self.scope.channelOn[channelIdx] = on

    def setVoltage(self,channelIdx,voltage):
        self.scope.voltage[channelIdx] = voltage
   
