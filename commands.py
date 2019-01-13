import struct
class AddressAttachCommand:
    def __init__(self,nameString,address,length):
        self.name = nameString
        self.address = address
        self.length = length

    def toBuf(self,value=1):
        ret = struct.pack("<IB",self.address,self.length) 
        for i in range(self.length):
            ret += bytes([value & 0xFF])
            value>>=8 
        return ret

class AddValueAttachCommand(AddressAttachCommand):
    def __init__(self,nameString,address,length,value):
        AddressAttachCommand.__init__(self,nameString,address,length)
        self.value = value

    def toBuf(self):
        ret = struct.pack("<IB",self.address,self.length) 
        value = self.value
        for i in range(self.length):
            ret += bytes([value & 0xFF])
            value>>=8 
        return ret

def unpackCommand(buf):
    (address,length) = struct.unpack('<IB',buf[0:5])
    data = struct.unpack('<' + str(length) + 'B',buf[4:length] )[0]
    return (address,length,data)

class Commands:
    commands = [ 
        AddValueAttachCommand("FPGA_DOWNLOAD_ADD", 16384, 4, 1),
        AddValueAttachCommand("MACHINE_TYPE_ADD", 16385, 1, 86),
        AddValueAttachCommand("FPGA_DOWNLOAD_QUERY_ADD", 547, 1, 0),
        AddValueAttachCommand("read_flash", 432, 1, 1),
        AddValueAttachCommand("trg_d_ADD", 1, 1, 0),
        AddValueAttachCommand("write_flash", 416, 1, 1),
        AddressAttachCommand("ADD_CH1_FreqRef", 74, 1), 
        AddressAttachCommand("ADD_CH2_FreqRef", 75, 1) ,
        AddressAttachCommand("CHECK_STOP_ADD", 177, 1),
        AddressAttachCommand("CHL_ON_ADD", 11, 1),
        AddressAttachCommand("DM_ADD", 92, 2),
        AddressAttachCommand("EMPTY_ADD", 268, 1),
        AddressAttachCommand("FORCETRG_ADD", 12, 1),
        AddressAttachCommand("GETDATA2_ADD", 8192, 2),
        AddressAttachCommand("MULTIFREQ_ADD", 80, 1),
        AddressAttachCommand("PF_ADD", 7, 1),
        AddressAttachCommand("PHASE_FINE", 24, 2),
        AddressAttachCommand("PREGET_SLOW_ADD", 12, 1),
        AddressAttachCommand("PRE_TRG_ADD", 90, 2),
        AddressAttachCommand("RE_COLLECT", 3, 1),
        AddressAttachCommand("RUNSTOP_ADD", 97, 1),
        AddressAttachCommand("SAMPLE_ADD", 9, 1),
        AddressAttachCommand("SLOWMOVE_ADD", 10, 1),
        AddressAttachCommand("SUF_TRG_ADD", 86, 4),
        AddressAttachCommand("SYNCOUTPUT_ADD", 6, 1),
        AddressAttachCommand("TIMEBASE_ADD", 82, 4),
        AddressAttachCommand("TRG_ADD", 36, 2),
        AddressAttachCommand("TRG_D_ADD", 1, 1),
        AddressAttachCommand("VIDEOLINE_ADD", 50, 2),
        AddressAttachCommand("VIDEOTRGD_ADD", 2, 1),
        AddressAttachCommand("channel_ch1_ADD", 273, 1),
        AddressAttachCommand("channel_ch1_ADD", 273, 1), 
        AddressAttachCommand("channel_ch2_ADD", 272, 1) ,
        AddressAttachCommand("channel_ch2_ADD", 272, 1),
        AddressAttachCommand("datafinished_ADD", 122, 1),
        AddressAttachCommand("edge_level_ch1_ADD", 46, 2),
        AddressAttachCommand("edge_level_ch1_ADD", 46, 2), 
        AddressAttachCommand("edge_level_ch2_ADD", 48, 2), 
        AddressAttachCommand("edge_level_ext_ADD", 268, 1) ,
        AddressAttachCommand("pulse_level_ch1_ADD", 46, 2), 
        AddressAttachCommand("pulse_level_ch2_ADD", 48, 2) ,
        AddressAttachCommand("slope_thred_ch1_ADD", 16, 2), 
        AddressAttachCommand("slope_thred_ch2_ADD", 18, 2) ,
        AddressAttachCommand("trg_cdt_equal_h_ch1_ADD", 50, 2), 
        AddressAttachCommand("trg_cdt_equal_h_ch2_ADD", 58, 2), 
        AddressAttachCommand("trg_cdt_equal_l_ch1_ADD", 54, 2) , 
        AddressAttachCommand("trg_cdt_equal_l_ch2_ADD", 62, 2)  ,
        AddressAttachCommand("trg_cdt_gl_ch1_ADD", 66, 2), 
        AddressAttachCommand("trg_cdt_gl_ch2_ADD", 70, 2) ,
        AddressAttachCommand("trg_holdoff_arg_ch1_ADD", 38, 1),
        AddressAttachCommand("trg_holdoff_arg_ch1_ADD", 38, 1), 
        AddressAttachCommand("trg_holdoff_arg_ch2_ADD", 42, 1), 
        AddressAttachCommand("trg_holdoff_arg_ext_ADD", 38, 1), 
        AddressAttachCommand("trg_holdoff_index_ch1_ADD", 39, 1) , 
        AddressAttachCommand("trg_holdoff_index_ch1_ADD", 39, 1),
        AddressAttachCommand("trg_holdoff_index_ch2_ADD", 43, 1) , 
        AddressAttachCommand("trg_holdoff_index_ext_ADD", 39, 1)  ,
        AddressAttachCommand("volt_gain_ch1_ADD", 278, 2),
        AddressAttachCommand("volt_gain_ch1_ADD", 278, 2), 
        AddressAttachCommand("volt_gain_ch2_ADD", 276, 2) ,
        AddressAttachCommand("volt_gain_ch2_ADD", 276, 2),
        AddressAttachCommand("zero_off_ch1_ADD", 266, 2),
        AddressAttachCommand("zero_off_ch1_ADD", 266, 2), 
        AddressAttachCommand("zero_off_ch2_ADD", 264, 2) ,
        AddressAttachCommand("zero_off_ch2_ADD", 264, 2),
        AddValueAttachCommand("GETDATA_ADD",0x1000,2,0),
        AddressAttachCommand("ADC_RESET", 0x21, 1),
        AddressAttachCommand("reset_adc_0x22", 0x22, 1),
        AddressAttachCommand("READBACK_HTRG_OFFSET", 0x66, 1),
        AddressAttachCommand("FLAG_5mV", 0x20, 1),
        AddressAttachCommand("SAMPLE_50M_FLAG", 0x17, 1),
        AddressAttachCommand("LED_CONTROL", 0x1006, 1),
    ]

    def __init__(self):
        pass

    def get(self,commandName):
        for cmd in self.commands:
            if cmd.name == commandName:
                return cmd
        return None
     
    def printSortedCommands(self):
        for cmd in sorted(self.commands,key=lambda x: x.address):
            print("address",hex(cmd.address),"CMD",cmd.name,"lenght:",cmd.length)

if __name__== "__main__":
    cmd = Commands()
    cmd.printSortedCommands()
