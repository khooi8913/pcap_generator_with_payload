#!/usr/bin/python3

import sys
import binascii
import random
import argparse

#for timestamping
import time
import re


# ----- ===== Configurable parameteres ==== ----
# DO NOT TOUCH OTHER VARIABLES
# default necessary values if there is nothing provided
# default_src_mac = "00:00:00:00:00:01"
# default_dst_mac = "00:00:00:00:00:02"
# default_src_ip = "10.0.0.1"
# default_dst_ip = "192.168.88.8"
# default_src_port = 1234
# default_dst_port = 808
# # default_vlan = None

#DEFINE HERE THE DIFFERENT PACKETS SIZE YOU WANT - ALL HEADER INFORMATION WILL BE THE SAME FOR ALL PACKET SIZES
#This needs to be list object: if you want to use one packet size must be a list with two elements, where the latter is
#empty, i.e., packet_size=(64,)
# payload_size = (64,) #,  # PCAP file will be generated for these
                # 128,  # packet sizes - we always generate all packets with these packet sizes
                # 256,
                # 512,
                # 1024,
                # 1280,
                # 1500)

# COLORIZING
none = '\033[0m'
bold = '\033[01m'
disable = '\033[02m'
underline = '\033[04m'
reverse = '\033[07m'
strikethrough = '\033[09m'
invisible = '\033[08m'

black = '\033[30m'
red = '\033[31m'
green = '\033[32m'
orange = '\033[33m'
blue = '\033[34m'
purple = '\033[35m'
cyan = '\033[36m'
lightgrey = '\033[37m'
darkgrey = '\033[90m'
lightred = '\033[91m'
lightgreen = '\033[92m'
yellow = '\033[93m'
lightblue = '\033[94m'
pink = '\033[95m'
lightcyan = '\033[96m'
CBLINK = '\33[5m'
CBLINK2 = '\33[6m'
# ------ =================================== -----



# Global header for pcap 2.4
pcap_global_header = ('D4 C3 B2 A1'
                      '02 00'  # File format major revision (i.e. pcap <2>.4)
                      '04 00'  # File format minor revision (i.e. pcap 2.<4>)
                      '00 00 00 00'
                      '00 00 00 00'
                      'FF FF 00 00'
                      '01 00 00 00')

# pcap packet header that must preface every packet
pcap_packet_header = ('T1 T1 T1 T1'  # time in seconds (little endian)
                      'T2 T2 T2 T2'  # time in microseconds (little endian)
                      'XX XX XX XX'  # Frame Size (little endian)
                      'YY YY YY YY')  # Frame Size (little endian)

eth_header = ('00 E0 4C 00 00 01'  # Dest Mac
              '00 04 0B 00 00 02'  # Src Mac
              '08 00')  # Protocol (0x0800 = IP)

ip_header = ('45'  # IP version and header length (multiples of 4 bytes)
             '00'
             'XX XX'  # Length - will be calculated and replaced later
             '00 00'
             '40 00 40'
             'PP'  # Protocol (0x11 = UDP, 0x06 = TCP)
             'YY YY'  # Checksum - will be calculated and replaced later
             'SS SS SS SS'  # Source IP (Default: 10.1.0.1)
             'DD DD DD DD')  # Dest IP (Default: 10.0.0.1)

udp_header = ('ZZ ZZ'  # Source port - will be replaced lated
              'XX XX'  # Destination Port - will be replaced later
              'YY YY'  # Length - will be calculated and replaced later
              '00 00')

tcp_header = ('ZZ ZZ'           # source port
              'XX XX'           # destination port
              'SS SS SS SS'     # Seq number
              'AA AA AA AA'     # ACK number - if SYN then ACK=0
              'A0 FF'           # offset, reserved and flags (SYN=02, SYN-ACK=12, ACK=10)
              '71 20'           #window
              'CC CC'           #checksum
              '00 00')          #URGENT pointer     
#these are observed from my own random traffic via wireshark
tcp_ack_opt= ('01 01 08 0A'
              'D2 46 05 C4'
              '81 81 4F 67')
tcp_syn_opt= ('02 04 05 B4'
              '04 02 08 0A'
              'BD B7 BC 30'
              '00 00 00 00'
              '01 03 03 07')
tcp_sa_opt = ('02 04 05 64'
              '04 02 08 0A'
              '72 DD ED 49'
              'BD B7 BB 36'
              '01 03 03 07')


gtp_header = ('30'              # Version(3), Proto type(1) and other zero fields
              'FF'              # Type: T-PDU
              'LL LL'           # Length - will be calculated later
              'TT TT TT TT')    # TEID - will be added later

###### SPECIAL CHARACTERS TO BE REPLACED LATER ######
## pcap_packet_header:
# - T1 T1 T1 T1: time in seconds 
# - T2 T2 T2 T2: time in microsecsonds
# - XX XX XX XX: frame size
# - YY YY YY YY: frame size
## ip_header:
# - XX XX: IP header length
# - PP: protocol
# - YY YY: checksum
# - SS SS SS SS: source IP
# - DD DD DD DD: destinatio IP
## udp_header:
# - ZZ ZZ: source port
# - XX XX: destination port
# - YY YY: length


def _reverseEndian(integer_number):
    #create a list of 2-characters of the input
    # big_endian = re.findall('..', hexstring)
    # little_endian=""
    # for i in reversed(big_endian):
    #     little_endian+=i
    #
    # return little_endian
    big_endian = integer_number
    little_endian=big_endian.to_bytes(4, byteorder='little',signed=True)
    return little_endian.hex()

def createTimestamp(**kwargs):
    # this is a timestamp in seconds.microseconds, e.g., 1570435931.7557144
    _time = kwargs.get('time',time.time())

    #check for float type
    if isinstance(_time,float):
        _time="%.8f" % _time # str(time) is not working well below python3 as floats become reduced to two decimals only
    #split it to seconds and microseconds
    _time=_time.split('.')
    # time is a list now
    sec  = int(_time[0])
    usec = int(_time[1])
    # convert the to hex
    # sec = ("%08x" % int(sec))   # now, we have sec in hex (big endian)
    # usec = ("%08x" % int(usec)) # now, we have usec in hex (big endian)

    sec  = _reverseEndian(sec)
    usec = _reverseEndian(usec)

    return (sec,usec)

def getByteLength(str1):
    return len(''.join(str1.split())) / 2

# raw_input returns the empty string for "enter"
yes = {'yes','y', 'ye', ''}
no = {'no','n'}

def confirm(**args):
    '''
    This function asks for confirmation? To specify the question, **args are defined
    :param args: with_something=with something, do=do, e.g.,  Do you really want to overwrite test.pcap
    :return:
    '''
    print("Do you really want to {} {}? (yes/no,y/n) [Default: Yes]".format(args.get('do',"do something"),args.get('with_something')))
    choice = raw_input().lower()
    print(choice)
    if choice in yes:
        return True
    elif choice in no:
        return False
    else:
        print("Please respond with 'yes/y' or 'no/n'")
        exit(-1)

first_byte_to_write = True

def writeByteStringToFile(bytestring, filename):
    bytelist = bytestring.split()
    bytes = binascii.a2b_hex(''.join(bytelist))
    bitout = open(filename, 'ab')
    bitout.write(bytes)

def backspace(n):
    # print((b'\x08' * n).decode(), end='') # use \x08 char to go back
    sys.stdout.write('\r' * n)  # use '\r' to go back

def calculateRemainingPercentage(current, n):
    percent = (int((current / float(n)) * 100))
    sys.stdout.write(str("Generating packets...{}%\r".format(percent)))
    sys.stdout.flush()
    # print("Creating pcap...{}\r".format(percent)),
    # sys.stdout.flush()
    # sys.stdout.write(percent)

    # backspace(len(percent))  # back for n chars

def readFile(input):
    headers = list() # list of dictionaries
    print("I am not crashed...just reading your input file...")
    with open(input, 'r') as lines:
        line_num = 1
        for line in lines:
            #remove blank spaces
            line = line.strip()
            #removed blank lines
            if line:
                #omit commented lines
                packet_counter=1
                if not (line.startswith("#", 0, 1)):
                    #assume that the desctiption file is a CSV file and look like this:
                    ##timestamp=123123124.123123, src_mac=<SRC_MAC>,dst_mac=<DST_MAC>, src_ip=<SRC_IP>, dst_ip<DST_IP>, src_port=<SRC_PORT>,dst_port=<DST_PORT>,gtp=<GTP_TEID>, ?? - unimplemented
                    #let us further assume that order is not important
                    one_line = line.split(',')
                    # this dictionary will store eventually one complete header
                    header = {
                            'timestamp':"",
                            'src_mac':"",
                            'dst_mac':"",
                            'src_ip':"",
                            'dst_ip':"",
                            'src_port':"",
                            'dst_port':"",
                            'gtp':"",
                            'ext_src_ip':"",
                            'ext_dst_ip':"",
                            'vlan':"",
                            'proto':"", #udp/tcp
                            'payload':"" #this points to a file containing the payload in HEX in one line
                            # TODO: add more (header) fields here
                    }
                    for i in one_line:
                        #remove white spaces
                        i=i.strip()
                        #check whether there is a remaining comma at the end (strip above already makes it a zero-length
                        #white space, so we only need to check that

                        if i != "":
                            #OK, everything is prepared, let's start to parse the relevant data
                            header_row=i.split('=')
                            #now, we only will have key=value pairs, let's see whether they are meaningful
                            #note we need to iterate the whole line first, as it should not be ordered.
                            for h in header.keys():
                                if header_row[0] == h:
                                    if h.endswith("mac"):
                                    #convert header data to MAC
                                        header[h] = parseMAC(header_row[1])
                                    elif h.endswith('ip'):
                                    #convert header data to IP
                                        header[h] = parseIP(header_row[1])
                                    elif h.endswith('port') or h.endswith('vlan') or h.endswith('gtp'):
                                    #convert header data to Integer
                                        header[h] = int(header_row[1])
                                    elif h.endswith('timestamp') or h.endswith('payload'):
                                        header[h] = header_row[1] #it is a string, but it can remain a string
                                    elif h.endswith('proto'):
                                        header[h] = parseProto(header_row[1])
                                    # TODO: handle here futher header fields

                    headers.append(header)

    for h in headers:
        #inside the list
        for hh in h:
            #inside one header
            if hh == 'timestamp' and h[hh]=="":
                h[hh] = default_timestamp

            if hh == 'src_mac' and h[hh]=="":
                h[hh]=parseMAC(default_src_mac)

            if hh == 'dst_mac' and h[hh]=="":
                h[hh] = parseMAC(default_dst_mac)

            if hh == 'src_ip' and h[hh] =="":
                h[hh]=parseIP(default_src_ip)

            if hh == 'dst_ip' and h[hh] == "":
                h[hh] = parseIP(default_dst_ip)

            if hh == 'src_port' and h[hh] == "":
                h[hh] = default_src_port

            if hh == 'dst_port' and h[hh] == "":
                h[hh] = default_dst_port

            if hh == 'vlan' and h[hh] == "":
                h[hh] = default_vlan

            if hh == 'gtp' and h[hh] == "":
                h[hh] = None

            if hh == 'payload' and h[hh] == "":
                h[hh] = None

            if hh == 'proto' and h[hh] == "":
                h[hh] = parseProto(default_proto)

    return headers


def generateTraceFromFile(inputfile, pcapfile, **kwargs):
    '''
    This function will read the input file and creates a pcap from its content
    :param inputfile: input file to read
    :param pcapfile: pcap output file
    :param kwargs:
        payload_size = list of packetsizes required
        src_mac = default src_mac
        dst_mac = default dst_mac
        src_ip = default src_ip
        dst_ip = default dst_ip
        src_port = default src_port
        dst_port = default dst_port
        vlan = default vlan
        gtp_teid = default gtp_teid
        timestamp = default timestamp
        payload = pointer to a file containing the payload in HEX
        proto = default proto (UDP)

    :return: None
    '''
    global default_src_mac, default_dst_mac
    global default_src_ip, default_dst_ip
    global default_src_port, default_dst_port
    global default_vlan
    global payload_size
    global verbose
    global default_timestamp
    global default_payload
    global default_proto

    default_payloadsize = kwargs.get('payload_size')
    default_src_mac = kwargs.get('src_mac')
    default_dst_mac = kwargs.get('dst_mac')
    default_src_ip = kwargs.get('src_ip')
    default_dst_ip = kwargs.get('dst_ip')
    default_src_port = int(kwargs.get('src_port'))
    default_dst_port = int(kwargs.get('dst_port'))
    default_vlan = kwargs.get('vlan')
    gtp_teid = kwargs.get('gtp_teid')
    verbose = kwargs.get('verbose')
    default_timestamp = kwargs.get('timestamp')
    default_payload = kwargs.get('payload')
    default_proto = kwargs.get('proto')

    if default_vlan is not None:
        default_vlan = int(default_vlan)

    i = 0
    with open(input, 'r') as f:
        line = f.readline()
        while line:
            i = i + 1    
            line = line.strip()
            if not (line.startswith("#", 0, 1)):
                #assume that the desctiption file is a CSV file and look like this:
                ##timestamp=123123124.123123, src_mac=<SRC_MAC>,dst_mac=<DST_MAC>, src_ip=<SRC_IP>, dst_ip<DST_IP>, src_port=<SRC_PORT>,dst_port=<DST_PORT>,gtp=<GTP_TEID>, ?? - unimplemented
                #let us further assume that order is not important
                one_line = line.split(',')
                # this dictionary will store eventually one complete header
                header = {
                        'timestamp':"",
                        'src_mac':"",
                        'dst_mac':"",
                        'src_ip':"",
                        'dst_ip':"",
                        'src_port':"",
                        'dst_port':"",
                        'gtp':"",
                        'ext_src_ip':"",
                        'ext_dst_ip':"",
                        'vlan':"",
                        'proto':"", #udp/tcp
                        'payload':"" #this points to a file containing the payload in HEX in one line
                        # TODO: add more (header) fields here
                }
                for j in one_line:
                    #remove white spaces
                    j=j.strip()
                    #check whether there is a remaining comma at the end (strip above already makes it a zero-length
                    #white space, so we only need to check that

                    if j != "":
                        #OK, everything is prepared, let's start to parse the relevant data
                        header_row=j.split('=')
                        #now, we only will have key=value pairs, let's see whether they are meaningful
                        #note we need to iterate the whole line first, as it should not be ordered.
                        for h in header.keys():
                            if header_row[0] == h:
                                if h.endswith("mac"):
                                #convert header data to MAC
                                    header[h] = parseMAC(header_row[1])
                                elif h.endswith('ip'):
                                #convert header data to IP
                                    header[h] = parseIP(header_row[1])
                                elif h.endswith('port') or h.endswith('vlan') or h.endswith('gtp'):
                                #convert header data to Integer
                                    header[h] = int(header_row[1])
                                elif h.endswith('timestamp') or h.endswith('payload'):
                                    header[h] = header_row[1] #it is a string, but it can remain a string
                                elif h.endswith('proto'):
                                    header[h] = parseProto(header_row[1])
                                # TODO: handle here futher header fields

                for hh in header:
                    #inside one header
                    if hh == 'timestamp' and header[hh]=="":
                        header[hh] = default_timestamp

                    if hh == 'src_mac' and header[hh]=="":
                        header[hh]=parseMAC(default_src_mac)

                    if hh == 'dst_mac' and header[hh]=="":
                        header[hh] = parseMAC(default_dst_mac)

                    if hh == 'src_ip' and header[hh] =="":
                        header[hh]=parseIP(default_src_ip)

                    if hh == 'dst_ip' and header[hh] == "":
                        header[hh] = parseIP(default_dst_ip)

                    if hh == 'src_port' and header[hh] == "":
                        header[hh] = default_src_port

                    if hh == 'dst_port' and header[hh] == "":
                        header[hh] = default_dst_port

                    if hh == 'vlan' and header[hh] == "":
                        header[hh] = default_vlan

                    if hh == 'gtp' and header[hh] == "":
                        header[hh] = None

                    if hh == 'payload' and header[hh] == "":
                        header[hh] = None

                    if hh == 'proto' and header[hh] == "":
                        header[hh] = parseProto(default_proto)

                # FURTHER PROCESSING HERE
                # set here the variables    
                timestamp = header['timestamp']
                sport = header['src_port']
                dport = header['dst_port']
                src_ip = header['src_ip']
                dst_ip = header['dst_ip']
                src_mac = header['src_mac']
                dst_mac = header['dst_mac']
                vlan = header['vlan']

                gtp_teid = header['gtp']
                ext_src_ip = header['ext_src_ip']
                ext_dst_ip = header['ext_dst_ip']

                payload = header['payload']
                proto = header['proto']


                #VLAN HANDLING - it requires other eth_type and additional headers
                if vlan is None:
                    # update ethernet header for each packet
                    eth_header = dst_mac + ' ' + src_mac + "0800"
                else:
                    eth_header = dst_mac + ' ' + src_mac + \
                                '81 00' + \
                                '0V VV' + \
                                '08 00'
                    # update vlan header
                    eth_header = eth_header.replace('0V VV', "0%03x" % vlan)

                # GTP tunneling: it requires additional headers
                if gtp_teid is not None:
                    gtp = gtp_header
                    gtp = gtp.replace('TT TT TT TT', "%08x" % gtp_teid)

                    # generate the external headers
                    gtp_dport = 2152
                    gtp_sport = 2152
                    ext_udp = udp_header.replace('XX XX', "%04x" % gtp_dport)
                    ext_udp = ext_udp.replace('ZZ ZZ', "%04x" % gtp_sport)
                    ext_ip = ip_header
                    ext_ip = ext_ip.replace('SS SS SS SS', ext_src_ip)
                    ext_ip = ext_ip.replace('DD DD DD DD', ext_dst_ip)

                # update ip header - see on top how it looks like (the last bytes are encoding the IP address)
                ip = ip_header
                ip = ip.replace('SS SS SS SS', src_ip) #update source IP
                ip = ip.replace('DD DD DD DD', dst_ip) #upodate destination IP

            
                # Random payload
                if payload is None:
                    # generate the packet payload (random)
                    if default_payloadsize is None:
                        payloadSize = random.randint(20,1200)
                    else:
                        payloadSize = int(default_payloadsize)

                    message = getMessage(payloadSize)

                # if payload is set
                else:
                    message=None
                    # Bypass the need for payload to be a fixed input file, instead, we specify the custom payload for each packet in the CSV file.
                    message=payload.strip()
                    # with open(payload, 'r') as lines:
                    #     for l in lines:
                    #         #remove blank spaces
                    #         l = l.strip()
                    #         #removed blank lines
                    #         if l:
                    #             #omit commented lines
                    #             if not (l.startswith("#", 0, 1)):
                    #                 message = l
                    if message is None:
                        print("The file containing the payload {} has no useful line".format(payload))
                        print("Exiting...")
                        exit(-1)
                
                #Update proto
                ip = ip.replace('PP', proto) #update IP proto
                if(proto != '06'): #it is NOT A TCP packet, treat as UDP!
                #----===== UDP =====----
                    TCP = False
                    # update ports
                    udp = udp_header.replace('XX XX', "%04x" % dport)
                    udp = udp.replace('ZZ ZZ', "%04x" % sport)

                    # generate the headers (in case of tunneling: internal headers)
                    udp_len = getByteLength(message) + getByteLength(udp_header)
                    udp = udp.replace('YY YY', "%04x" % int(udp_len))

                    ip_len = udp_len + getByteLength(ip_header)
                    #print("IP_LEN:", ip_len)
                #-----------------------
                else:
                    # print("TCP")
                #----=====  TCP  =====----
                    TCP = True
                    tcp = tcp_header.replace('ZZ ZZ', "%04x" % sport) #src port
                    tcp = tcp.replace('XX XX', "%04x" % dport) #dest port
                    #seq_no =  str("%08x" % random.randint(0,2**32))
                    #ack_no =  str("%08x" % random.randint(0,2**31))
                    seq_no = '24922ce5'
                    ack_no = '709e582a'
                    tcp = tcp.replace('SS SS SS SS', seq_no) #Seq no
                    tcp = tcp.replace('AA AA AA AA', ack_no) #ACK no
                    tcp = tcp.replace('FF', '12') #replace flags to indicate SYN-ACK
                    
                    #for checksum calculations we need pseudo header and tcp header with 00 00 checksum
                    hdr = tcp.replace('CC CC', '00 00')
                    
                    #preparing for checksum calculation
                    pseudo_hdr = '00'+proto+src_ip+dst_ip+'14' #last element is TCP length (including data part) which is 20 bytes always
                    # print("---", pseudo_hdr)
                    # print(hdr)
                    hdr_checksum=pseudo_hdr+hdr
                    tcp = tcp.replace('CC CC', "%04x" % int(calc_checksum(hdr_checksum)))

                    #TCP SYN-ACK is supported only
                    # Add TCP SA options to TCP base header

                    tcp += tcp_sa_opt 
                    # TODO: add TCP SYN, ACK, and further features
                    # print('---tcp_sa')
                    # print(tcp_sa_opt)

                    # tcp_len = getByteLength(message) + getByteLength(tcp)
                    tcp_len =  getByteLength(tcp)
                    ip_len = tcp_len + getByteLength(ip_header)
                    #print("IP_LEN:", ip_len)

                #-------------------------

                ip = ip.replace('XX XX', "%04x" % int(ip_len))
                checksum = calc_checksum(ip.replace('YY YY', '00 00'))
                ip = ip.replace('YY YY', "%04x" % int(checksum))
                tot_len = ip_len

                # encapsulation (external header)
                if gtp_teid is not None:
                    gtp_len = ip_len
                    gtp = gtp.replace('LL LL', "%04x" % int(gtp_len))

                    # generate the external headers
                    if(not TCP):
                        ext_udp_len = gtp_len + getByteLength(gtp) + getByteLength(udp_header)
                        ext_udp = ext_udp.replace('YY YY', "%04x" % int(ext_udp_len))

                        ext_ip_len = ext_udp_len + getByteLength(ip_header)
                        if ext_ip_len > 1500:
                            print("WARNING! Generating >MTU size packets: {}".format(ext_ip_len))
                        ext_ip = ext_ip.replace('XX XX', "%04x" % int(ext_ip_len))
                        checksum = calc_checksum(ext_ip.replace('YY YY', '00 00'))
                        ext_ip = ext_ip.replace('YY YY', "%04x" % int(checksum))
                        tot_len = ext_ip_len
                    else:
                        print("GTP and TCP is not supported yet")
                        exit(-1)
                        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                        # TODO: add TCP + GTP support here
                        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

                pcap_len = tot_len + getByteLength(eth_header)
                hex_str = "%08x" % int(pcap_len)
                reverse_hex_str = hex_str[6:] + hex_str[4:6] + hex_str[2:4] + hex_str[:2]

                pcaph = pcap_packet_header.replace('XX XX XX XX', reverse_hex_str)
                pcaph = pcaph.replace('YY YY YY YY', reverse_hex_str)

                #adding timestamp
                if timestamp is None: #timestamp was not set, use current time
                    t = createTimestamp()
                else:
                    t = createTimestamp(time=timestamp)
                pcaph = pcaph.replace('T1 T1 T1 T1', t[0]) # time[0] is seonds
                pcaph = pcaph.replace('T2 T2 T2 T2', t[1]) # time[1] is useonds

                # at the first packet we need the global pcap header
                if i == 1:
                    if gtp_teid is not None: 
                        if not TCP: 
                            bytestring = pcap_global_header + pcaph + eth_header + ext_ip + ext_udp + gtp + ip + udp + message
                        else:
                            #TODO: gtp + tcp support
                            print("GTP and TCP is not supported yet")
                            exit(-1)
                    else:
                        if not TCP: 
                            bytestring = pcap_global_header + pcaph + eth_header + ip + udp + message
                        else:
                            bytestring = pcap_global_header + pcaph + eth_header + ip + tcp + message
                # for the rest, only the packets are coming
                else:
                    if gtp_teid is not None:
                        if not TCP:
                            bytestring = pcaph + eth_header + ext_ip + ext_udp + gtp + ip + udp + message
                        else: 
                            #TODO: gtp + tcp support
                            print("GTP and TCP is not supported yet")
                            exit(-1)
                    else:
                        if not TCP:
                            bytestring = pcaph + eth_header + ip + udp + message
                        else:
                            bytestring = pcaph + eth_header + ip + tcp + message

                # this function is writing out pcap file per se
                if verbose:
                    print("Packet to be written out:\n{}".format(header))

                writeByteStringToFile(bytestring, pcapfile + ".pcap")

                # we have to change back the variable fields to their original fixed value else they will not be found
                ip = ip.replace("%04x" % int(ip_len), 'XX XX')
                udp = udp.replace("%04x" % int(udp_len), 'YY YY')
                if gtp_teid is not None:
                    gtp = gtp.replace("%04x" % int(gtp_len), 'LL LL')
                    ext_udp = ext_udp.replace("%04x" % int(ext_udp_len), 'YY YY')
                    ext_ip = ext_ip.replace("%04x" % int(ext_ip_len), 'XX XX')

            line = f.readline()



    # headers=readFile(inputfile)
    # n=len(headers)

    # write out header information to file - for easier NF configuration later - 5-tuples are in .nfo files as well
    # for i in range(1, int(n) + 1):
        # print out the remaining percentage to know when the generate will finish
        #calculateRemainingPercentage(i, int(n))

        # # set here the variables
        # timestamp = headers[i-1]['timestamp']
        # sport = headers[i-1]['src_port']
        # dport = headers[i-1]['dst_port']
        # src_ip = headers[i-1]['src_ip']
        # dst_ip = headers[i-1]['dst_ip']
        # src_mac = headers[i-1]['src_mac']
        # dst_mac = headers[i-1]['dst_mac']
        # vlan = headers[i-1]['vlan']

        # gtp_teid = headers[i-1]['gtp']
        # ext_src_ip = headers[i-1]['ext_src_ip']
        # ext_dst_ip = headers[i-1]['ext_dst_ip']

        # payload = headers[i-1]['payload']
        # proto = headers[i-1]['proto']


        # #VLAN HANDLING - it requires other eth_type and additional headers
        # if vlan is None:
        #     # update ethernet header for each packet
        #     eth_header = dst_mac + ' ' + src_mac + "0800"
        # else:
        #     eth_header = dst_mac + ' ' + src_mac + \
        #                  '81 00' + \
        #                  '0V VV' + \
        #                  '08 00'
        #     # update vlan header
        #     eth_header = eth_header.replace('0V VV', "0%03x" % vlan)

        # # GTP tunneling: it requires additional headers
        # if gtp_teid is not None:
        #     gtp = gtp_header
        #     gtp = gtp.replace('TT TT TT TT', "%08x" % gtp_teid)

        #     # generate the external headers
        #     gtp_dport = 2152
        #     gtp_sport = 2152
        #     ext_udp = udp_header.replace('XX XX', "%04x" % gtp_dport)
        #     ext_udp = ext_udp.replace('ZZ ZZ', "%04x" % gtp_sport)
        #     ext_ip = ip_header
        #     ext_ip = ext_ip.replace('SS SS SS SS', ext_src_ip)
        #     ext_ip = ext_ip.replace('DD DD DD DD', ext_dst_ip)

        # # update ip header - see on top how it looks like (the last bytes are encoding the IP address)
        # ip = ip_header
        # ip = ip.replace('SS SS SS SS', src_ip) #update source IP
        # ip = ip.replace('DD DD DD DD', dst_ip) #upodate destination IP

       
        # # Random payload
        # if payload is None:
        #     # generate the packet payload (random)
        #     if default_payloadsize is None:
        #         payloadSize = random.randint(20,1200)
        #     else:
        #         payloadSize = int(default_payloadsize)

        #     message = getMessage(payloadSize)

        # # if payload is set
        # else:
        #     message=None
        #     # Bypass the need for payload to be a fixed input file, instead, we specify the custom payload for each packet in the CSV file.
        #     message=payload.strip()
        #     # with open(payload, 'r') as lines:
        #     #     for l in lines:
        #     #         #remove blank spaces
        #     #         l = l.strip()
        #     #         #removed blank lines
        #     #         if l:
        #     #             #omit commented lines
        #     #             if not (l.startswith("#", 0, 1)):
        #     #                 message = l
        #     if message is None:
        #         print("The file containing the payload {} has no useful line".format(payload))
        #         print("Exiting...")
        #         exit(-1)
        
        # #Update proto
        # ip = ip.replace('PP', proto) #update IP proto
        # if(proto != '06'): #it is NOT A TCP packet, treat as UDP!
        # #----===== UDP =====----
        #     TCP = False
        #     # update ports
        #     udp = udp_header.replace('XX XX', "%04x" % dport)
        #     udp = udp.replace('ZZ ZZ', "%04x" % sport)

        #     # generate the headers (in case of tunneling: internal headers)
        #     udp_len = getByteLength(message) + getByteLength(udp_header)
        #     udp = udp.replace('YY YY', "%04x" % int(udp_len))

        #     ip_len = udp_len + getByteLength(ip_header)
        #     #print("IP_LEN:", ip_len)
        # #-----------------------
        # else:
        #     # print("TCP")
        # #----=====  TCP  =====----
        #     TCP = True
        #     tcp = tcp_header.replace('ZZ ZZ', "%04x" % sport) #src port
        #     tcp = tcp.replace('XX XX', "%04x" % dport) #dest port
        #     #seq_no =  str("%08x" % random.randint(0,2**32))
        #     #ack_no =  str("%08x" % random.randint(0,2**31))
        #     seq_no = '24922ce5'
        #     ack_no = '709e582a'
        #     tcp = tcp.replace('SS SS SS SS', seq_no) #Seq no
        #     tcp = tcp.replace('AA AA AA AA', ack_no) #ACK no
        #     tcp = tcp.replace('FF', '12') #replace flags to indicate SYN-ACK
            
        #     #for checksum calculations we need pseudo header and tcp header with 00 00 checksum
        #     hdr = tcp.replace('CC CC', '00 00')
            
        #     #preparing for checksum calculation
        #     pseudo_hdr = '00'+proto+src_ip+dst_ip+'14' #last element is TCP length (including data part) which is 20 bytes always
        #     # print("---", pseudo_hdr)
        #     # print(hdr)
        #     hdr_checksum=pseudo_hdr+hdr
        #     tcp = tcp.replace('CC CC', "%04x" % int(calc_checksum(hdr_checksum)))
            

        #     #TCP SYN-ACK is supported only
        #     # Add TCP SA options to TCP base header

        #     tcp += tcp_sa_opt 
        #     # TODO: add TCP SYN, ACK, and further features
        #     # print('---tcp_sa')
        #     # print(tcp_sa_opt)

        #     # tcp_len = getByteLength(message) + getByteLength(tcp)
        #     tcp_len =  getByteLength(tcp)
        #     ip_len = tcp_len + getByteLength(ip_header)
        #     #print("IP_LEN:", ip_len)

        # #-------------------------


        # ip = ip.replace('XX XX', "%04x" % int(ip_len))
        # checksum = calc_checksum(ip.replace('YY YY', '00 00'))
        # ip = ip.replace('YY YY', "%04x" % int(checksum))
        # tot_len = ip_len

        # # encapsulation (external header)
        # if gtp_teid is not None:
        #     gtp_len = ip_len
        #     gtp = gtp.replace('LL LL', "%04x" % int(gtp_len))

        #     # generate the external headers
        #     if(not TCP):
        #         ext_udp_len = gtp_len + getByteLength(gtp) + getByteLength(udp_header)
        #         ext_udp = ext_udp.replace('YY YY', "%04x" % int(ext_udp_len))

        #         ext_ip_len = ext_udp_len + getByteLength(ip_header)
        #         if ext_ip_len > 1500:
        #             print("WARNING! Generating >MTU size packets: {}".format(ext_ip_len))
        #         ext_ip = ext_ip.replace('XX XX', "%04x" % int(ext_ip_len))
        #         checksum = calc_checksum(ext_ip.replace('YY YY', '00 00'))
        #         ext_ip = ext_ip.replace('YY YY', "%04x" % int(checksum))
        #         tot_len = ext_ip_len
        #     else:
        #         print("GTP and TCP is not supported yet")
        #         exit(-1)
        #         # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        #         # TODO: add TCP + GTP support here
        #         # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        # pcap_len = tot_len + getByteLength(eth_header)
        # hex_str = "%08x" % int(pcap_len)
        # reverse_hex_str = hex_str[6:] + hex_str[4:6] + hex_str[2:4] + hex_str[:2]

        # pcaph = pcap_packet_header.replace('XX XX XX XX', reverse_hex_str)
        # pcaph = pcaph.replace('YY YY YY YY', reverse_hex_str)

        # #adding timestamp
        # if timestamp is None: #timestamp was not set, use current time
        #   time = createTimestamp()
        # else:
        #   time = createTimestamp(time=timestamp)
        # pcaph = pcaph.replace('T1 T1 T1 T1', time[0]) # time[0] is seonds
        # pcaph = pcaph.replace('T2 T2 T2 T2', time[1]) # time[1] is useonds

        # # at the first packet we need the global pcap header
        # if i == 1:
        #     if gtp_teid is not None: 
        #         if not TCP: 
        #             bytestring = pcap_global_header + pcaph + eth_header + ext_ip + ext_udp + gtp + ip + udp + message
        #         else:
        #             #TODO: gtp + tcp support
        #             print("GTP and TCP is not supported yet")
        #             exit(-1)
        #     else:
        #         if not TCP: 
        #             bytestring = pcap_global_header + pcaph + eth_header + ip + udp + message
        #         else:
        #             bytestring = pcap_global_header + pcaph + eth_header + ip + tcp + message
        # # for the rest, only the packets are coming
        # else:
        #     if gtp_teid is not None:
        #         if not TCP:
        #             bytestring = pcaph + eth_header + ext_ip + ext_udp + gtp + ip + udp + message
        #         else: 
        #             #TODO: gtp + tcp support
        #             print("GTP and TCP is not supported yet")
        #             exit(-1)
        #     else:
        #         if not TCP:
        #             bytestring = pcaph + eth_header + ip + udp + message
        #         else:
        #             bytestring = pcaph + eth_header + ip + tcp + message

        # # this function is writing out pcap file per se
        # if verbose:
        #     print("Packet to be written out:\n{}".format(headers[i-1]))

        # writeByteStringToFile(bytestring, pcapfile + ".pcap")

        # # we have to change back the variable fields to their original fixed value else they will not be found
        # ip = ip.replace("%04x" % int(ip_len), 'XX XX')
        # udp = udp.replace("%04x" % int(udp_len), 'YY YY')
        # if gtp_teid is not None:
        #     gtp = gtp.replace("%04x" % int(gtp_len), 'LL LL')
        #     ext_udp = ext_udp.replace("%04x" % int(ext_udp_len), 'YY YY')
        #     ext_ip = ext_ip.replace("%04x" % int(ext_ip_len), 'XX XX')

def getRandomMAC():
    return "1a" + str("%0.10X" % random.randint(1,0xffffffffff))

def getRandomIP():

    # to avoid multicast addresses (range is between 0.0.0.0/8 and 223.255.255.255)
    ip = str("%0.8X" % random.randint(0x01000000,0xdfffffff))

    #avoid others 127.0.0.0/8 - hex(127)=7F
    while ip.startswith("7F"):
        #print "Ooops, accidentally a 127.0.0.0/8 IP was generated...REGENERATING!"
        ip = str("%0.8X" % random.randint(0x01000000, 0xdfffffff))

    return ip

def getRandomPort(**args):
    port = random.randint(1,65535)
    exlude = args.get("exclude", 4305)
    if(port == exlude):
        getRandomPort()
    return int(port)

def parseMAC(mac):
    ret_val=mac.replace(":","").upper()
    if len(ret_val) != 12: #check mac address length
        print("ERROR during parsing mac address - not long enough!: {}".format(mac))
        exit(-1)
    return  ret_val

def parseIP(ip):
    ret_val = ""
    #split IP address into 4 8-bit values
    ip_segments=ip.split(".")
    for i in ip_segments:
        ret_val+=str("%0.2X" % int(i))
    if len(ret_val) != 8: #check length of IP
        print("ERROR during parsing IP address - not long enough!: {}".format(ip))
        exit(-1)
    return ret_val

def parseProto(proto):
    if proto.lower() == "tcp":
        ret_val = '06'
    else:
    #everything else is set to UDP by default irrespectively of having proto=udp or proto=unknown_proto
        ret_val = '11' #(0x11 = 17)
    #there is no HEX type in python, so we return string as we anyway need string for the pcap files to write
    return ret_val

def splitN(str1, n):
    return [str1[start:start + n] for start in range(0, len(str1), n)]


# Calculates and returns the IP checksum based on the given IP Header
def calc_checksum(iph):
    #remove whitespaces
    iph=iph.replace(' ','')

    # split into 16-bits words
    words = splitN(''.join(iph.split()), 4)

    csum = 0
    for word in words:
        csum += int(word, base=16)

    csum += (csum >> 16)
    csum = csum & 0xFFFF ^ 0xFFFF

    return csum

def getMessage(packetsize):
    message = ''
    for i in range(0, int(packetsize) - 46):  # 46 = eth + ip + udp header
        message += "%0.2X " % random.randint(0, 255)

    return message


def showHelp():
    print ("{}usage: pcap_generator_from_csv.py <input_csv_file> <desired_output_pcapfile_prefix>{}".format(bold,none))
    print("Example: ./pcap_generator_from_csv.py input.csv output")
    print("{}Note: Existing files with the given <desired_output_pcapfile_prefix>.pcap will be overwritten!{}".format(yellow,none))

    print("This python script generates pcap files according to the header information stored in a CSV file")
    print("See 'input.csv' file for CSV details\n")
    print("Supported header fields: {}\n\n" \
                                               "  VLAN \n" \
                                               "  L2 (src and dst MAC) \n" \
                                               "  L3 (src and dst IP) \n" \
                                               "  L4 (src and dst PORT) \n" \
                                               "  GTP_TEID\n " \
                                               "  PAYLOAD (pointer to a file containing the payload in one line in HEX)\n " \
                                               "  TIMESTAMP for each packet\n".format(bold,none))
    print("Any further header definition in the file is sleemlessly ignored!\n")
    print("In case of missing header information in the inputfile, default values will be used!")
    print("To change the default values, modify the source code (first couple of lines after imports)\n")
    print("Default packet size is 64-byte! It is defined as a list in the source code! " \
          "Extend it if necessary!\n")
    exit(0)


"""------------------------------------------"""
""" End of functions, execution starts here: """
"""------------------------------------------"""
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Usage of PCAP generator from CSV file")
    parser.add_argument('-i','--input',nargs=1,
                        help="Specify the name of the input CSV file. "
                             "For syntax, see input.csv.example!",
                        required=True)
    parser.add_argument('-o','--output',nargs=1,
                        help="Specify the output PCAP file's basename! "
                             "Output will be [output].pcap extension is not needed!",
                        required=True)
    parser.add_argument('-p','--payloadsize',nargs=1,
                        help="Specify here the default payloadsize if payload is not defined in your input.csv! "
                        "Default is a random, which is between 20--1200 to surely avoid too big MTU)",
                        required=False,
                        default=[None])
    parser.add_argument('-a','--src_mac',nargs=1,
                        help="Specify default source MAC address if it is not present "
                        "in the input.csv. Default: 00:00:00:00:00:01",
                        required=False,
                        default=["00:00:00:00:00:01"])
    parser.add_argument('-b', '--dst_mac', nargs=1,
                        help="Specify default destination MAC address if it is not present "
                             "in the input.csv. Default: 00:00:00:00:00:02",
                        required=False,
                        default=["00:00:00:00:00:02"])
    parser.add_argument('-c', '--vlan', nargs=1,
                        help="Specify default VLAN tag if it is not present "
                             "in the input.csv. Default: No VLAN",
                        required=False,
                        default=[None])
    parser.add_argument('-d', '--src_ip', nargs=1,
                        help="Specify default source IP address if it is not present "
                             "in the input.csv. Default: 10.0.0.1",
                        required=False,
                        default=["10.0.0.1"])

    parser.add_argument('-e', '--dst_ip', nargs=1,
                        help="Specify default destination IP address if it is not present "
                             "in the input.csv. Default: 10.0.0.2",
                        required=False,
                        default=["10.0.0.2"])
    parser.add_argument('-l', '--proto', nargs=1,
                        help="Specify default protocol "
                             "in the input.csv. Default: udp",
                        required=False,
                        default=["udp"])

    parser.add_argument('-f', '--src_port', nargs=1,
                        help="Specify default source port if it is not present "
                             "in the input.csv. Default: 1234",
                        required=False,
                        default=["32768"])

    parser.add_argument('-g', '--dst_port', nargs=1,
                        help="Specify default destination port if it is not present "
                             "in the input.csv. Default: 80",
                        required=False,
                        default=["5858"])
    parser.add_argument('-j', '--gtp_teid', nargs=1,
                        help="Specify default GTP_TEID if it is not present "
                             "in the input.csv. Default: NO GTP TEID",
                        default=[None])
    parser.add_argument('-t', '--timestamp', nargs=1,
                        help="Specify the default timestamp for each packet if it is not present "
                             "in the input.csv. Default: Use current time",
                        required=False,
                        default=[None])
    


    parser.add_argument('-v','--verbose', action='store_true', required=False, dest='verbose',
    help="Enabling verbose mode")
    parser.set_defaults(verbose=False)

    args = parser.parse_args()

    input = args.input[0]
    output = args.output[0]
    payload_size = args.payloadsize[0]
    src_mac = args.src_mac[0]
    dst_mac = args.dst_mac[0]
    src_ip = args.src_ip[0]
    dst_ip = args.dst_ip[0]
    src_port = args.src_port[0]
    dst_port = args.dst_port[0]
    vlan = args.vlan[0]
    gtp_teid = args.gtp_teid[0]
    timestamp = args.timestamp[0]
    proto = args.proto[0]

    verbose=args.verbose

    print("{}The following arguments were set:{}".format(bold,none))
    print("{}Input file:                 {}{}{}".format(bold,green,input,none))
    print("{}Output file:                {}{}{}".format(bold,green,output,none))
    print("{}Payload size if no payload: {}{}{}".format(bold,green,payload_size,none))
    print("{}SRC MAC if undefined:       {}{}{}".format(bold,green,src_mac,none))
    print("{}DST MAC if undefined:       {}{}{}".format(bold,green,dst_mac,none))
    print("{}SRC IP if undefined:        {}{}{}".format(bold,green,src_ip,none))
    print("{}DST IP if undefined:        {}{}{}".format(bold,green,dst_ip,none))
    print("{}PROTO if undefined:         {}{}{}".format(bold,green,proto,none))
    print("{}SRC PORT if undefined:      {}{}{}".format(bold,green,src_port,none))
    print("{}DST PORT if undefined:      {}{}{}".format(bold,green,dst_port,none))
    print("{}VLAN if undefined:          {}{}{}".format(bold,green,vlan,none))
    print("{}GTP_TEID if undefined       {}{}{}".format(bold,green,gtp_teid,none))
    print("{}TIMESTAMP if undefined:     {}{}{}".format(bold,green,timestamp,none))

    open(str("{}.pcap".format(output)),'w') # delete contents

    generateTraceFromFile(
                            input,
                            output,
                            payload_size=payload_size,
                            src_mac=src_mac,
                            dst_mac=dst_mac,
                            src_ip=src_ip,
                            dst_ip=dst_ip,
                            src_port=src_port,
                            dst_port=dst_port,
                            vlan=vlan,
                            verbose=verbose,
                            gtp_teid=gtp_teid,
                            timestamp=timestamp,
                            proto=proto
                         )

    print("Generating packets...[DONE]")
