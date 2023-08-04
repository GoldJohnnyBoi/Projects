// This is code that is used on the Arduino Portenta. Its purpose is to rotate a stepper mover using a driver given inputs from reflective sensors. The sensors shoot out a laser that if reflected, for the duration that the reflection continues, will change
// its input signal. There is a sensor that will always home the motor back home in case of a random outage. There is a sensor that will give the motor the go-ahead to rotate when activated. 

#include <math.h>
#include "Arduino_MachineControl.h"     //Important Libraries
#include "Wire.h"
#include <cmath>

using namespace machinecontrol;      //Important, required for sensors. 
uint16_t readings = 0;
uint16_t HS_readings = 0;

long delay_Micros = 1600; // Set value
long currentMicros = 0; 
long previousMicros = 0;   //Controlling motor speed
int global_position = 0;
int BR = 9600;    // Baudrate
int speed_var = 10000;     // Controlling motor speed
int DIR_PIN = 0;
int MOTOR_PIN = 1;
int HOMING_SENSOR = 2;      // Sensors 
int DOOR_SENSOR = 3;
int ENABLE_DRIVER_PIN = 4;
int count  = 0;
int interval = 0;


void stepper_move(int set_position, int speed_var)    // This function moves the motor.
{
  int rotation_value=0;//The var for the degree difference
  int i = 0;//count var
  int del = 3;
  int new_delay;
  int c = 3000;

  //Checking if the wheel needs to go CW or CCW. This will also set the global_position value to keep track of the position.
  if(set_position>=global_position){
    rotation_value = set_position - global_position;
    global_position = set_position;
    digital_outputs.set(DIR_PIN,HIGH);//CCW
  }
  else{
    rotation_value =  global_position - set_position;
    global_position = set_position;
    digital_outputs.set(DIR_PIN,LOW);//CW
  }
  Serial.println("Direction Set");
  rotation_value = ceil(rotation_value*4.444);//conversion from 360 degrees to pulses (400).
  Serial.println("Rotation Value Set");
  //This loop controls the pulses and goes until it has hit the desired rotation_value.
  while(i <= rotation_value){
    
    if (i <= 200) {     //This logic will smooth out the starts and stops. 
      c = c - 10;
	    new_delay = c;
      Serial.println("Speeding...");
  
    } else if (i >= (rotation_value - 200)) {
      c = c + 10;
	    new_delay = c;
      Serial.println("Slowing...");
  
    } else {
	    new_delay = c;
      Serial.println("Max Speed");
    }

    currentMicros = micros();   //Prevents motor from breaking
    //The micros stuff makes sure we arent getting ahead of ourselves.
    if(currentMicros - previousMicros >= delay_Micros){

      i++;//count var

      previousMicros = currentMicros;

      digital_outputs.set(MOTOR_PIN,HIGH);

      delayMicroseconds(new_delay);      //actually makes the motor move through pulses

      digital_outputs.set(MOTOR_PIN,LOW);

      delayMicroseconds(new_delay);
      
    }
  }
}


void homing_sequence() {   //Will put the motor in the home position
  HS_readings = read_homing_input();
  digital_outputs.set(DIR_PIN,HIGH); //Direction pin is 0 / Low is CW
  while(HS_readings == HIGH) {
    digital_outputs.set(MOTOR_PIN,HIGH);  //Motor pins are 1
    delayMicroseconds(5000);
    digital_outputs.set(MOTOR_PIN,LOW);

    HS_readings = read_homing_input();
  
  }
}

int read_homing_input() {
  HS_readings = digital_inputs.read(DIN_READ_CH_PIN_02); //Homing sensor pin is 2   
  return HS_readings;
}

int read_doorcheck_input() {
  readings = digital_inputs.read(DIN_READ_CH_PIN_03); // Door sensor is pin 3
  return readings;
}





void execution() {
  int doorsense = read_doorcheck_input();
  if (doorsense == HIGH) {

    stepper_move(270, speed_var);  //deg, speed

    delay(1000);
   
    stepper_move(0, speed_var);

    delay(1000);

  }
}


void setup() {
  // put your setup code here, to run once:
  Serial.begin(BR); //                                                       <----------

  while(!Serial);
  Wire.begin();

  if (!digital_inputs.init()) {                                             // Initialization Code for startup
    Serial.println("Digital input GPIO expander initializations failed!!");
  }

  digital_outputs.set(ENABLE_DRIVER_PIN, HIGH); //                           <-----------                 

  Serial.println("Homing...");
  homing_sequence();
  Serial.println("Homing Finished");

}

void loop() {
  // put your main code here, to run repeatedly:
  execution();
}



