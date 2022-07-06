"""
Atitude Determination Monitoring by PiPico
Author : Porya M. Nilaore
Date : 2022/06/09
"""
from PyQt5 import uic
import PyQt5.QtWidgets as qtw
import PyQt5.QtGui as qtg
from PyQt5.QtCore import QTimer, QTime
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWebEngineWidgets import QWebEngineView
from serial import Serial
import datetime as dt
import sys
import io
import folium

# Define global variables:
global com_port
global com_baudrate

latitude = 35.69980007202098
longitude = 51.33802050209452
altitude = 1280
satNo = 6
wx = 0 
wy = 0
wz = 0
ax = 0
ay = 0
az = 9.81
#compang = 7
#compdir = 'E'
#spd = 72.3
fix = 0
battery = 100
data_res = []
T = 0

#TODO: Check operation system type and do below function as it
#TODO: Move this content to com module 
def windows_serial_ports():
    import winreg
    import itertools
    
    path = 'HARDWARE\\DEVICEMAP\\SERIALCOMM'
    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path)

    win_ports = []
    for i in itertools.count():
        try:
            win_ports.append(winreg.EnumValue(key, i)[1])
        except EnvironmentError:
            break

    return win_ports

def general_ports():
    import serial.tools.list_ports as ser_ports
    
    com_ports = list(ser_ports.comports())

    return com_ports

# Date and Time Function
def now():
    dtime = dt.datetime.now()
    YYYY = dtime.year
    MO = dtime.month
    DD = dtime.day
    HH = dtime.hour
    MM = dtime.minute
    SS = dtime.second
    ex_time = "{}/{}/{} - {}:{}:{}".format(YYYY,MO,DD,HH,MM,SS)
    return ex_time
    
    
# Port and Baudrate Selection Window
class PBWin(qtw.QWidget):
    def __init__(self):
        super(PBWin, self).__init__()
        
        # Load Ui file that was created with qtdesigner:
        uic.loadUi("PBWin.ui", self)
        
        # Define Widgets:
        # sample if use xml to define :
        # self.bla = self.findChild(ClassName, "objectname")
        self.portCombo = self.findChild(qtw.QComboBox, "portsList")
        self.baudCombo = self.findChild(qtw.QComboBox, "baudratesList")  
        self.selectButt = self.findChild(qtw.QPushButton, "selectButton")   
        self.exitButt = self.findChild(qtw.QPushButton, "exitButton") 
        
        # Port ComboBox:
        for i in general_ports():
            self.portCombo.addItem(str(i),i.device)
        
        # Baudrate ComboBox:
        self.baudCombo.addItem("4800", 4800)
        self.baudCombo.addItem("9600", 9600)
        self.baudCombo.addItem("14400", 14400)
        self.baudCombo.addItem("19200", 19200)
        self.baudCombo.addItem("38400", 38400)
        self.baudCombo.addItem("57600", 57600)
        self.baudCombo.addItem("115200", 115200)        
        
        # Do operation :
        self.selectButt.clicked.connect(self.clicker)       
        self.exitButt.clicked.connect(self.close)
        #self.portCombo.clicked.connect(self.comboClick)
        
        self.show()
    
    # define another window
    def openADSWin(self):
        self.ADS = ADSWin()
        self.ADS.show()
        
    # Check buttons an comboboxes operation
    def clicker(self):
        #try:
          
        global com_port
        global com_baudrate 
        com_port = str(self.portCombo.currentData())            
        com_baudrate = int(self.baudCombo.currentData())
        
        self.openADSWin()
        self.close()
        
        #except TypeError:
            #print("Error")
              

# Attitude Determination System Window
class ADSWin(qtw.QMainWindow):
    def __init__(self):
        super(ADSWin, self).__init__()
        
        # Load Ui file that was created with qtdesigner:
        uic.loadUi("ADSWin.ui", self)

        self.show()
        
        # Define variables
        global latitude
        global longitude
        global altitude
        global satNo
        global wx
        global wy
        global wz
        global ax
        global ay
        global az
        global battery
        
        # Define widgets               
        self.exitbutt = self.findChild(qtw.QMenu, "menuFile") # define exit button in menubar
        self.timebrowser = self.findChild(qtw.QTextBrowser, "dateTimeBrowser") # define date and time text browser
        self.portbaudrate = self.findChild(qtw.QTextBrowser, "portBaudrateBrowser") # define port and baudrate text browser
        self.mapview = self.findChild(qtw.QVBoxLayout, "verticalLayout_2")
        self.axlcd = self.findChild(qtw.QLCDNumber, "lcdNumber")
        self.aylcd = self.findChild(qtw.QLCDNumber, "lcdNumber_2")
        self.azlcd = self.findChild(qtw.QLCDNumber, "lcdNumber_3")
        self.wxlcd = self.findChild(qtw.QLCDNumber, "lcdNumber_6")
        self.wylcd = self.findChild(qtw.QLCDNumber, "lcdNumber_4")
        self.wzlcd = self.findChild(qtw.QLCDNumber, "lcdNumber_5")
        self.latlcd = self.findChild(qtw.QLCDNumber, "lcdNumber_9")
        self.longlcd = self.findChild(qtw.QLCDNumber, "lcdNumber_7")
        self.altlcd = self.findChild(qtw.QLCDNumber, "lcdNumber_10")
        self.satNo = self.findChild(qtw.QLCDNumber, "lcdNumber_11")
        self.fixlcd = self.findChild(qtw.QLCDNumber, "lcdNumber_12")
        #self.compdirlcd = self.findChild(qtw.QTextBrowser, "textBrowser")
        self.battlcd = self.findChild(qtw.QLCDNumber, "lcdNumber_8")
        self.templcd = self.findChild(qtw.QLCDNumber, "lcdNumber_13")
        self.webView = QWebEngineView()
        
        # Display info
        # TODO: do tihs with thread
        self.com_buad = ("{} - {}".format(com_port, com_baudrate))
        self.portbaudrate.append(self.com_buad)

        ## Map
        self.coordinate = (latitude, longitude)
        self.map = folium.Map(location=self.coordinate, zoom_start=14)
        folium.Marker(self.coordinate, popup='GeneralPMN', tooltip='click').add_to(self.map)
        data = io.BytesIO()
        self.map.save(data, close_file=False)
        webView = QWebEngineView()
        webView.setHtml(data.getvalue().decode())
        self.mapview.addWidget(webView)
        
        # Do somethings
        self.exitbutt.triggered.connect(self.exitApp)
    
        self.thread = GetData(self)
        self.thread.dataChanged.connect(self.onDataChanged  )
        self.thread.start()
        
    def onDataChanged(self, latitude, longitude, altitude, satNo, fix, wx, wy, wz, ax, ay, az, T):
        self.timebrowser.append(now()) # display date and time
        self.latlcd.display(latitude)
        self.longlcd.display(longitude)
        self.altlcd.display(altitude)
        self.satNo.display(satNo)
        self.fixlcd.display(fix)
        self.wxlcd.display(wx)
        self.wylcd.display(wy)
        self.wzlcd.display(wz)
        self.axlcd.display(ax)
        self.aylcd.display(ay)
        self.azlcd.display(az)
        self.templcd.display(T)

        self.battlcd.display(battery)
        
    def exitApp(self):
        self.close()

class GetData(QThread):
    #dataChanged = pyqtSignal(float, float, float, float, float, float, float, float, float, float, float)
    dataChanged = pyqtSignal(str, str, str, str, str, str, str, str, str, str, str, str)
    def __ini__(self, parent=None):
        global com_port
        global com_baudrate
        
        QThread.__init__(self, parent)
            
    def __del__(self):
        self.wait()
        
    def run(self):
        global latitude
        global longitude
        global altitude
        global satNo
        global fix
        global wx
        global wy
        global wz
        global ax
        global ay
        global az
        global T
        
        self.serial_init()
        while True:
            self.unpack(self.packet())
            latitude = latitude
            longitude = longitude
            altitude = altitude
            satNo = satNo
            fix = fix
            wx = wx
            wy = wy
            wz = wz
            ax = ax
            ay = ay
            az = az
            T = T
            self.dataChanged.emit(latitude, longitude, altitude, satNo, fix, wx, wy, wz, ax, ay, az, T)
    
    def serial_init(self):
        self.ser = Serial(com_port, com_baudrate)     
        self.ser.close()
        self.ser.open()
        self.ser.flush()
        self.ser.reset_input_buffer()
        
    def packet(self):
        global data_res
        raw_data = self.ser.read(120).decode("utf-8")
        data_array = raw_data.rstrip().split(',')
        self.ser.reset_input_buffer()

        try:
            if '' in data_array:
                data_array.remove('')
        except ValueError:
            pass
        
        if 'S' in data_array:
            S_flag = True
        else:
            S_flag = False
            
        if 'ES' in data_array:
            ES_flag = True
        else:
            ES_flag = False
        
        if S_flag and ES_flag == True:
            data_res = []
            start = data_array.index('S')
            end = data_array.index('ES')
            data = data_array[start:end]
            data_res = data_array[end:-1]
            data_res.append(data_array[-1])
        else:
            end = data_array.index('ES')
            if len(data_res) != 0:
                j = 0
                for i in data_array:
                    if j == end:
                        data = data_res
                        data_res = [] 
                    data_res.append(i)
                    j += 1
        
        return data
        
    def unpack(self,data):
        global latitude
        global longitude
        global altitude
        global satNo
        global fix
        global wx
        global wy
        global wz
        global ax
        global ay
        global az
        global T
        
        try:
            latitude = data[2]
            longitude = data[3]
            altitude = data[4]
            satNo = data[5]
            fix = data[6]
            ax = data[8]
            ay = data[9]
            az = data[10]
            wx = data[11]
            wy = data[12]
            wz = data[13]
            T = data[14]
        except:
            latitude = latitude
            longitude = longitude
            altitude = altitude
            satNo = satNo
            fix = fix
            ax = ax
            ay = ay
            az = az
            wx = wx
            wy = wy
            wz = wz
            T = T

                                                 
#Initialize the App      
try:
    app = qtw.QApplication(sys.argv)
    
    PBWindow = PBWin()
    #ADSWindow = ADSWin()
    app.exec_() 
    
except SystemExit:
    print("Close Windows ...")