import usb1,struct,traceback,sys,math
import numpy as np

def AddValueAttachCommand(name,address,length,value):
    ret = struct.pack("<IB",address,length) 
    for i in range(length):
        ret += bytes([value & 0xFF])
        value>>=8 
    return ret


def hexAscii(data):
    return ''.join( d if 0x20 <= ord(d) <= 0x80 else '.' for x in data )

def printBytes(val):
    count = 0 
    for b in val:
        if count % 16 == 0:
            print('')
        count+=1
        print("%2.2x"%b),
    print('')

class VDS1022:
    debug = False
    # Some Device specific USB parameters
    VENDOR_ID =  0x5345
    PRODUCT_ID = 0x1234
    INTERFACE = 0
    BULK_WRITE_ENDPOINT = 0x3
    BULK_READ_ENDPOINT = 0x81
    DEFAULT_RESPONSE_LENGTH = 5

    #calibrationtypes {
    GAIN = 0
    AMPLITUDE = 1
    COMPENSATION = 2

    vdivs = [
	[ 5, 1000 ],
	[ 10, 1000 ],
	[ 20, 1000 ],
	[ 50, 1000 ],
	[ 100, 1000 ],
	[ 200, 1000 ],
	[ 500, 1000 ],
	# volts 
	[ 1, 1 ],
	[ 2, 1 ],
	[ 5, 1 ] 
        ]

    # args are specified as channel-tuples for each setting
    #    voltage # from 0-9
    #    lowpass = [0,0] # from 0-4
    #    channelOn = [0,0] # 0 for off 1 for on
    #    coupling = [0,0] # allowed to be 1,0,2
    def __init__(self,
            voltage=[7,7],
            lowpass=[0,4],
            coupling=[0,0],
            channelOn=[True,False],
            timebase = 0x190,
        ):
        # Save the parameters
        self.voltage = voltage 
        self.lowpass = lowpass
        self.coupling = coupling
        self.channelOn = channelOn
        self.timebase = timebase

        # blaat 
        self.calibration_data = [[[0 for k in range(10)] for j in range(2)] for i in range(3)]


        print("trying to open usb")
        self._openUsb()

        try:
            #Check machine code
            print("Trying to check the machine type")
            version =  self._packed_cmd_response( 0x4001, 86, 1, 'V') # MACHINE_TYPE_ADD
            if version != 1:
                print ("this does not appear to be a VDS")
                raise Exception("This does not appear to be a VDS1022")

            print("This appears to be a VDS1022")

            self.checkBitstreamUpload()

            # read the calibration data
            self.write(AddValueAttachCommand("read_flash", 432, 1, 1))
            calibration_data = self.read(2002)

            printBytes(calibration_data)
            
            self._parse_flash(calibration_data)
        except Exception as e:
            traceback.print_exc()
            print(e)
            self.handle.close()

    def checkBitstreamUpload(self):
            # Check if we need to upload the FPGA bitstream
            response = self._packed_cmd_response( 547, 0, 1, 'E') # FPGA_DOWNLOAD_QUERY_ADD
            
            if response == 0:
                print("uploading bitstream")
                self._uploadBitstream()
                print("done")


    def _uploadBitstream(self,fpgaPath='VDS1022_FPGA_V3.7.bin'):
        with open(fpgaPath,'rb') as fpgaFile:
            bitStream = fpgaFile.read()

        self.write(AddValueAttachCommand('FPGA_DOWNLOAD_ADD',0x4000,4,len(bitStream)))
        bufferSize = self.checkResponse('D')

        if self.debug:
            print("Buffersize: ",bufferSize)

        i = 0 
        while i < 1 + (len(bitStream) // (bufferSize - 4)) : 
            # transfer ID
            if self.debug:
                print('Sending chunk:',i)

            large_buffer = struct.pack('<I',i)

            pos = i * (bufferSize - 4)
            length = bufferSize - 4
            if pos + length > len(bitStream):
                length = len(bitStream) - pos

            large_buffer += bitStream[pos:pos+length]

            self.write(large_buffer)
            response = self.checkResponse('S')

            if response != i:
                raise Exception("Bad response in bitstream upload",hex(i) )

            i+=1

    def _parse_flash(self,buf):
        if buf[0] != 0xaa or buf[1] != 0x55:
            raise Exception("bad flash header")

        version = buf[2] | (buf[3] << 8) | (buf[4] << 16) | (buf[5] << 24)
        if version != 2:
                raise Exception("bad flash version %d", version)

        shortBuf = [ buf[i] + (buf[i+1]<<8) for i in range(6,len(buf),2) ]

        count=0
        for z in range(3):
            for y in range(2):
                for x in range(10):
                    self.calibration_data[z][y][x] = shortBuf[count] & 0xffFF
                    print("%3.3X"%shortBuf[count])
                    count+=1

    def _openUsb(self):
        handle = usb1.USBContext().openByVendorIDAndProductID(
            self.VENDOR_ID,
            self.PRODUCT_ID,
            skip_on_error=True,
        )
        if handle is None:
            print("Device not present, or user is not allowed to access device.")
            sys.exit(-1)
            pass
        handle.claimInterface(self.INTERFACE)
        handle.clearHalt(self.BULK_WRITE_ENDPOINT)

        self.handle = handle

    def write(self,buf, dataLength=None):
        if not dataLength:
            dataLength = len(buf)

        if self.debug:
            print("\nSending: ")
            printBytes(ord(x) for x in buf)
        self.handle.bulkWrite(self.BULK_WRITE_ENDPOINT,buf,dataLength)

    def read(self,dataLength=DEFAULT_RESPONSE_LENGTH):
        ret = self.handle.bulkRead(self.BULK_READ_ENDPOINT,dataLength)
        if self.debug:
            print("\nReceived: ")
            printBytes(ret)
        return ret

    def _packed_cmd_response(self, address, value, length, expectedResponse):
        self.write(AddValueAttachCommand('',address,length,value))
        return self.checkResponse(expectedResponse)

    def checkResponse(self,expected):
        resp = self.read()

        if int(resp[0]) != ord(expected):
            raise Exception("Unexpected response expected:"+expected+"got:"+chr(resp[0]))

        return struct.unpack('<I',resp[1:])[0]

    def configure_channel(self,channel):
        #Channel_ch1/2, bit fields
        #bit 7 channel is on                => 0x80
        #bit 5,6 coupling method ( 1,0,2 )  => 0x20,0,0x40
        #bit 4 no
        #bit 2,3 bandwidth limit            => 0x4,0x8,0xc
        #bit 1 input attenuation            => 0x2
        #bit 0 no   
        channelArg = 0
	# channel_ch1 # This sets the voltage
        print("channel on",self.channelOn)
        if self.channelOn[channel] == True:
            channelArg |= 0x80
        
        #coupling ( 1,0,2)
        channelArg |= ( self.coupling[channel] << 5 )

        #lowpass filter
        channelArg |= ( self.lowpass[channel] << 2 )

        # After voltage 5 we need to set the input attenuation
        if self.voltage[channel] >= 6:
            channelArg |= 0x2

        # send it to the scope
        if channel == 0:
            self._packed_cmd_response( 0x111, channelArg , 1, 'S') # Channel_ch1_ADD
        else:
            self._packed_cmd_response( 0x110, channelArg , 1, 'S') # Channel_ch2_add

	# volt_gain_ch1
        tmp = self.calibration_data[self.GAIN][channel][self.voltage[channel]]

        print('gain',hex(tmp))
        if channel == 0:
            self._packed_cmd_response( 0x116, tmp, 2, 'S')
        else:
            self._packed_cmd_response( 0x114, tmp, 2, 'S')

        # zero_off_ch1
        # TODO: 50 should be adjustable #TODO what is going on here
        tmp = self.calibration_data[self.COMPENSATION][channel][self.voltage[channel]]
        tmp = tmp - (50 * self.calibration_data[self.AMPLITUDE][channel][self.voltage[channel]] // 100)

        if channel == 0:
            self._packed_cmd_response( 0x10a, tmp, 2, 'S')
        else:
            self._packed_cmd_response( 0x108, tmp, 2, 'S')

    # 0x6 = ~16k samples (1 1khz pulse) =  16msps? # at this speed we dont have enough samples to calibrate :(
    # 0xc = ~8k samples (1 1khz pulse) =  8msps? # at this speed we dont have enough samples to calibrate :(
    # 0x18 = ~4k samples (1 1khz pulse) =  4msps?
    # 0x30 = ~2k samples (1 1khz pulse) =  2msps?
    # 0x60 = ~1k samples (1 1khz pulse) =  1msps?
    # 0xc0 = ~500 samples (1 1khz pulse) = 0.5msps

    def configure_timebase(self,timebase=None): 
        if timebase:
            self.timebase = timebase
        # timebase
        self._packed_cmd_response( 0x52, self.timebase, 4, 'S')

        # slowmove
        if self.timebase < 0xffFFffFF: #TODO: when do we need to turn on slow-move?
            self._packed_cmd_response( 0xa, 0, 1, 'S')
        else:
            self._packed_cmd_response( 0xa, 1, 1, 'S')

    def capture_init(self):
        # phase_fine
        self._packed_cmd_response( 0x18, 0x0, 1, 'S') # PHASE_FINE
        self._packed_cmd_response( 0x19, 0x0, 1, 'S') # what is this?

        # trg
        self._packed_cmd_response( 0x24, 0x0, 2, 'S') # TRG_ADD

        # trg_holdoff_arg_ch1
        self._packed_cmd_response( 0x26, 0x0, 1, 'S') # trg_holdoff_arg_ext_ADe

        # trg_holdoff_index_ch1
        self._packed_cmd_response( 0x27, 0x41, 1, 'S') 

        # edge_level_ch1
        self._packed_cmd_response( 0x2e, 0x32, 1, 'S') # pulse_level_ch1_ADD/EDGE LEVEL
        self._packed_cmd_response( 0x2f, 0x28, 1, 'S') # 

        # chl_on: Arg appears to be a bit mask of channels to turn on
        self._packed_cmd_response( 0xb, 0x3, 1, 'S')


        # edge_level_ext?
        self._packed_cmd_response( 0x10c, 0, 1, 'S')

        # TODO: here? #TODO: find out what Alyssa meant

        self.configure_channel(1)
        self.configure_timebase()

        # sample
        self._packed_cmd_response( 0x9, 0, 1, 'S')

        # dm (deep mem)
        self._packed_cmd_response( 0x5c, 0x13ec, 2, 'S')

        # sync output
        self._packed_cmd_response( 0x6,0, 1, 'S')


        # pre_trg
        #self._packed_cmd_response( 0x5a, 0xf1, 1, 'S') # PRE_TRG_ADD
        #self._packed_cmd_response( 0x5b, 0x09, 1, 'S')
        self._packed_cmd_response( 0x5a, 0x00, 1, 'S') # PRE_TRG_ADD
        self._packed_cmd_response( 0x5b, 0x00, 1, 'S')

        # suf_trg
        #self._packed_cmd_response( 0x56, 0xfb, 1, 'S') # SUF_TRG_ADD
        #self._packed_cmd_response( 0x57, 0x09, 1, 'S')
        self._packed_cmd_response( 0x56, 0x88, 1, 'S') # SUF_TRG_ADD
        self._packed_cmd_response( 0x57, 0x13, 1, 'S')
        self._packed_cmd_response( 0x58, 0, 1, 'S')
        self._packed_cmd_response( 0x59, 0, 1, 'S')

        # edge_level_ext (again)

    def capture_start(self):
        self._packed_cmd_response( 0x10c, 1, 1, 'S')

    def get_data_ready(self):
	#trg_d
        self._packed_cmd_response( 0x1, 0, 1, 'S')

	# datafinished
        return self._packed_cmd_response( 0x7a, 0, 1, 'S')

    def get_data(self):
        self.write(AddValueAttachCommand('',0x1000,2,0x0101)) # getdata_ADD
        #self.write(AddValueAttachCommand('',0x1000,2,0x0505)) # getdata_ADD

        ret = [ [],[] ]

        for i in range(2):
            buf = self.read(5200 + 11 )

            if len(buf) != 5211:
                # probably EBUSY
                raise Exception("got incoming packet of size %d, that's bad: ", len(buf))
                # ouch

            channel = buf[0]
            if channel < 0 or channel > 1:
                    raise Exception ("invalid channel %d", channel)

            num_samples = (5000 - 2) + 50 + 50

            analog_data = np.zeros(num_samples,dtype='float32')

            #
            Range = (float(self.vdivs[self.voltage[channel]][0]) / self.vdivs[self.voltage[channel]][1]) * 255
            vdivlog = math.log10(Range / 255)
            #digits = -(int)vdivlog + (vdivlog < 0.0)

            # the layout is [11 bytes header] + [100 bytes trigger buffer] + [50 bytes pre] + [1000 bytes payload] + [50 bytes post]
            # the pre/payload/post seems to all be valid data
            # owon use only the payload, offset by 1 point, looks like they're trying to avoid some problem when triggering on square waves (sometimes you get a bad sample (or even two) at the start of the pre), idk

            data_in = np.frombuffer( buf[ 11 + 100 + 1:], '<i1')
            #data_in = buf[ 11 + 100 + 1:]

            for i in range(num_samples):
                    #define ZEROOFF_HACK 50 // also in protocol.c :/
                    ZEROOFF_HACK = 50
                    analog_data[i] = Range / 255 * float(data_in[i]) - ZEROOFF_HACK
                    #analog_data[i] = data_in[i]

            ret[channel] = analog_data

        return ret

    def force_trigger(self):
        self._packed_cmd_response( 0xc, 0x3, 1, 'S') # FORCETRIG_add
        return

    def close(self):
        if self.handle:
            self.handle.close()
            self.handle = None
