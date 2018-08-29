'''
Authors: Ian Shearer
         Alex Lam
         Shannon Fies

Date Created: 04/01/2018
Date Modified: 06/28/2018

Description: This project is a GUI created for the IEEE PES club at UCF.
             The project uses PyQt5 from the Qt library for creating the GUI (This is also used for the threading in this project)
             This GUI is controlled from a Raspberry Pi 3 where the GPIO pins control the valves and are used for measurements
             outputting in "Current" on the screen and feedbacking information to the LED controller
             LED controller done by the neopixel Library found here
             https://github.com/jgarff/rpi_ws281x       Main Author: Jeremy Garff 
'''

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
from neopixel import *

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
    # Relay is active LOW, therefore set the pins for the pins to HIGH to have the valves turned off
    def setup():
        global ValvePins
        GPIO.setmode(GPIO.BOARD)
        for i in range(0,6):
            GPIO.setup( ValvePins[i] , GPIO.OUT, initial=GPIO.HIGH )
    
    # When shutting down the system, Close valves and turn off pump
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
    # A timer is used for now as we set up better feedback from water sensor
    def Capacitor():
        global ValvePins
        GPIO.output( ValvePins[0], GPIO.LOW )  # Turn on pump/Open capacitor valves to get water pressure ready
        GPIO.output( ValvePins[3], GPIO.LOW )
        GPIO.output( ValvePins[5], GPIO.LOW )
        print("In Capacitor state")
        time.sleep(7)                          # Fill up capacitor (Pump and top/bottom valve turned on)
        GPIO.output( ValvePins[5], GPIO.LOW )
        GPIO.output( ValvePins[0], GPIO.HIGH )
        GPIO.output( ValvePins[3], GPIO.HIGH )
        time.sleep(9)                          # Hold charge by turning off pump, then release water after 9 seconds
        GPIO.output( ValvePins[5], GPIO.HIGH )

    # Setup for Inductor mode
    def Inductor():
        global ValvePins
        GPIO.output( ValvePins[0], GPIO.LOW )
        GPIO.output( ValvePins[4], GPIO.LOW )
        print("In Inductor state")
        
    # When no actions are going on, have everything off (valves closed/pump turned off) besides lower capacitor to discharge any excess water
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

    # water flow sensor code     
    def _FlowSensor( self, amount_of_pins, Pins, Type, CON ):
        for i in range(0, amount_of_pins):
            rate_cnt=0
            tot_cnt=0
            minutes=0
            constant= CON 
            time_new=0.0
            stop_time=0.0
            gpio_last=2

            # Loop to check switching between high and low from input, finding the frequency in Hz (Square wave)
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
        self.change_current.emit(str(Gal), Type) # Signal sending for feedback
        return

    # honestly don't know why this is here, but it will not shut down the thread if not here
    def __del__(self):
        self.wait()

    # constant used to stop the infinite loop controled by the Main Thread
    def stop(self):
        self._is_running = False

    # will conitnously run until a signal is sent from the UI terminating the thread
    def run(self):
        GPIO.setup( self.Flow_pins, GPIO.IN )
        while self._is_running == True:
            self._FlowSensor(self.amt_of_pins, self.Flow_pins, self.Type, self.Constant)
        
# Capacitor thread for LED control
class Capacitor_Thread( QThread ):

    def __init__(self, Pins):
        QThread.__init__(self)
        self.pins = Pins

    def __del__(self):
        self.wait()

    def stop(self):
        self._is_running = False

    def _Capacitor(self):
        GPIO.output( self.pins[0], GPIO.LOW )
        GPIO.output( self.pins[3], GPIO.LOW )
        GPIO.output( self.pins[5], GPIO.LOW )
        print("In Capacitor state")
        time.sleep(7)
        GPIO.output( self.pins[5], GPIO.LOW )
        GPIO.output( self.pins[0], GPIO.HIGH )
        GPIO.output( self.pins[3], GPIO.HIGH )
        time.sleep(9)
        GPIO.output( self.pins[5], GPIO.HIGH )

    def run(self):
        self._Capacitor()

# eveything LED realted and control through this information

class LED_Control( QThread ):
    

    def __init__(self):
        # Used to inherit the code into the thread
        QThread.__init__(self)
        # LED strip configuration
        self.LED_COUNT      = 177      # Number of LED pixels.
        self.LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
        self.LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
        self.LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
        self.LED_BRIGHTNESS = 200     # Set to 0 for darkest and 255 for brightest
        self.LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
        self.LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53
        self.strip = Adafruit_NeoPixel(self.LED_COUNT, self.LED_PIN, self.LED_FREQ_HZ, self.LED_DMA, self.LED_INVERT, self.LED_BRIGHTNESS, self.LED_CHANNEL)
        self._is_running = True

    def stop(self):
        self._is_running = False
    # controls the KVL LED's 
    def kVL(strip, freq1, color=Color(0,0,127), wait_ms=50, startOfSnake=0, endOfSnake=3):
        for i in range(43): #0-stripSize
            startOfSnake%=43 #to always show start even if value is over strip size
            endOfSnake%=43
            for j in range(startOfSnake, endOfSnake): #snakeSize
                strip.setPixelColor(j, color) #turn on those LEDs
                strip.show()
            time.sleep(wait_ms/(1000.0*freq1)) #delay
            strip.setPixelColor(startOfSnake, 0) #turn off the start
            strip.show()
            startOfSnake+=1 #so the snake will move along
            endOfSnake+=1
    
    # controls the KCL LEDs for the one wire section
    def kCLTop(strip, freq2, wait_ms=50):
        for i in range(14): #0-stripSize
            strip.setPixelColor(i+44, Color( 0,   127, 127)) #turn on those LEDs
            strip.show()
            time.sleep(wait_ms/(1000.0*freq2)) #delay
            strip.setPixelColor(i+44, 4) #turn off the start
            strip.show()

    # controls the KCL LEDs for the middle connection on bottom node
    def kCLMid(strip, freq3, freq4, wait_ms=50, x=0):
        #time.sleep(1)
        for i in range(3):
            if (i==0):
                strip.setPixelColor(74-i, Color(  0,   127, 127)) #turn on those LEDs
            else:    
                strip.setPixelColor(74-i, Color(  0,   127-freq4, 127)) #turn on those LEDs
                strip.setPixelColor(74+i, Color(  0,   127, 127-freq3)) #turn on those LEDs
            strip.show()
            time.sleep(wait_ms/1000.0) #delay
            strip.setPixelColor(74-i, 0) #turn off the start
            strip.setPixelColor(74+i, 0) #turn off the start
            strip.show()

    # Controls the left and right nodes of the KCL split
    def kCLLR(strip, freq3, freq4, wait_ms=100, x=0):
        """snakeing"""
        if (freq3>=freq4):
            r=freq3-freq4
            t=r*40
            for i in range(14):
                strip.setPixelColor(i+77,  Color(  0,   127, 127-(20*(freq3-freq4)))) #turn on those LEDs
                strip.show()
                for j in range(0,r):
                    strip.setPixelColor(((i+j+x)%14)+58,  Color(  0,   127-(20*(freq3-freq4)), 127)) #turn on those LEDs
                    strip.show()
                    time.sleep(wait_ms/1000.0) #delay
                    strip.setPixelColor(((i+j+x)%14)+58, 0)
                    strip.show()
                x+=r-1
                strip.setPixelColor(i+77, 0) #turn off the start
                strip.show()
            
        else:
            r=freq4-freq3
            for i in range(15): #0-stripSize
                for j in range(0,r):
                    strip.setPixelColor(i+j+77,  Color(  0,   0, 127-(freq3*20))) #turn on those LEDs
                    strip.show()
                    time.sleep(wait_ms/(1000.0+(r*100))) #delay
                    strip.setPixelColor(i+j+77, 0)
                strip.setPixelColor(i+58,  Color(  0,   127-(freq4*20) ,127)) #turn on those LEDs
                strip.show()
                time.sleep(wait_ms/1000.0) #delay
                strip.setPixelColor(i+58, 0) #turn off the start

    # Controls the capacitor LEDs
    # Fills the capacitor with the LED
    # Holds the LED there
    # Then drains from the Top of the LEDs to the empty
    def capacitorLEDs(strip, freq5, freq6, wait_ms=50, startOfCap=18, endOfCap=23, fill=23):
        """cap"""
        for x in range( 6):
            for i in range(24):
                if (i>=startOfCap and i<=endOfCap):
                    if ((i+x)>=endOfCap):
                        strip.setPixelColor(i+91, Color(0, 0, 127)) #turn off current LED
                        strip.show()
                        time.sleep((wait_ms*(1+abs(freq5-freq6))/1000.0))
                    else:
                        strip.setPixelColor(i+91, Color(0, 0, 127)) #turn off next LED
                        strip.show()
                        time.sleep((wait_ms*(1+abs(freq5-freq6)))/1000.0)
                        strip.setPixelColor(i+91, 0) #turn off next LED
                        strip.show()
                        
                else:
                    strip.setPixelColor(i+91, Color(0, 0, 127)) #turn off next LED
                    strip.show()
                    time.sleep((wait_ms*(1+abs(freq5-freq6)))/1000.0)
                    strip.setPixelColor(i+91, 0) #turn off next LED
                    strip.show()
                    
        for y in range( 6):
            strip.setPixelColor(y+109, Color(0, 0, 127)) #turn off current LED
            strip.show()
        
        for x in range( 6):
            for i in range(24):
                if(i==x):
                    strip.setPixelColor(x+109, Color(0, 0, 0)) #turn off current LED
                    strip.show()
                    time.sleep((wait_ms*(1+abs(freq5-freq6))/1000.0))
                        
                elif(i>7):
                    strip.setPixelColor(i+107, Color(0, 0, 127)) #turn off next LED
                    strip.show()
                    time.sleep((wait_ms*(1+abs(freq5-freq6)))/1000.0)
                    strip.setPixelColor(i+107, 0) #turn off next LED
                    strip.show()

    # Controls the inductor portion (goes slow to fast for "Wind up/Wind down" speed)  
    def inductorLEDs(strip, freq7, Color=Color(0,0,127), wait_ms=500, startOfSnake=0, endOfSnake=3):
        """inductor""" 
        for x in range(5):
            for i in range(44): #0-stripSize
                startOfSnake%= 44 #to always show start even if value is over strip size
                endOfSnake%= 44
                for j in range(startOfSnake, endOfSnake): #snakeSize
                    strip.setPixelColor(j+133, Color) #turn on those LEDs
                    strip.show()
                time.sleep(500.0/(wait_ms*freq7)) #delay
                strip.setPixelColor(startOfSnake+133, 0) #turn off the start
                strip.show()
                startOfSnake+=1 #so the snake will move along
                endOfSnake+=1
                wait_ms+=500 #to speed up
            wait_ms+=500 #to speed up

    # Function taken from example code
    def wheel(pos):
        """Generate rainbow colors across 0-255 positions."""
        if pos < 85:
            return Color(pos * 3, 255 - pos * 3, 0)
        elif pos < 170:
            pos -= 85
            return Color(255 - pos * 3, 0, pos * 3)
        else:
            pos -= 170
            return Color(0, pos * 3, 255 - pos * 3)

    # Pretty light show for when the system is in Idle mode (No specific processes going on)
    def Idle_LED(strip, wait_ms=1, iterations=5):
        """Draw rainbow that uniformly distributes itself across all pixels."""
        for j in range(256*iterations):
            for i in range(strip.numPixels()):
                strip.setPixelColor(i, LED_Control.wheel((int(i * 256 / strip.numPixels()) + j) & 255))
            strip.show()
            time.sleep(wait_ms/1000.0)

    def __del__(self):
        self.wait()

    def Turnoff(self):
        self.strip.Color(0,0,0) # This should Turn off all of the LEDs during shutdown
        time.sleep(0.1) # To make sure that shut down is done properly

    # What the thread is executing, this should always be running
    def run(self):
        self.strip.begin()
        while self._is_running == True:
            LED_Control.Idle_LED(self.strip)
            self.thread.change_current.connect(Current, Type) # Does this place it in the variable??
            if Type == "Idle":
                LED_Control.Idle_LED(self.strip)
            elif Type == "KVL":
                LED_Control.kVL(self.strip, Current)
            # elif Type == "KCL": # Not sure how to do this this one
            elif Type == "CAP":
                LED_Control.capacitorLEDs(self.strip) # This shouldn't need any feed back to control the flow as this is mostly constant
            elif Type == "IND":
                LED_Control.inductorLEDs(self.strip) # Should need any feedback as well as this will be nearly constant too.
                                                     # Maybe we can make it so when it stops it will start draining???
            else:
                Idle_LED(strip)  # If it is anything else put it in Idle mode (Default) 
                print("Went into else mode, change the Type: %s" % (Type)) # Used for debugging where the wrong type is being placed

# Main thread (Controls all UI options)
class Ui_MainWindow( QMainWindow ):
    def __init__( self ):
        super().__init__()
        self.width = 800    # Max width and height for the RPi screen (Pixel Dimensions)
        self.height = 480
        self.init()
        # self.LED_thread = LED_Control()

    # init based off of PyQt5 documentation
    def init( self ):
        # loads the xml style inforamtion from the file labeled gui.ui (must be in same directory)
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
        page_number = main_window.stackedWidget.currentIndex()
        # We want the LED thread to be running all the time (Can change this later if need be)
        self.LED_thread = LED_Control()
        self.LED_thread.start()
           
        # Takes the current obtained from the the feedback code and displays it where necessary
        # You can change the style of how it looks changing the HTML and the GUI will take care of the rest
        def Update_Current(Text, Type):
            HTML = '<html><head/><body><p align="center"><span style=" font-size:12pt; font-weight:600;">' + Text + ' (A)' + '</span></p></body></html>'
            if Type == "KVL":
                main_window.Dyanmic_current_KVL.setText( HTML )
            elif Type == "KCL":
                main_window.Dynamic_current_KCL.setText( HTML )
            elif Type == "KCL2":
                main_window.Dynamic_current_KCL_2.setText( HTML )
            elif Type == "KCL3":
                main_window.Dyanmic_current_KCL_3.setText( HTML )
            elif Type == "IND":
                main_window.Dyanmic_Current_Inductor.setText( HTML )
            elif Type == "CAP":
                main_window.Dynamic_Current_Capacitor.setText( HTML )
            elif Type == "CAP2":
                main_window.Dynamic_Current_Capacitor_2.setText( HTML )
            else:
                print("There was no \'Type\' found. Type listed is: %s" % (Type))
                return

        # If KVL section was selected, start the KVL pins and feedback thread
        if( page_number == Page.KVL_ON.value ):
            BoardFunctions.KVL()
            self.thread = Water_Sensor( KVL_Flow_Pins, 1, "KVL", 0.02 )
            self.thread.start()
            self.thread.change_current.connect(Update_Current)
        # If KCL section is selected, start the KCL thread and a thread for each sensor for feedback from all sensors    
        elif( page_number == Page.KCL_ON.value ):
            # Three sperate threads running here for each of the flow sensors
            BoardFunctions.KCL()
            self.thread = Water_Sensor( KCL_Flow_Pins[0], 1, "KCL", 0.2 )
            self.thread.start()
            self.thread.change_current.connect(Update_Current)
            self.thread1 = Water_Sensor( KCL_Flow_Pins[1], 1, "KCL2", 0.2 )
            self.thread1.start()
            self.thread1.change_current.connect(Update_Current)
            self.thread2 = Water_Sensor( KCL_Flow_Pins[2], 1, "KCL3", 0.2 )
            self.thread2.start()
            self.thread2.change_current.connect(Update_Current)
        # If Capacitor section is selected, start the CAP thread (causes GUI lock if not on its own thread) and all sensor threads
        elif( page_number == Page.CAP_ON.value ):
            self.Cap_Thread = Capacitor_Thread( ValvePins )
            self.Cap_Thread.start()
            self.thread = Water_Sensor( CAP_Flow_Pins[0], 1, "CAP", 0.1 )
            self.thread.start()
            self.thread.change_current.connect(Update_Current)
            self.thread1 = Water_Sensor( CAP_Flow_Pins[1], 1, "CAP2", 0.1 )
            self.thread1.start()
            self.thread1.change_current.connect(Update_Current)
        # Inductor section not completed (waiting for hardware to be finished to work on this section)
        elif( page_number == Page.IND_ON.value ):
            BoardFunctions.Inductor()
            self.thread = Water_Sensor( IND_Flow_Pins, 1, "IND", 0.1 )
            self.thread.start()
            self.thread.change_current.connect(Update_Current)
        # If no section is running, stop all threads and change into the Idle state by turning off shutting down pump and 
        # setting LEDs to their proper location
        else:
            self.Stop_thread()
            self.Stop_thread1()
            self.Stop_thread2()
            self.Stop_LED_thread()
            BoardFunctions.Idle_State()
            
    # Stops the thread safely (Will not stop thread otherwise, please leave in or there will be lots of issues)   
    # Need a better way to shut down threads safetly when MULTIPLE threads are running (see KCL as an issue)
    def Stop_thread(self):
        self.thread.stop()
        self.thread.quit()
        self.thread.wait()

    # Exception will probably be raised if the thread did not exist
    def Stop_thread1(self):
        try:
            self.thread1.stop()
            self.thread1.quit()
            self.thread1.wait()
        except as e:
            print("Exception Raised, %s" % (e))
            break
    
    # Exception will probably be raised if the thread did not exist
    def Stop_thread2(self):
        try:
            self.thread2.stop()
            self.thread2.quit()
            self.thread2.wait()
        except as e:
            print("Exception Raised, %s" % (e))
            break
    
    # Used when shutting down the system (LEDs are always on)
    def Stop_LED_thread(self):
        self.LED_thread.stop()
        self.LED_thread.quit()
        self.LED_thread.wait()

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

        # These all go back to either the off position (On -> Off) or the main menu (Off -> Main Menu)
        main_window.Start_button_KVL_off.clicked.connect( lambda: self.push_button_KVL_start( main_window ))
        main_window.Stop_button_KVL.clicked.connect( lambda: self.push_button_KVL_stop( main_window ))
        main_window.Start_Button_KCL.clicked.connect( lambda: self.push_button_KCL_start( main_window ))
        main_window.Stop_KCL.clicked.connect( lambda: self.push_button_KCL_stop( main_window ))
        main_window.Capacitor_Start_Button.clicked.connect( lambda: self.push_button_CAP_start( main_window ))
        main_window.Stop_Button_Capacitor.clicked.connect( lambda: self.push_button_CAP_stop( main_window ))
        main_window.Start_Button_Inductor.clicked.connect( lambda: self.push_button_IND_start( main_window ))
        main_window.Stop_Button_Inductor.clicked.connect( lambda: self.push_button_IND_stop( main_window ))

    # Back to main menu page
    def push_button_back( self, main_window ):
        main_window.stackedWidget.setCurrentIndex( Page.Main_Page.value )
        self.start( main_window )

    # KVL mode buttons
    def push_button_KVL_start( self, main_window ):
        main_window.stackedWidget.setCurrentIndex( Page.KVL_ON.value )
        self.start( main_window )
    def push_button_KVL_stop( self, main_window ):
        main_window.stackedWidget.setCurrentIndex( Page.KVL_OFF.value )
        self.start( main_window )

    # KCL mode buttons
    def push_button_KCL_start( self, main_window ):
        main_window.stackedWidget.setCurrentIndex( Page.KCL_ON.value )
        self.start( main_window )
    def push_button_KCL_stop( self, main_window ):
        main_window.stackedWidget.setCurrentIndex( Page.KCL_OFF.value )
        self.start( main_window )

    # Capacitor mode buttons
    def push_button_CAP_start( self, main_window ):
        main_window.stackedWidget.setCurrentIndex( Page.CAP_ON.value )
        self.start( main_window )
    def push_button_CAP_stop( self, main_window ):
        main_window.stackedWidget.setCurrentIndex( Page.CAP_OFF.value )
        self.start( main_window )
    
    # Inductor mode buttons
    def push_button_IND_start( self, main_window ):
        main_window.stackedWidget.setCurrentIndex( Page.IND_ON.value )
        self.start( main_window )
    def push_button_IND_stop( self, main_window ):
        main_window.stackedWidget.setCurrentIndex( Page.IND_OFF.value )
        self.start( main_window )

    # Controls top menu button (Only action for now is to terminate the program)
    def init_menubar( self, main_window ):
        main_window.actionExit.triggered.connect( self.terminate ) 

    # Turns off systems cleanly
    def terminate( self ):
        BoardFunctions.Turnoff()
        LED_Control.Turnoff()
        sys.exit()

# Enumerates the pages for ease of use
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
# code from somewhere on the interenet (Forgot to document where this is from)
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

# Starts the main function only if this is the application called
if __name__ == "__main__":
    main()
