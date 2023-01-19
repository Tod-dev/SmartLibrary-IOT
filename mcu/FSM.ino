#include <MFRC522.h>
#define SS_PIN 53
#define RST_PIN 5
MFRC522 mfrc522(SS_PIN, RST_PIN);

const int ledPins[] = {4,6,8};
const int shelfIds[] = {111,222,333};
const int totPin = 3;
int curstate;
int shelf;
int code;

int readNFC()
{
  MFRC522::MIFARE_Key key;
  for (byte i = 0; i < 6; i++)
  {
    key.keyByte[i] = 0xFF;
  }
  unsigned long timer = millis();
  while(millis()-timer<5000)
  {
    if (mfrc522.PICC_IsNewCardPresent()) return 0;
    //if ( ! mfrc522.PICC_ReadCardSerial()) return 0;
  }
  return -1;
}

void switchOffAllShelfLeds(int ledPin)
{
  digitalWrite(ledPin,LOW);
  digitalWrite(ledPin+1,LOW);
}

void switchOnAllShelfLeds(int ledPin)
{
  digitalWrite(ledPin,HIGH);
  digitalWrite(ledPin+1,HIGH);
}

void changeLedColorShelf(int ledPin)
{
  digitalWrite(ledPin,!digitalRead(ledPin));
  digitalWrite(ledPin+1,!digitalRead(ledPin+1));
}

//usato solo quando da tutti i led spenti accendo quello verde quando il libro è stato riconsegnato
void switchOnGreenShelfLed(int ledPin)
{
  digitalWrite(ledPin,HIGH);
}

int findIdArr()
{
  for (int i = 0; i < totPin; i++)
  {
    if (shelfIds[i]==shelf) return i;
  }
  return -1;
}

void sendToBridge(int intero)
{
  Serial.write(0XFF);
  Serial.write(highByte(shelf));
  Serial.write(lowByte(shelf));
  Serial.write(intero);
  Serial.write(0XFE);
}

void performInActions()
{
  int idArr = findIdArr();
  if (idArr >= 0)
  {
    int resNFC;
    switch(code)
    {
      case 1:
        changeLedColorShelf(ledPins[idArr]);
        break;
      case 2:
        switchOnAllShelfLeds(ledPins[idArr]);
        resNFC = readNFC();
        switchOffAllShelfLeds(ledPins[idArr]);
        sendToBridge(1);
        break;
      case 3:
        resNFC = readNFC();
        sendToBridge(2);
        switchOnGreenShelfLed(ledPins[idArr]);        
        break;
    }
  }
}
  
void setup()
{
  mfrc522.PCD_Init();
  Serial.begin(9600);
  for (int i = 0; i < totPin; i++)
  {
    pinMode(ledPins[i], OUTPUT);
    pinMode(ledPins[i]+1, OUTPUT);
    switchOffAllShelfLeds(ledPins[i]);
    switchOnGreenShelfLed(ledPins[i]); 
  }

  shelf = -1;
  code = -1;
  curstate = -1;
}

void loop()
{ 
  if (Serial.available()>0)
  {
    //read input 
    int val;
    val = Serial.read();
  
    //future state (default fstate = curstate)
    int fstate;
    fstate = curstate;
    if ((curstate == -1 && val == 0XFF) || val == 0XFF) fstate=0;
    if (curstate == 0) fstate = 1;
    if (curstate == 1) fstate = 2;
    if (curstate == 2) fstate = 3;
    if (curstate == 3 && val == 0XFE) fstate = 4;
    
    
    //on entry and on exit actions
    if (fstate != curstate)
    {
       if (fstate==0) {shelf = -1; code = -1;}
       if (fstate==1) shelf = val * 256;
       if (fstate==2) shelf = shelf + val;
       if (fstate==3) code = val;
       if (fstate==4) {performInActions();}
    }
    
    //transition
    curstate = fstate;
  }
}
