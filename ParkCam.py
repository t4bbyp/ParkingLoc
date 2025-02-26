import io
import queue
import traceback
import AWSIoTPythonSDK.MQTTLib as AWSIoTPyMQTT
import PySimpleGUI as sg
from PIL import Image
import pytesseract
import requests
import numpy as np
import cv2
import threading
import asyncio
import aiohttp
import re
import matplotlib.pyplot as plt

pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract'
upload_location_url = "https://parkingtori.relaxterra.com/app_api/py_update_location.php"
find_car_url = "https://parkingtori.relaxterra.com/app_api/py_search_car.php"

class Application:

    def __init__(self):
        self.myAWSIoTMQTTClient = None
        self.gui_queue = queue.Queue()

        middle_font = ('Helvetica', 14)
        context_font = ('Helvetica', 10)
        sg.theme('DarkBlue14')


        layout = [
            [sg.VPush()],
            [sg.Push(), sg.Frame('', [[sg.Column([
                        [sg.Button('Connect', key='_CONNECT_BTN_', font='Any 10', size=(10, 1))],
                    ], element_justification='center', pad=(0, 0))]], font='Any 12', relief=sg.RELIEF_FLAT), sg.Push()],
            [sg.Column([
                [sg.Frame('CAM 1', [[sg.Image(key='_ESP32/CAM_1_', size=(480, 320))]], font='Any 12')]
            ], element_justification='center', pad=(0, 0)),
            sg.Column([
                [sg.Frame('CAM 2', [[sg.Image(key='_ESP32/CAM_2_', size=(480, 320))]], font='Any 12')]
            ], element_justification='center', pad=(0, 0))],
            [sg.VPush()]
        ]


        self.window = sg.Window('ParkCam', layout)


        while True:
            event, values = self.window.Read(timeout=5)
            if event is None or event == 'Exit':
                break

            if event == '_CONNECT_BTN_':
                if self.window[event].get_text() == 'Connect':
                    self.window['_CONNECT_BTN_'].update('Disconnect')
                    self.aws_connect()

                else:
                    self.window['_CONNECT_BTN_'].update('Connect')
                    self.aws_disconnect()

            try:
                message = self.gui_queue.get_nowait()
            except queue.Empty:
                message = None

            if message is not None:
                _target_ui = message.get("Target_UI")
                _image = message.get("Image")
                
                self.window[_target_ui].update(data=_image)

        self.window.Close()

    
    def start_camera_thread(self, topic, ui_element):
            threading.Thread(target=self.mqtt_subscribe, args=(topic, ui_element), daemon=True).start()


    def aws_connect(self):
        ENDPOINT = "a286bf02lkuiob-ats.iot.eu-north-1.amazonaws.com"
        PATH_TO_CERT = "certificates/DeviceCertificate.crt"
        PATH_TO_KEY = "certificates/Private.key"
        PATH_TO_ROOT = "certificates/rootCA.pem"

        client_id = "Python_Client"

        self.myAWSIoTMQTTClient = AWSIoTPyMQTT.AWSIoTMQTTClient(client_id)
        self.myAWSIoTMQTTClient.configureEndpoint(ENDPOINT, 8883)
        self.myAWSIoTMQTTClient.configureCredentials(PATH_TO_ROOT, PATH_TO_KEY, PATH_TO_CERT)

        try:
            if self.myAWSIoTMQTTClient.connect():
                self.add_note('[MQTT] Connected')
                self.start_camera_thread("esp32/cam_1", "_ESP32/CAM_1_")
                self.start_camera_thread("esp32/cam_2", "_ESP32/CAM_2_")
            else:
                self.add_note('[MQTT] Cannot Access AWS IOT')
        except Exception as e:
            tb = traceback.format_exc()
            sg.Print(f'An error happened.  Here is the info:', e, tb)


    def aws_disconnect(self):
        if self.myAWSIoTMQTTClient is not None:
            self.myAWSIoTMQTTClient.disconnect()
            self.add_note('[MQTT] Successfully Disconnected!')

    def mqtt_subscribe(self, topic, element_key):
        def callback(client, userdata, message):
            image_data = self.byte_image_to_png(message)  # Transforma datele byte primite prin MQTT in imagine PNG
            self.gui_queue.put({"Target_UI": element_key, "Image": image_data})
            self.process_stream(image_data, element_key)
        self.myAWSIoTMQTTClient.subscribe(topic, 0, callback)


    def add_note(self, note):
        print(note)


    def byte_image_to_png(self, message):
        bytes_image = io.BytesIO(message.payload)
        picture = Image.open(bytes_image)

        im_bytes = io.BytesIO()
        picture.save(im_bytes, format="PNG")
        return im_bytes.getvalue()

    
    def popup_dialog(self, contents, title, font):
        sg.Popup(contents, title=title, keep_on_top=True, font=font)


    # Filtreaza textul obtinut din imagine cu Tesseract
    def remove_spaces(self, text):
        cleaned_text = text.replace(" ", "").replace("\n", "").replace("\r", "").strip()
        match = re.search(r'[A-Z]{2}\d{2}[A-Z]{3}', cleaned_text)
        return match.group(0) if match else None


    # Inregistreaza in baza de date locul de parcare in care masina (car_id) se afla
    def update_location(self, car_id, car_location):
        try:
            payload = {
                'car_id': car_id,
                'car_location': car_location
            }

            print(f"Payload: {payload}")
            
            response_upload_location = requests.post(upload_location_url, data=payload)
            response_upload_location.raise_for_status() 

            print(f"Raw response text: {response_upload_location.text}")

            try:
                data_upload_location = response_upload_location.json()
            except ValueError as e:
                print(f"Error parsing JSON response: {e}")
                return None

            if 'error' in data_upload_location:
                print(f"Error: {data_upload_location['error']}")
                return None
            else:
                car_id = data_upload_location.get('car_id')
                if car_id is not None:
                    return car_id
                else:
                    print("car_id not found in the response")
                    return None

        except requests.RequestException as err:
            print(f"HTTP request error: {err}")
            return None 
        except ValueError as err:
            print(f"Error parsing JSON response: {err}")
            return None


    # Cauta numarul matricol citit din imagine in baza de date
    def find_car_nr(self, car_nr):
        try:
            params = {'car_nr': car_nr}
            print(f"Car nr: " + car_nr)

            req = requests.Request('GET', find_car_url, params=params)
            prepared = req.prepare()
            print(f"Request URL: {prepared.url}")

            response_find_car = requests.get(find_car_url, params=params)
            response_find_car.raise_for_status()

            print(f"Raw response text: {response_find_car.text}")

            data_find_car = response_find_car.json()

            print(f"Response type: {type(data_find_car)}")
            print(f"Response data: {data_find_car}")

            if isinstance(data_find_car, dict):
                if data_find_car.get('error') == True:
                    print(f"Error: {data_find_car['message']}")
                    return None
                else:
                    car_id = data_find_car.get('car_details', {}).get('car_id')
                    if car_id is not None:
                        return car_id
                    else:
                        print("car_id not found in the response")
                        return None
            else:
                print("Unexpected response format, expected a dictionary")
                return None

        except requests.RequestException as err:
            print(f"HTTP request error: {err}")
            return None
        except ValueError as err:
            print(f"Error parsing JSON response: {err}")
            return None

    
    # Bucla principala de afisare a imaginilor si procesarea lor
    def process_stream(self, image_bytes, element_key):
        try:
                imgnp = np.array(bytearray(image_bytes), dtype=np.uint8)
                frame = cv2.imdecode(imgnp, -1)

                if frame is not None:
                    text = pytesseract.image_to_string(frame, config='--psm 6')
                    cleaned_text = self.remove_spaces(text)

                    print(f"\nExtracted Text: {text}\nExtracted Text without Spaces: {cleaned_text}\n")

                    if re.match(r"^[A-Z]{2}\d{2}[A-Z]{3}$", cleaned_text):
                        print("going in async")
                        threading.Thread(target=lambda: asyncio.run(self.process_plate_async(cleaned_text, element_key)), daemon=True).start()
                    
        except Exception as e:
            print(f"Error: {e}")

    # Functie asincrona de request-uri API cu numarul matricol obtinut
    # Am ales o functie asincrona pentru a nu incarca bucla principala cu numeroase procese consecutive si a optimiza programul
    async def process_plate_async(self, plate_number, element_key):
        async with aiohttp.ClientSession() as session:
                async with session.get(find_car_url, params={'car_nr': plate_number}) as response:
                    data = await response.json()
                    car_id = data.get('car_details', {}).get('car_id')

                    if car_id:
                        location = "D1" if element_key == "_ESP32/CAM_1_" else "D3"
                        await session.post(upload_location_url, data={'car_id': car_id, 'car_location': location})

    # Proceseaza imaginea cu OpenCV pentru a imbunatati calitatea citirii Tesseract (rezultatul nu este cel afisat in UI)
    def preprocess_image(self, frame):
        height, width = frame.shape[:2]

        cropped = frame[height//2:, :]

        gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
        ret, thresh4 = cv2.threshold(gray, 120, 255, cv2.THRESH_TOZERO) 

        lightness_factor = -150
        darker_image = np.clip(thresh4.astype(np.int16) + lightness_factor, 0, 255).astype(np.uint8)

        return darker_image


if __name__ == '__main__':
    Application()
