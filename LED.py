#!/usr/bin/env python3
# Author: Tony DiCola (tony@tonydicola.com)
# Modified By: Alex Lam

import time
from neopixel import *
import csv

# LED strip configuration:
LED_COUNT      = 177      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 200     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53


# Define functions which animate LEDs in various ways.
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
        
def kCLTop(strip, freq2, wait_ms=50):
    for i in range(14): #0-stripSize
        strip.setPixelColor(i+44, Color( 0,   127, 127)) #turn on those LEDs
        strip.show()
        time.sleep(wait_ms/(1000.0*freq2)) #delay
        strip.setPixelColor(i+44, 4) #turn off the start
        strip.show()

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

def Idle_LED(strip, wait_ms=20, iterations=5):
    """Draw rainbow that uniformly distributes itself across all pixels."""
    for j in range(256*iterations):
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, wheel((int(i * 256 / strip.numPixels()) + j) & 255))
        strip.show()
        time.sleep(wait_ms/1000.0)

# Main program logic follows:
if __name__ == '__main__':

    # Create NeoPixel object with appropriate configuration.

    # Intialize the library (must be called once before other functions).
    strip.begin()
    Type = "Idle"
    gal = 0

    while True:
        with open('FlowInfo.csv','r') as Info:
            reader = csv.Dictreader(Info)
            length = len(reader)
            try:
                gal1 = reader['gal1'][len - 1]
                gal2 = reader['gal2'][len - 1]
                gal3 = reader['gal3'][len - 1]
                Type = reader['Type'][len - 1]
            except:
                gal = 0
                Type = "Idle"
            if Type == "Idle":
                Idle_LED(strip)
            elif Type == "KVL":
                kVL(strip, gal)
            elif Type == "KCL":
                kCLTop(strip, gal1)
                kCLMid(strip, gal2, gal3)
                kCLLR(strip, gal2, gal3)
            elif Type == "CAP":
                capacitorLEDs(strip, gal1, gal2)
            elif Type == "IND":
                inductorLEDs(strip, gal1)
            else:
                print("Wrong type was entered\n")
            