import io
import os
import time

from picamera import PiCamera
from gpiozero import Button

from RPLCD import CharLCD
import RPi.GPIO as GPIO

# connect to DynamoDB
import datetime
import boto3
import json

# ----------------------------------------------------------------------------------
path = '/home/pi/Desktop/python/car.jpg'
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/pi/Downloads/iot_key.json"


# ----------------------------------------------------------------------------------
class CheckPermission(object):
    def __init__(self, Table_Name='CarPermission'):
        self.Table_Name = Table_Name
        self.db = boto3.resource('dynamodb')
        self.table = self.db.Table(Table_Name)
        self.client = boto3.client('dynamodb')

    def get(self, carNumber):
        response = self.table.get_item(
            Key={
                "CarNumber": carNumber
            }
        )

        return response


# ----------------------------------------------------------------------------------
class InsertLog(object):
    def __init__(self, Table_Name='CarLogInfo'):
        self.Table_Name = Table_Name
        self.db = boto3.resource('dynamodb')
        self.table = self.db.Table(Table_Name)
        self.client = boto3.client('dynamodb')

    def recordIn(self, carNumber, inDate):
        self.table.put_item(
            Item={
                "CarNumber": carNumber,
                "Date": inDate
            }
        )


# ----------------------------------------------------------------------------------
def connectDB(carNum):
    # 입출입 시간
    now = datetime.datetime.now()
    tm = "{}-{}-{}\n{}:{}:{}".format(now.year, now.month, now.day, now.hour, now.minute, now.second)

    checkPer = CheckPermission()
    chk = checkPer.get(carNum)
    chk = json.dumps(chk, indent=4)

    if 'Item' in chk:
        inoutLog = InsertLog()
        inoutLog.recordIn(carNum, tm)
        return "1"
    else:
        return "0"


# ----------------------------------------------------------------------------------
def detect_text(path):
    from google.cloud import vision
    client = vision.ImageAnnotatorClient()

    with io.open(path, 'rb') as image_file:
        content = image_file.read()

    image = vision.types.Image(content=content)

    response = client.text_detection(image=image)
    texts = response.text_annotations
    # print(texts)

    text_list = []
    for text in texts:
        txt = str(text.description).rstrip().replace(" ", "")
        text_list.append(txt)

    return text_list


# ----------------------------------------------------------------------------------
camera = PiCamera()
camera.resolution = (1920, 1080)
camera.framerate = 15


def take_picture():
    button = Button(17)

    camera.start_preview()
    button.wait_for_press()
    # time.sleep(3)
    camera.capture(path)
    camera.stop_preview()


# ----------------------------------------------------------------------------------
lcd = CharLCD(cols=16, rows=2, pin_rs=37, pin_e=35, pins_data=[40, 38, 36, 32, 33, 31, 29, 23],
              numbering_mode=GPIO.BOARD)


def led_display(flag, name):
    name2 = '';
    if len(name) == 7:
        name2 = name[3:]
    else:
        name2 = name[4:]
    # name = name[4:-1]
    if flag == "1":
        lcd.cursor_pos = (0, 0)
        lcd.write_string("Welcom " + name2)

        lcd.cursor_pos = (1, 0)
        lcd.write_string("Plase come In!!!")
    else:
        lcd.cursor_pos = (0, 0)
        lcd.write_string("!STOP!STOP!STOP!")

        lcd.cursor_pos = (1, 0)
        lcd.write_string("Do not Access!!!")
    # ----------------------------------------------------------------------------------


GPIO_TRIGGER = 12
GPIO_ECHO = 18
GPIO.setmode(GPIO.BOARD)
GPIO.setup(GPIO_TRIGGER, GPIO.OUT)
GPIO.setup(GPIO_ECHO, GPIO.IN)


def check_distance():
    GPIO.output(GPIO_TRIGGER, True)

    time.sleep(0.00001)
    GPIO.output(GPIO_TRIGGER, False)

    StartTime = time.time()
    StopTime = time.time()

    while GPIO.input(GPIO_ECHO) == 0:
        StartTime = time.time()

    while GPIO.input(GPIO_ECHO) == 1:
        StopTime = time.time()

    TimeElapsed = StopTime - StartTime

    distance = (TimeElapsed * 17000)
    time.sleep(1)
    return round(distance, 2)


# ----------------------------------------------------------------------------------
green_led = 8
red_led = 10
GPIO.setup(green_led, GPIO.OUT)
GPIO.setup(red_led, GPIO.OUT)
# ----------------------------------------------------------------------------------
if __name__ == '__main__':
    try:
        while True:
            dist = check_distance()

            print("Distance = %.1f cm" % dist)
            # GPIO.cleanup()
            if 30 < dist and dist < 50:
                take_picture()
                text_list = detect_text(path)

                print(text_list)
                txt = text_list[0].split('\n')
                for i in txt:
                    if len(i) == 7 or len(i) == 8:
                        txt = i
                        break
                print(txt)
                if txt is '12314568':
                    txt = '123가4568'
                elif txt is '6354128':
                    txt = '63두4128'
                chk = connectDB(text_list[0])
                # chk
                led_display(chk, text_list[0])
    except KeyboardInterrupt:
        print("stopped by user")
        GPIO.cleanup()

# pip install boto3
# pip instqall awscli
# aws configure

# client ID
# secretKey

# client PW
# secretKey

# region
# us-east-1

# json