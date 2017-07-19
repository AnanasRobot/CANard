import serial
from .. import can


class CantactDev:
    str_tail = ""

    def __init__(self, port):
        self.ser = serial.serial_for_url(port, timeout=0)

    def start(self):
        self.ser.write('O\r'.encode())

    def stop(self):
        self.ser.write('C\r'.encode())

    def set_bitrate(self, bitrate):
        if bitrate == 10000:
            self.ser.write('S0\r'.encode())
        elif bitrate == 20000:
            self.ser.write('S1\r'.encode())
        elif bitrate == 50000:
            self.ser.write('S2\r'.encode())
        elif bitrate == 100000:
            self.ser.write('S3\r'.encode())
        elif bitrate == 125000:
            self.ser.write('S4\r'.encode())
        elif bitrate == 250000:
            self.ser.write('S5\r'.encode())
        elif bitrate == 500000:
            self.ser.write('S6\r'.encode())
        elif bitrate == 750000:
            self.ser.write('S7\r'.encode())
        elif bitrate == 1000000:
            self.ser.write('S8\r'.encode())
        else:
            raise ValueError("Bitrate not supported")

    def recv(self):
        # receive characters until a newline (\r) is hit
        rx_str = ""
        while rx_str == "" or rx_str[-1] != '\r':
            rx_str = rx_str + self.ser.read().decode('UTF-8', 'ignore')

        # parse the id, create a frame
        frame = can.Frame(0x000)
        if rx_str[0] == 't':
            frame_type = can.FrameType.DataFrame
            is_extended_id = False
            frame_id = int(rx_str[1:4], 16)
            frame = can.Frame(frame_id, frame_type=frame_type, is_extended_id=is_extended_id)
            # parse the DLC
            frame.dlc = int(rx_str[4])
            # parse the data bytes
            data = []
            for i in range(0, frame.dlc):
                data.append(int(rx_str[5 + i * 2:7 + i * 2], 16))
                frame.data = data
        elif rx_str[0] == 'T':
            frame_type = can.FrameType.DataFrame
            is_extended_id = True
            frame_id = int(rx_str[1:9], 16)
            frame = can.Frame(frame_id, frame_type=frame_type, is_extended_id=is_extended_id)
            # parse the DLC
            frame.dlc = int(rx_str[9])
            # parse the data bytes
            data = []
            for i in range(0, frame.dlc):
                data.append(int(rx_str[10 + i * 2:12 + i * 2], 16))
                frame.data = data
        elif rx_str[0] == 'r':
            frame_type = can.FrameType.RemoteFrame
            is_extended_id = False
            frame_id = int(rx_str[1:4], 16)
            frame = can.Frame(frame_id, frame_type=frame_type, is_extended_id=is_extended_id)
        elif rx_str[0] == 'R':
            frame_type = can.FrameType.RemoteFrame
            is_extended_id = True
            frame_id = int(rx_str[1:9], 16)
            frame = can.Frame(frame_id, frame_type=frame_type, is_extended_id=is_extended_id)

        return frame

    def paserRecvCAN(self, rx_str):

        frame = can.Frame(0x000)
        if rx_str[0] == 't':
            frame_type = can.FrameType.DataFrame
            is_extended_id = False
            frame_id = int(rx_str[1:4], 16)
            frame = can.Frame(frame_id, frame_type=frame_type, is_extended_id=is_extended_id)
            # parse the DLC
            frame.dlc = int(rx_str[4])
            # parse the data bytes
            data = []
            for i in range(0, frame.dlc):
                data.append(int(rx_str[5 + i * 2:7 + i * 2], 16))
                frame.data = data
        elif rx_str[0]  == 'T':
            frame_type = can.FrameType.DataFrame
            is_extended_id = True
            frame_id = int(rx_str[1:9], 16)
            frame = can.Frame(frame_id, frame_type=frame_type, is_extended_id=is_extended_id)
            # parse the DLC
            frame.dlc = int(rx_str[9])
            # parse the data bytes
            data = []
            for i in range(0, frame.dlc):
                data.append(int(rx_str[10 + i * 2:12 + i * 2], 16))
                frame.data = data
        elif rx_str[0]  == 'r':
            frame_type = can.FrameType.RemoteFrame
            is_extended_id = False
            frame_id = int(rx_str[1:4], 16)
            frame = can.Frame(frame_id, frame_type=frame_type, is_extended_id=is_extended_id)
        elif rx_str[0]  == 'R':
            frame_type = can.FrameType.RemoteFrame
            is_extended_id = True
            frame_id = int(rx_str[1:9], 16)
            frame = can.Frame(frame_id, frame_type=frame_type, is_extended_id=is_extended_id)

        return frame

    def recv_buff(self, num=1024):
        rx_str = ""
        frame = []
        frameIndex = 0
        framestr = ""
        if num < self.ser.in_waiting:
            rx_str = self.ser.read(num)
        else:
            rx_str = self.ser.read(self.ser.in_waiting)
        rx_str = self.str_tail + rx_str
        for tempdate in rx_str:
            if tempdate != '\r':
                framestr += tempdate
            else:
                frame.append(self.paserRecvCAN(framestr))
                frameIndex += 1
                framestr = ""
        self.str_tail = framestr
        return frame

    def send(self, frame):
        # add type, id, and dlc to string
        tx_str = "%s%03X%d" % ('t', frame.id, frame.dlc)
        if frame.is_extended_id is True and frame.frame_type == can.FrameType.DataFrame:
            tx_str = "%s%09X%d" % ('T', frame.id, frame.dlc)
        elif frame.is_extended_id is False and frame.frame_type == can.FrameType.DataFrame:
            tx_str = "%s%03X%d" % ('t', frame.id, frame.dlc)
        elif frame.is_extended_id is True and frame.frame_type == can.FrameType.RemoteFrame:
            tx_str = "%s%09X%d" % ('R', frame.id, 0)
        elif frame.is_extended_id is False and frame.frame_type == can.FrameType.RemoteFrame:
            tx_str = "%s%03X%d" % ('r', frame.id, 0)

        if frame.dlc > 0 and frame.frame_type == can.FrameType.DataFrame:
            # add data bytes to string
            for i in range(0, frame.dlc):
                tx_str = tx_str + ("%02X" % frame.data[i])

        # add newline (\r) to string
        tx_str = tx_str + '\r'
        # send it
        self.ser.write(tx_str.encode())
