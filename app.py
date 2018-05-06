import os
import sys
from enum import Enum
from PyQt5 import QtCore 
from PyQt5.QtCore import QThread 
from PyQt5.QtCore import pyqtSignal
from PyQt5 import uic
from PyQt5 import QtGui
from PyQt5.QtWidgets import *
import RPi.GPIO as GPIO
import time

# Pin 22 used with pump
# Relay is active low
# 31 = Evalvecontrol 1 (KVL), 29 = Evalvecontrol 2 (KCL), 26 = Evalvecontrol 3 (Capacitor top), 24 = Evalvecontrol 4 (Inductor), 23 = Evalvecontrol 5 (Capacitor bottom)
ValvePins = [22, 31, 29, 26, 24, 23]
KVL_Flow_Pins = [15]
KCL_Flow_Pins = [37, 38, 40]
CAP_Flow_Pins = [18, 19]
IND_Flow_Pins = [21]
GPIO.setwarnings(False)

# Everything GPIO related in terms of pins
class BoardFunctions():
    def setup():
        global ValvePins
        GPIO.setmode(GPIO.BOARD)
        for i in range(0,6):
            GPIO.setup( ValvePins[i] , GPIO.OUT, initial=GPIO.HIGH )
    
    def Turnoff():
        global ValvePins
        GPIO.output( ValvePins, GPIO.HIGH ) # all to high as relay is active low
        GPIO.cleanup

    # Setup for KVL mode
    def KVL():
        global ValvePins
        GPIO.output( ValvePins[0], GPIO.LOW )
        GPIO.output( ValvePins[1], GPIO.LOW )
        print("In KVL state")

    # Setup for KCL mode
    def KCL():
        global ValvePins
        GPIO.output( ValvePins[0], GPIO.LOW )
        GPIO.output( ValvePins[2], GPIO.LOW )
        print("In KCL state")

    # Setup for Capacitor mode
    def Capacitor():
        global ValvePins
        GPIO.output( ValvePins[0], GPIO.LOW )
        GPIO.output( ValvePins[3], GPIO.LOW )
        GPIO.output( ValvePins[5], GPIO.LOW )
        print("In Capacitor state")
        time.sleep(5)
        GPIO.output( ValvePins[5], GPIO.LOW )
        GPIO.output( ValvePins[0], GPIO.HIGH )
        GPIO.output( ValvePins[3], GPIO.HIGH )
        time.sleep(9)
        GPIO.output( ValvePins[5], GPIO.HIGH )

    # Setup for Inductor mode
    def Inductor():
        global ValvePins
        GPIO.output( ValvePins[0], GPIO.LOW )
        GPIO.output( ValvePins[4], GPIO.LOW )
        print("In Inductor state")
        
    def Idle_State():
        GPIO.output( ValvePins[0], GPIO.HIGH )
        GPIO.output( ValvePins[1], GPIO.HIGH )
        GPIO.output( ValvePins[2], GPIO.HIGH )
        GPIO.output( ValvePins[3], GPIO.HIGH )
        GPIO.output( ValvePins[4], GPIO.HIGH )
        GPIO.output( ValvePins[5], GPIO.LOW )
        print("In Idle State")

# everything water sensor realted for reading in water flow
class Water_Sensor( QThread ):

    change_current = pyqtSignal(str, str)

    def __init__(self, Flow_pins, amt_of_pins, Type, Constant):
        QThread.__init__(self)
        self._is_running = True
        self.Flow_pins = Flow_pins
        self.amt_of_pins = amt_of_pins
        self.Type = Type
        self.Constant = Constant
        
    def _FlowSensor( self, amount_of_pins, Pins, Type, CON ):
        for i in range(0, amount_of_pins):
            rate_cnt=0
            tot_cnt=0
            minutes=0
            constant= CON 
            time_new=0.0
            stop_time=0.0
            gpio_last=2

            for sec_mult in range(0,1):
                time_new=time.time()+.5
                rate_cnt=0              
                while time.time() <= time_new:
                    gpio_cur=GPIO.input(Pins[i])
                    if gpio_cur !=gpio_last:
                        rate_cnt+=1
                        tot_cnt +=1
                    else:
                        rate_cnt=rate_cnt
                        tot_cnt=tot_cnt
                        
                    gpio_last=gpio_cur
            minutes+=1
            print('\nFrequency',
                    round(rate_cnt/2,4),'approximate')
            print('Gallons/min',
                    round(rate_cnt*constant,4),'approximate')
            Gal = []
            Gal = round(rate_cnt*constant,4)
        self.change_current.emit(str(Gal), Type)
        return

    def __del__(self):
        self.wait()

    def stop(self):
        self._is_running = False

    # will conitnously run until a signal is sent from the UI terminating the thread
    def run(self):
        GPIO.setup( self.Flow_pins, GPIO.IN )
        while self._is_running == True:
            self._FlowSensor(self.amt_of_pins, self.Flow_pins, self.Type, self.Constant)
        


# eveything LED realted and control through this information
# class LED_Control( QThread ):


class Ui_MainWindow( QMainWindow ):
    def __init__( self ):
        super().__init__()
        self.width = 800
        self.height = 480
        self.init()

    def init( self ):
        main_window = uic.loadUi( "gui.ui", self )
        
        self.main_window = main_window

        # Initialize gui xml
        main_window.setFixedSize( self.width, self.height )

        # Initialize I/O
        self.add_functionality( main_window )

        # Set to first page
        main_window.stackedWidget.setCurrentIndex( Page.Main_Page.value )
        self.showFullScreen()

    def start( self, main_window ):
        # first see which page is selected
        # then executes the functions needed for what is selected
        page_number = main_window.stackedWidget.currentIndex()
           
        def Update_Current(Text, Type):
            HTML = '<html><head/><body><p align="center"><span style=" font-size:12pt; font-weight:600;">' + Text + ' (A)' + '</span></p></body></html>'
            if Type == "KVL":
                main_window.Dyanmic_current_KVL.setText( HTML )
            elif Type == "KCL":
                main_window.Dynamic_current_KCL.setText( HTML )
            elif Type == "IND":
                main_window.Dyanmic_Current_Inductor.setText( HTML )
            elif Type == "CAP":
                main_window.Dynamic_Current_Capacitor.setText( HTML )
            else:
                print("There was no \'Type\' found.")
                return


        if( page_number == Page.KVL_ON.value ):
            BoardFunctions.KVL()
            self.thread = Water_Sensor( KVL_Flow_Pins, 1, "KVL", 0.02 )
            self.thread.start()
            self.thread.change_current.connect(Update_Current)
        elif( page_number == Page.KCL_ON.value ):
            # maybe have three threads here for the all three flow readers to be reading at the same time
            BoardFunctions.KCL()
            self.thread = Water_Sensor( KCL_Flow_Pins, 3, "KCL", 0.2 )
            self.thread.start()
            self.thread.change_current.connect(Update_Current)
        elif( page_number == Page.CAP_ON.value ):
            self.thread = Water_Sensor( CAP_Flow_Pins, 2, "CAP", 0.1 )
            self.thread.start()
            self.thread.change_current.connect(Update_Current)
            BoardFunctions.Capacitor()
        elif( page_number == Page.IND_ON.value ):
            BoardFunctions.Inductor()
            self.thread = Water_Sensor( IND_Flow_Pins, 1, "IND", 0.1 )
            self.thread.start()
            self.thread.change_current.connect(Update_Current)
        else:
            self.Stop_thread()
            BoardFunctions.Idle_State()
            
    # Stops the thread safely (Will not stop thread otherwise, please leave in or there will be lots of issues)    
    def Stop_thread(self):
        self.thread.stop()
        self.thread.quit()
        self.thread.wait()

    # initalize actions to occur from user
    def add_functionality( self, main_window ):
        self.init_labels( main_window )
        self.init_buttons( main_window )
        self.init_menubar( main_window )

    # Goes to the correct page when a button is clicked
    def init_labels( self, main_window ):
        clickable( main_window.Capacitor_picture ).connect( self.label_capacitor )
        clickable( main_window.Capacitor_label ).connect( self.label_capacitor )
        clickable( main_window.Inductor_picture ).connect( self.label_inductor )
        clickable( main_window.Inductor_label ).connect( self.label_inductor) 
        clickable( main_window.KCL_picture ).connect( self.label_KCL )
        clickable( main_window.KCL_label ).connect( self.label_KCL )
        clickable( main_window.KVL_picture ).connect( self.label_KVL ) 
        clickable( main_window.KVL_label ).connect( self.label_KVL )

    def label_KVL( self ):
        self.main_window.stackedWidget.setCurrentIndex( Page.KVL_OFF.value )
    def label_KCL( self ):
        self.main_window.stackedWidget.setCurrentIndex( Page.KCL_OFF.value )
    def label_capacitor( self ):
        self.main_window.stackedWidget.setCurrentIndex( Page.CAP_OFF.value )
    def label_inductor( self ):
        self.main_window.stackedWidget.setCurrentIndex( Page.IND_OFF.value )


    # initalizing buttons
    def init_buttons( self, main_window ):
        # These all lead back to the main menu
        main_window.Main_menu_KVL_off.clicked.connect( lambda: self.push_button_back( main_window ))
        main_window.Main_menu_KVL_ON.clicked.connect( lambda: self.push_button_back( main_window ))
        main_window.Main_menu_KCL_off.clicked.connect( lambda: self.push_button_back( main_window ))
        main_window.Main_Menu_KCL_On.clicked.connect( lambda: self.push_button_back( main_window ))
        main_window.Main_menu_Capacitor_off.clicked.connect( lambda: self.push_button_back( main_window ))
        main_window.Main_Menu_Cap_On.clicked.connect( lambda: self.push_button_back( main_window ))
        main_window.Main_Menu_IND_Off.clicked.connect( lambda: self.push_button_back( main_window ))
        main_window.Main_Menu_Inductor_On.clicked.connect( lambda: self.push_button_back( main_window ))

        main_window.Start_button_KVL_off.clicked.connect( lambda: self.push_button_KVL_start( main_window ))
        main_window.Stop_button_KVL.clicked.connect( lambda: self.push_button_KVL_stop( main_window ))
        main_window.Start_Button_KCL.clicked.connect( lambda: self.push_button_KCL_start( main_window ))
        main_window.Stop_KCL.clicked.connect( lambda: self.push_button_KCL_stop( main_window ))
        main_window.Capacitor_Start_Button.clicked.connect( lambda: self.push_button_CAP_start( main_window ))
        main_window.Stop_Button_Capacitor.clicked.connect( lambda: self.push_button_CAP_stop( main_window ))
        main_window.Start_Button_Inductor.clicked.connect( lambda: self.push_button_IND_start( main_window ))
        main_window.Stop_Button_Inductor.clicked.connect( lambda: self.push_button_IND_stop( main_window ))

    def push_button_back( self, main_window ):
        main_window.stackedWidget.setCurrentIndex( Page.Main_Page.value )
        self.start( main_window )

    def push_button_KVL_start( self, main_window ):
        main_window.stackedWidget.setCurrentIndex( Page.KVL_ON.value )
        self.start( main_window )
    def push_button_KVL_stop( self, main_window ):
        main_window.stackedWidget.setCurrentIndex( Page.KVL_OFF.value )
        self.start( main_window )

    def push_button_KCL_start( self, main_window ):
        main_window.stackedWidget.setCurrentIndex( Page.KCL_ON.value )
        self.start( main_window )
    def push_button_KCL_stop( self, main_window ):
        main_window.stackedWidget.setCurrentIndex( Page.KCL_OFF.value )
        self.start( main_window )

    def push_button_CAP_start( self, main_window ):
        main_window.stackedWidget.setCurrentIndex( Page.CAP_ON.value )
        self.start( main_window )
    def push_button_CAP_stop( self, main_window ):
        main_window.stackedWidget.setCurrentIndex( Page.CAP_OFF.value )
        self.start( main_window )
    
    def push_button_IND_start( self, main_window ):
        main_window.stackedWidget.setCurrentIndex( Page.IND_ON.value )
        self.start( main_window )
    def push_button_IND_stop( self, main_window ):
        main_window.stackedWidget.setCurrentIndex( Page.IND_OFF.value )
        self.start( main_window )

    def init_menubar( self, main_window ):
        main_window.actionExit.triggered.connect( self.terminate ) 

    def terminate( self ):
        BoardFunctions.Turnoff()
        sys.exit()

# changes pages to number
class Page( Enum ):
    Main_Page = 0
    KVL_OFF = 1
    KVL_ON = 2
    KCL_OFF = 3
    KCL_ON = 4
    CAP_OFF = 5
    CAP_ON = 6
    IND_OFF = 7
    IND_ON = 8

# allows pictures to be clicked on
def clickable( widget ):
    class Filter( QtCore.QObject ):
        clicked = QtCore.pyqtSignal()

        def eventFilter( self, obj, event ):
            if obj == widget and event.type() == QtCore.QEvent.MouseButtonRelease and obj.rect().contains( event.pos() ):
                self.clicked.emit()
                return True
            return False
    filter = Filter( widget )
    widget.installEventFilter( filter )
    return filter.clicked

# Handles everything for to launch the GUI
def main():
    BoardFunctions.setup()          # Setup board to properly turn on the pins to the right mode
    app = QApplication( sys.argv ) 
    window = Ui_MainWindow()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
