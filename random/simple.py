import serial
import time
import pygame
import re

pygame.mixer.init()

ser = serial.Serial("/dev/tty.usbmodem101", 9600, timeout=1)
time.sleep(2)

high_bpm_music = "music/thatHome.mp3"
normal_bpm_music = "music/onMyWay.mp3"
low_bpm_music = "music/edge.mp3"

current_track = None

def play_music(file):
    global current_track
    if file != current_track:
        print(f"Changing track to: {file}")
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.load(file)
            pygame.mixer.music.play()
            current_track = file
        except Exception as e:
            print(f"Error loading music: {e}")
    else:
        print("Same track already playing, no change.")

while True:
    try:
        if ser.in_waiting > 0:
            line = ser.readline().decode("utf-8").strip()
            print(f"Received: {line}")


            match = re.search(r"Smoothed:\s*(\d+)", line)
            if match:
                bpm = int(match.group(1))
                print(f"Detected BPM: {bpm}")

                if bpm > 600:
                    play_music(high_bpm_music)
                elif bpm >= 450:
                    play_music(normal_bpm_music)
                else:
                    play_music(low_bpm_music)
            else:
                print("No valid BPM found in the serial data.")

    except Exception as e:
        print(f"Error reading from serial: {e}")

    time.sleep(0.1)
