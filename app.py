import os
import sys
from enum import Enum
from PyQt5 import uic
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5.QtWidgets import *
import RPi.GPIO as GPIO
import time

# Pin 22 used with pump
# Relay is active low
# 31 = Evalvecontrol 1 (KVL), 29 = Evalvecontrol 2 (KCL), 26 = Evalvecontrol 3 (Capacitor top), 24 = Evalvecontrol 4 (Inductor), 23 = Evalvecontrol 5 (Capacitor bottom)
ValvePins = [22, 31, 29, 26, 24, 23]

GPIO.setwarnings(False)

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
        
                
        def Change_Text( main_window, Text ):
            if Text == "KVL":
                main_window.Dyanmic_current_KVL.setText(Text)
            elif Text == "KCL":
                main_window.Dyanmic_current_KVL.setText(Text)
            elif Text == "IND":
                main_window.Dyanmic_current_KVL.setText(Text)
            elif Text == "CAP":
                main_window.Dyanmic_current_KVL.setText(Text)

        if( page_number == Page.KVL_ON.value ):
            Current = BoardFunctions.KVL()
            Change_Text( main_window, Current )
        elif( page_number == Page.KCL_ON.value ):
            BoardFunctions.KCL()
        elif( page_number == Page.CAP_ON.value ):
            BoardFunctions.Capacitor()
        elif( page_number == Page.IND_ON.value ):
            BoardFunctions.Inductor()
        else:
            BoardFunctions.Idle_State()

            
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
        clickable( main_window.KCL_label ).connect( self.label_KCL)
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



class BoardFunctions():
    # Pins used for Valves
    def setup():
        global ValvePins
        GPIO.setmode(GPIO.BOARD)
        for i in range(0,6):
            GPIO.setup( ValvePins[i] , GPIO.OUT, initial=GPIO.HIGH )
    
    def Turnoff():
        global ValvePins
        GPIO.output( ValvePins, GPIO.HIGH )
        GPIO.cleanup

    # Setup for KVL mode
    def KVL():
        global ValvePins
        FlowPins = [15] 
        GPIO.output( ValvePins[0], GPIO.LOW )
        GPIO.output( ValvePins[1], GPIO.LOW )
        print("In KVL state")
        KVL = "KVL"
        Current = BoardFunctions.FlowSensor( 1, FlowPins, KVL, 0.042 )
        return Current
        # Code here for outputing current information and LED output

    # Setup for KCL mode
    def KCL():
        global ValvePins
        FlowPins = [37, 38, 40]
        GPIO.output( ValvePins[0], GPIO.LOW )
        GPIO.output( ValvePins[2], GPIO.LOW )
        print("In KCL state")
        KCL = "KCL"
        Currents = BoardFunctions.FlowSensor( 3, FlowPins, KCL, 0.2 )
        return Currents
    # Setup for Capacitor mode
    def Capacitor():
        global ValvePins
        # Idle_State( False )
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
        # Should both the bottom and top valve be open at the begining, just the top valve open? This needs to be decided

    # Setup for Inductor mode
    def Inductor():
        global ValvePins
        # Idle_State( State )
        GPIO.output( ValvePins[0], GPIO.LOW )
        GPIO.output( ValvePins[4], GPIO.LOW )        # Code here for outputing current information and LED output
        print("In Inductor state")
        
    def Idle_State():
        GPIO.output( ValvePins[0], GPIO.HIGH )
        GPIO.output( ValvePins[1], GPIO.HIGH )
        GPIO.output( ValvePins[2], GPIO.HIGH )
        GPIO.output( ValvePins[3], GPIO.HIGH )
        GPIO.output( ValvePins[4], GPIO.HIGH )
        GPIO.output( ValvePins[5], GPIO.LOW )
        print("In Idle State")

    def FlowSensor( amount_of_pins, Pins, Type, CON ):
        time.sleep(5)
        for i in range(0, amount_of_pins):
            GPIO.setup(Pins[i],GPIO.IN)
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
        return str(Gal)

# Handles everything for to launch the GUI
def main():
    BoardFunctions.setup()
    app = QApplication( sys.argv )
    window = Ui_MainWindow()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
