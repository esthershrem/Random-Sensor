import serial
import time
import pygame
import re
import asyncio
import websockets
import json
import threading

pygame.mixer.init()

ser = serial.Serial("/dev/tty.usbmodem101", 9600, timeout=1)
time.sleep(2)

high_bpm_music = "music/thatHome.mp3"
normal_bpm_music = "music/onMyWay.mp3"
low_bpm_music = "music/edge.mp3"

current_track = None
previous_bpm = None
bpm_tolerance = 10

bpm_queue = asyncio.Queue()

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

async def serial_reader():
    while True:
        try:
            if ser.in_waiting > 0:
                line = await asyncio.to_thread(ser.readline)
                line = line.decode("utf-8").strip()
                print(f"Received: {line}")

                match = re.search(r"Smoothed:\s*(\d+)", line)
                if match:
                    bpm = int(match.group(1))
                    print(f"Detected BPM: {bpm}")

                    if bpm > 600:
                        play_music(high_bpm_music)
                        bpm_queue.put_nowait(bpm)
                    elif bpm >= 450:
                        play_music(normal_bpm_music)
                        bpm_queue.put_nowait(bpm)
                    else:
                        play_music(low_bpm_music)
                        bpm_queue.put_nowait(bpm)
                else:
                    print("No valid BPM found in the serial data.")

        except Exception as e:
            print(f"Error reading from serial: {e}")

        await asyncio.sleep(0.2)

async def send_updates(websocket, path):
    global previous_bpm
    while True:
        bpm = await bpm_queue.get()
        song = get_song(bpm)
        data = json.dumps({"bpm": bpm, "song": song})
        
        print(f"Sending data to WebSocket: {data}")  # Log the data before sending

        await websocket.send(data)
        threading.Thread(target=play_music, args=(f"music/{song}.mp3",)).start()

def get_song(bpm):
    if bpm > 600:
        return "high"
    elif bpm >= 450:
        return "normal"
    else:
        return "low"

async def main():
    asyncio.create_task(serial_reader())

    start_server = await websockets.serve(send_updates, "localhost", 6790)
    print("WebSocket server started")
    await start_server.wait_closed()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    asyncio.run(main())