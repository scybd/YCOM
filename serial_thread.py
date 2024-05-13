from PyQt5.QtCore import pyqtSignal, QObject
import threading
from PyQt5.QtSerialPort import QSerialPort


class SerialThreadFunction(QObject):

    signal_initSerial = pyqtSignal()
    signal_openCom = pyqtSignal(object)
    signal_openComFlag = pyqtSignal(object)
    signal_redData = pyqtSignal(object)
    signal_DTR = pyqtSignal(object)
    signal_RTS = pyqtSignal(object)
    signal_sendData = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.state = 0  # 0-关闭 1-打开 2-打开失败

    def slot_openCom(self, param):
        if self.state == 0:
            print(param)
            self.serial = QSerialPort()
            self.serial.setPortName(param['comboBox_com'])
            self.serial.setBaudRate(int(param['comboBox_baud']))
            self.serial.setDataBits(int(param['comboBox_data']))

            if param['comboBox_stop'] == '1.5':
                self.serial.setStopBits(3)
            else:
                self.serial.setStopBits(int(param['comboBox_stop']))

            if param['comboBox_check'] == 'None':
                self.serial.setParity(0)
            elif param['comboBox_check'] == 'Odd':
                self.serial.setParity(3)
            else:
                self.serial.setParity(2)

            if self.serial.open(QSerialPort.ReadWrite):
                self.serial.readyRead.connect(self.slot_recData)    # 打开成功后开始接收数据
                self.state = 1
                self.signal_openComFlag.emit(self.state)
            else:
                self.signal_openComFlag.emit(2)

        elif self.state == 1:
            self.state = 0
            self.serial.close()
            self.signal_openComFlag.emit(self.state)

    def slot_recData(self):
        # 串口线程接收到数据后传给主线程显示
        self.signal_redData.emit(self.serial.readAll())

    def slot_DTR(self, state):
        if state == 2:
            self.serial.setDataTerminalReady(True)
        else:
            self.serial.setDataTerminalReady(False)

    def slot_RTS(self, state):
        if state == 2:
            self.serial.setRequestToSend(True)
        else:
            self.serial.setRequestToSend(False)

    def slot_sendData(self, sendData):
        if self.state != 1:
            return
        if sendData['hex'] == 2:
            sendList = []
            sendText = sendData['data']
            while sendText != '':
                try:
                    num = int(sendText[0:2], 16)
                except:
                    return
                sendText = sendText[2:].strip()
                sendList.append(num)
            sendList = bytes(sendList).decode()
            if sendData['new_line'] == 2:
                sendList += '\r\n'
            sendList = str.encode(sendList)
            self.serial.write(sendList)
        else:
            if sendData['new_line'] == 2:
                sendData['data'] += '\r\n'
            byteData = str.encode(sendData['data'])
            self.serial.write(byteData)
