from Raspi_MotorHAT import Raspi_MotorHAT, Raspi_DCMotor
from Raspi_PWM_Servo_Driver import PWM
import RPi.GPIO as GPIO
import time
import threading

class ConveyerController:
    def __init__(self, addr=0x6f, motor_id=2, sensor_pin=17):

        self.mh = Raspi_MotorHAT(addr=addr)
        self.motor = self.mh.getMotor(motor_id)
        self.motor_speed=255
        self.motor.setSpeed(self.motor_speed)
        
        self.servo = PWM(addr)
        self.servo.setPWMFreq(60)
        
        

        self.sensor_pin = sensor_pin
        self.stop_event = threading.Event()
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.sensor_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.sensor_pin, GPIO.FALLING, 
            callback=self._object_detected, bouncetime=200)

    def _object_detected(self, channel):
        self.stop_event.set()
        print("detect")


    def move_motor_async(self, duration, direction):
        def _worker():
           
            self.motor.setSpeed(self.motor_speed)
            self.motor.run(direction)
            
            
            start_time = time.time()
            
            while (time.time() - start_time < duration) and not self.stop_event.is_set():
                time.sleep(0.1) 

            self.motor.run(Raspi_MotorHAT.RELEASE)
            print("모터 정지 완료")

        t = threading.Thread(target=_worker)
        t.start()

    def belt_run(self):
        
        self.stop_event.clear()
        
      
        self.move_motor_async(5, Raspi_MotorHAT.FORWARD)

    def belt_stop(self):
        self.stop_event.set()

    def servo_push(self):
        self.servo.setPWM(1, 0, 600)
        self.servo.setPWM(0, 0, 600)

    def servo_pull(self):
        self.servo.setPWM(1, 0, 100)
        self.servo.setPWM(0, 0, 100)

    def cleanup(self):
        self.motor.run(Raspi_MotorHAT.RELEASE)
        GPIO.cleanup()
