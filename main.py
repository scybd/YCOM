import os
import sys
import time
import PyQt5.QtWidgets as qw
from PyQt5 import QtGui
from PyQt5.QtGui import QTextCursor, QColor, QIcon

import main_ui
from PyQt5.QtCore import QThread, QTimer
from serial_thread import SerialThreadFunction
from PyQt5.QtSerialPort import QSerialPortInfo


class UIThread(qw.QWidget):
    def __init__(self):
        super().__init__()
        self.ui = main_ui.Ui_YCOM()
        self.ui.setupUi(self)
        self.initInterface()
        self.coms = []
        # print("主线程id", threading.current_thread().ident)

        self.serialThread = QThread()   # 创建串口线程
        self.serialThreadFunction = SerialThreadFunction()  # 创建串口线程运行的函数（类）
        self.serialThreadFunction.moveToThread(self.serialThread)   # 绑定串口线程和其函数
        self.serialThread.start()       # 开启串口线程

        # 连接信号和槽
        # 开启串口
        self.serialThreadFunction.signal_openCom.connect(self.serialThreadFunction.slot_openCom)
        # 串口开启状态
        self.serialThreadFunction.signal_openComFlag.connect(self.function_openComFlag)
        # 接收显示数据
        self.serialThreadFunction.signal_redData.connect(self.function_showData)
        # RTS,DTR,timeStamp
        self.serialThreadFunction.signal_RTS.connect(self.serialThreadFunction.slot_RTS)
        self.serialThreadFunction.signal_DTR.connect(self.serialThreadFunction.slot_DTR)
        # 发送数据
        self.serialThreadFunction.signal_sendData.connect(self.serialThreadFunction.slot_sendData)
        # 定时扫描可用串口
        self.signal_comScan = QTimer()
        self.signal_comScan.timeout.connect(self.function_comScan)
        self.signal_comScan.start(1000)
        # 定时发送
        self.signal_timeSend = QTimer()
        self.signal_timeSend.timeout.connect(self.function_timeSend)

    def initInterface(self):
        self.ui.comboBox_baud.addItems(('9600', '115200'))
        self.ui.comboBox_stop.addItems(('1', '1.5', '2'))
        self.ui.comboBox_data.addItems(('8', '7', '6', '5'))
        self.ui.comboBox_check.addItems(('None', 'Odd', 'Even'))
        self.ui.pushButton_open.clicked.connect(self.function_openCom)
        self.ui.checkBox_RTS.stateChanged.connect(self.function_RTS)
        self.ui.checkBox_DTR.stateChanged.connect(self.function_DTR)
        self.ui.checkBox_hex_send.stateChanged.connect(self.function_hexSend)
        self.ui.pushButton_send.clicked.connect(self.function_send)
        self.ui.checkBox_timed_send.stateChanged.connect(self.function_timeSendFlag)
        self.ui.lineEdit_cycle.setText('1000')
        self.ui.pushButton_clear_rec.clicked.connect(self.function_clearRec)
        self.ui.pushButton_clear_send.clicked.connect(self.function_clearSend)

    def function_comScan(self):
        avaComs = QSerialPortInfo.availablePorts()
        if len(self.coms) != len(avaComs):
            for com in avaComs:
                self.coms.append(com.portName())
            self.ui.comboBox_com.clear()
            self.ui.comboBox_com.addItems(self.coms)

    def function_openCom(self):
        comParams = {'comboBox_com': self.ui.comboBox_com.currentText(),
                     'comboBox_baud': self.ui.comboBox_baud.currentText(),
                     'comboBox_stop': self.ui.comboBox_stop.currentText(),
                     'comboBox_data': self.ui.comboBox_data.currentText(),
                     'comboBox_check': self.ui.comboBox_check.currentText()}
        self.serialThreadFunction.signal_openCom.emit(comParams)

    def function_openComFlag(self, state):
        if state == 0:
            self.ui.pushButton_open.setStyleSheet('QPushButton {background-color: red;}')
            self.ui.pushButton_open.setText("Open Serial")
        elif state == 1:
            self.ui.pushButton_open.setStyleSheet('QPushButton {background-color: green;}')
            self.ui.pushButton_open.setText("Close Serial")
            self.signal_comScan.stop()
        elif state == 2:
            self.ui.pushButton_open.setStyleSheet("")
            qw.QMessageBox.critical(self, "Error", "Fail to open it!")
            self.signal_comScan.start(1000)

    def function_showData(self, data):
        if self.ui.checkBox_time_stamp.checkState():
            timeStr = "\r\n" + time.strftime('%Y-%M-%D %H:%M:%S', time.localtime()) + "\r\n"
            self.ui.textEdit_rec.setTextColor(QColor(255, 100, 100))
            self.ui.textEdit_rec.insertPlainText(timeStr)
            self.ui.textEdit_rec.setTextColor(QColor(0, 0, 0))

        dataBytes = bytes(data)
        if self.ui.checkBox_hex_disp.checkState():  # 16进制显示
            dataView = ''
            for i in range(0, len(dataBytes)):
                dataView += '{:02x}'.format(dataBytes[i]) + ' '
            self.ui.textEdit_rec.insertPlainText(dataView)
        else:
            self.ui.textEdit_rec.insertPlainText(dataBytes.decode('utf-8', 'ignore'))
        self.ui.textEdit_rec.moveCursor(QTextCursor.End)

    def function_RTS(self, state):
        self.serialThreadFunction.signal_RTS.emit(state)

    def function_DTR(self, state):
        self.serialThreadFunction.signal_DTR.emit(state)

    def function_hexSend(self, state):
        sendData = self.ui.textEdit_send.toPlainText()
        if state == 2:
            sendData = str.encode(sendData)
            data = ''
            for i in range(0, len(sendData)):
                data += '{:02x}'.format(sendData[i]) + ' '
            self.ui.textEdit_send.setText(data)
        else:
            sendList = []
            while sendData != '':
                try:
                    num = int(sendData[0:2], 16)
                except:
                    qw.QMessageBox.warning(self, '错误信息', '请正确输入16进制数据')
                    return
                sendData = sendData[2:].strip()
                sendList.append(num)
            sendList = bytes(sendList)
            self.ui.textEdit_send.setText(sendList.decode())

    def function_send(self):
        sendData = {}
        sendData['data'] = self.ui.textEdit_send.toPlainText()
        sendData['hex'] = self.ui.checkBox_hex_send.checkState()
        sendData['new_line'] = self.ui.checkBox_send_new_line.checkState()
        self.serialThreadFunction.signal_sendData.emit(sendData)

    def function_timeSend(self):
        self.function_send()

    def function_timeSendFlag(self, state):
        if state == 2:
            timeData = self.ui.lineEdit_cycle.text()
            self.signal_timeSend.start(int(timeData))
        else:
            self.signal_timeSend.stop()

    def function_clearRec(self):
        self.ui.textEdit_rec.clear()

    def function_clearSend(self):
        self.ui.textEdit_send.clear()


basedir = os.path.dirname(__file__)

if __name__ == "__main__":
    app = qw.QApplication(sys.argv)
    app.setWindowIcon(QIcon(os.path.join(basedir, "imgs", "icon.svg")))
    w = UIThread()
    w.show()
    sys.exit(app.exec_())
