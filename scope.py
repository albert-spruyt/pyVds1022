from queue import Queue
from threading import Thread
from vds1022  import VDS1022 
import time,traceback

# Scope is the interface the application talks to.
# The reason for this is that to ensure proper scope operation it must be continually polled (for some reason)
def runThread(parent,cmdQueue,outQueue):
    scope = parent.scope
    close=False
    while not close:
        try:
            scope.capture_init()
            while not close:
                if not cmdQueue.empty():
                    (cmd,args) = cmdQueue.get()
                    if cmd == 'configure_timebase':
                        scope.configure_timebase(args[0])
                    elif cmd == 'configure_channel':
                        scope.configure_channel(args[0])
                    elif cmd == 'capture_init':
                        scope.capture_init()
                    elif cmd == 'capture_start':
                        scope.capture_start()
                        outQueue.put([ [],[] ])
                    elif cmd ==  'get_data':
                        print("waiting for data ready")
                        timeout = time.time() + parent.timeout
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
                    elif cmd == 'trg_pre':
                        scope.configure_trg_pre(args[0])
                    elif cmd == 'trg_suf':
                        scope.configure_trg_suf(args[0])
                    elif cmd == 'trg_edge_level':
                        scope.configure_trg_edge_level(args[0])
                    elif cmd == 'trg':
                        scope.configure_trg(args[0],args[1])
                    elif cmd == 'close':
                        close=True
                        break
                    else:
                        print("Received an unknown command",cmd)
                        close=True
                        break

                else:
                    # Wait 10ms so as not to use too much CPU time.
                    time.sleep(0.01)
                    scope.checkBitstreamUpload()

        except Exception as e:
            print("Exception in thread",e)
            print(traceback.format_exc())
    scope.close()


class Scope():

    # Timebase
    timebaseNames = ['100MSP', '50MSPS', '32MSPS', '16MSPS','8MSPS','4MSPS','2MSPS','1MSPS','500KSPS','250KSPS','125KSPS','62KSPS']
    timebaseValues = [     0x1,    0x02 ,     0x3 ,      0x6,   0x18,   0x30,   0x60,   0xc0,    0x180,    0x300,    0x600,  0xc00 ]
    timebaseDiv   = [100/1e-6, 50/1e-6 , 32/1e-6 ,  16/1e-6, 8/1e-6, 4/1e-6, 2/1e-6, 1/1e-6, 500/1e-3, 250/1e-3, 125/1e-3, 62/1e-3] 


    couplingNames    = ['DC','AC','Ground']
    couplingOrdinals = [   1,   0,       2]
    #Trigger

    trgTypeNames =     [ 'Edge','Video','Slope','Pulse' ]
    trgTypeOrdinals =  [     0 ,     2 ,    1  ,     3  ]

    trgChannelNames    = ["Channel 1","Channel 2","External"]
    trgChannelOrdinals = [          0,          1,         2]

    def __init__(self,
            voltage=[7,1],
            coupling=[0,0],
            channelOn=[True,False],
            timebase = 0x190,
            trg_suf=5000,
            trg_pre=0,
            timeout=1,
            ):


        self.timeout = timeout
        print("making a scope")
        self.scope = VDS1022(voltage,coupling,channelOn,timebase,trg_suf,trg_pre)
        print("made a scope")

        self.cmdQueue = Queue(10)
        self.outQueue = Queue(10)


        print("in scope constructor timebase",timebase)
        try:
            print("Trying to make new thread")
            self.thread = Thread(target=runThread,args=(self,self.cmdQueue,self.outQueue))
            self.thread.start()
            self.configure_timebase(timebase)
            
        except Exception as e:
            print("Unable to start thread",e)

    def configure_timebase(self,speed):
        self.cmdQueue.put(['configure_timebase',[speed]])

    def configure_channel(self,channel):
        self.cmdQueue.put(['configure_channel',[channel]])

    def close(self):
        self.cmdQueue.put(['close',[]])

    def capture_init(self):
        self.cmdQueue.put(['capture_init',[]])

    def arm(self):
        return self.capture_start()

    def capture_start(self):
        self.cmdQueue.put(['capture_start',[]])
        return self.outQueue.get()

    def get_data(self):
        self.cmdQueue.put(['get_data',[]])

        return self.outQueue.get()
      
    def channel_on(self,channelIdx,on):
        self.scope.channelOn[channelIdx] = on

    def setVoltage(self,channelIdx,voltage):
        self.scope.voltage[channelIdx] = voltage

    def setCoupling(self,channelIdx,coupling):
        self.scope.coupling[channelIdx] = coupling
   
    def configure_trg_suf(self,val):
        self.cmdQueue.put(['trg_suf',[val]])

    def configure_trg_pre(self,val):
        self.cmdQueue.put(['trg_pre',[val]])

    def configure_trg_edge_level(self,val):
        self.cmdQueue.put(['trg_edge_level',[val]])

    def configure_trg(self,triggerType,triggerChannel):
        self.cmdQueue.put(['trg',[triggerType,triggerChannel]])

    def reconnect(self):
        pass

