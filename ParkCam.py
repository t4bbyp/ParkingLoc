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
                        [sg.Text('Client Id:', font='Any 12')],
                        [sg.Input('Python_Client', key='_CLIENTID_IN_', size=(19, 1), font='Any 10'),
                        sg.Button('Connect', key='_CONNECT_BTN_', font='Any 10')],
                    ], size=(235, 100), pad=(0, 0))]], font='Any 12', relief=sg.RELIEF_FLAT), sg.Push()],
            [sg.Column([
                [sg.Frame('CAM 0', [[sg.Image(key='_ESP32/CAM_0_', size=(480, 320))]], font='Any 12')]
            ], element_justification='center', pad=(0, 0)),
            sg.Column([
                [sg.Frame('CAM 1', [[sg.Image(key='_ESP32/CAM_1_', size=(480, 320))]], font='Any 12')]
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

                    if len(self.window['_CLIENTID_IN_'].get()) == 0:
                        self.popup_dialog('Client Id is empty', 'Error', context_font)
                    else:
                        self.window['_CONNECT_BTN_'].update('Disconnect')
                        self.aws_connect(self.window['_CLIENTID_IN_'].get())

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
                self.process_stream(_image, _target_ui)

        self.window.Close()

    def aws_connect(self, client_id):
        ENDPOINT = "a286bf02lkuiob-ats.iot.eu-north-1.amazonaws.com"
        PATH_TO_CERT = "certificates/DeviceCertificate.crt"
        PATH_TO_KEY = "certificates/Private.key"
        PATH_TO_ROOT = "certificates/rootCA.pem"

        self.myAWSIoTMQTTClient = AWSIoTPyMQTT.AWSIoTMQTTClient(client_id)
        self.myAWSIoTMQTTClient.configureEndpoint(ENDPOINT, 8883)
        self.myAWSIoTMQTTClient.configureCredentials(PATH_TO_ROOT, PATH_TO_KEY, PATH_TO_CERT)

        try:
            if self.myAWSIoTMQTTClient.connect():
                self.add_note('[MQTT] Connected')
                for i in range(2):
                    self.mqtt_subscribe('esp32/cam_{}'.format(i))

            else:
                self.add_note('[MQTT] Cannot Access AWS IOT')
        except Exception as e:
            tb = traceback.format_exc()
            sg.Print(f'An error happened.  Here is the info:', e, tb)

    def aws_disconnect(self):
        if self.myAWSIoTMQTTClient is not None:
            self.myAWSIoTMQTTClient.disconnect()
            self.add_note('[MQTT] Successfully Disconnected!')

    def mqtt_subscribe(self, topic):
        if self.myAWSIoTMQTTClient.subscribe(topic, 0, lambda client, userdata, message: {

            self.gui_queue.put({"Target_UI": "_{}_".format(str(message.topic).upper()),
                                "Image": self.byte_image_to_png(message)})
        }):
            self.add_note('[MQTT] Topic: {}\n-> Subscribed'.format(topic))
        else:
            self.add_note('[MQTT] Cannot subscribe\nthis Topic: {}'.format(topic))

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


    def remove_spaces(self, text):
        cleaned_text = text.replace(" ", "").replace("\n", "").replace("\r", "").strip()
        return cleaned_text


    def update_location(self, car_id, car_location):
        try:
            payload = {
                'car_id': car_id,
                'car_location': car_location
            }

            print(f"Payload: {payload}")
            
            response_upload_location = requests.post(upload_location_url, data=payload)
            response_upload_location.raise_for_status()  # Raise an exception for HTTP errors
            
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

    def process_stream(self, image_bytes, element_key):
        try:
                imgnp = np.array(bytearray(image_bytes), dtype=np.uint8)
                frame = cv2.imdecode(imgnp, -1)

                if frame is not None:
                    frame = cv2.resize(frame, (480, 320))
                    text = pytesseract.image_to_string(frame, config='--psm 6')
                    text_without_spaces = self.remove_spaces(text)

                    print(f"\nExtracted Text: {text}\nExtracted Text without Spaces: {text_without_spaces}\n")

                    car_id = self.find_car_nr(text_without_spaces)
                    if car_id:
                        self.update_location(car_id, "D5") 

                    imgbytes = cv2.imencode('.png', frame)[1].tobytes()
                    self.window[element_key].update(data=imgbytes)
                    

        except Exception as e:
            print(f"An error occurred: {e}")



if __name__ == '__main__':
    Application()
