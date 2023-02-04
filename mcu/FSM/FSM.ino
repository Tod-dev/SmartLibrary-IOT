#include <MFRC522.h>
#include <SPI.h>
#define SDA_PIN 10
#define RST_PIN 9
#define BUZ_PIN 14
#define LENGTH_UID 4
#define NFC_READ_TIMEOUT 10000

MFRC522 nfcReader(SDA_PIN, RST_PIN);
const int ledPins[] = {3,5,7};
const int shelfIds[] = {1,2,3};
const int totLeds = 3;
int curstate;
int shelf;
int code;
int s;
bool setupComplete;
byte byteNfcUID[4]; 

int readNFC()
{
  MFRC522::MIFARE_Key key;
  for (byte i = 0; i < 6; i++)
  {
    key.keyByte[i] = 0xFF;
  }
  
  unsigned long timer = millis();
  while(millis()-timer < NFC_READ_TIMEOUT)
  {
    if (nfcReader.PICC_IsNewCardPresent())
    {
      if (nfcReader.PICC_ReadCardSerial())
      {
        //rfid.uid.size
        //byte *byteUID = nfcReader.uid.uidByte;
        for (int i=0; i<LENGTH_UID; i++)
        {
          byteNfcUID[i]=nfcReader.uid.uidByte[i];
        }
        //unsigned long hexUID;
        //hexUID = byteUID[0] << 24;
        //hexUID += byteUID[1] << 16;
        //hexUID += byteUID[2] << 8;
        //hexUID += byteUID[3];
        //long int intUID = (int)hexUID;
        nfcReader.PICC_HaltA(); //halt PICC
        nfcReader.PCD_StopCrypto1(); //stop encryption on PCD
        //return intUID;
        return 1;
      }
    }
  }
  //posso eventualmente settare a zero tutti gli elementi di byteNfcUID
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
  digitalWrite(ledPin+1,LOW);
}

int findIdArr(int shl)
{
  for (int i = 0; i < totLeds; i++)
  {
    if (shelfIds[i]==shl) return i;
  }
  return -1;
}

void buzzerError(int inter)
{
  unsigned long timer = millis();
  
  while(millis()-timer < inter)
  {
    int musicalVal = random(200, 1000);
    tone(BUZ_PIN, musicalVal);
    unsigned long delayTimer = millis();
    while(millis()-delayTimer < 200){}
  }
  noTone(BUZ_PIN);
}

void sendToBridge(int intero, int shl, byte *nfcUID=-1)
{
  
  Serial.write(0XFF);
  Serial.write(highByte(shl));
  Serial.write(lowByte(shl));
  if (nfcUID>0)
  {
    for (int i=0; i<LENGTH_UID; i++)
    {
      Serial.write(nfcUID[i]);
    }
  }
  else
  {
    for (int i=0; i<LENGTH_UID; i++)
    {
      Serial.write(0);
    }
  }
  Serial.write(intero);
  Serial.write(0XFE);
}

void performInActions()
{
  int idArr = findIdArr(shelf);
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
        do
        {
          resNFC = readNFC();
          if (resNFC < 0)
          {
            buzzerError(2000);
          }
        }
        while(resNFC < 0);  
        switchOffAllShelfLeds(ledPins[idArr]);
        sendToBridge(1, shelf, byteNfcUID);
        break;
      case 3:
        switchOnAllShelfLeds(ledPins[idArr]);
        do
        {
          resNFC = readNFC();
          if (resNFC < 0)
          {
            buzzerError(2000);
          }
        }
        while(resNFC < 0);
        sendToBridge(2, shelf, byteNfcUID);
        switchOnGreenShelfLed(ledPins[idArr]);        
        break;
    }
  }
}
  
void setup()
{
  Serial.begin(9600);
  SPI.begin();
  nfcReader.PCD_Init();
  
  pinMode(BUZ_PIN,OUTPUT);
  for (int i = 0; i < totLeds; i++)
  {
    pinMode(ledPins[i], OUTPUT);
    pinMode(ledPins[i]+1, OUTPUT);
    switchOffAllShelfLeds(ledPins[i]);
  }
  
  shelf = -1;
  code = -1;
  curstate = -1;
  s = 0;
  setupComplete = false;

  sendToBridge(3,0);
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
    else if (curstate >= 0) fstate = curstate + 1;    
    
    //on entry and on exit actions
    if ((setupComplete) && (fstate != curstate))
    {
       if (fstate==0) {shelf = -1; code = -1;}
       else if (fstate==1) shelf = val * 256;
       else if (fstate==2) shelf = shelf + val;
       else if (fstate==3) code = val;
       else if (fstate==4 && val == 0XFE) {performInActions();}
    }

    if ((!setupComplete) && (fstate != curstate))
    {
      if (val == 0XFE) {setupComplete = !setupComplete;}
      else if (fstate>0)
      {
        switch(val)
        {
          case 1:
            switchOnGreenShelfLed(ledPins[s]);
            s = s + 1;
            break;
          case 2:
            switchOnGreenShelfLed(ledPins[s]);
            changeLedColorShelf(ledPins[s]);
            s = s + 1;
            break;
          case 3:
            //switchOffAllShelfLeds(ledPins[s]); in realtà non fai nulla perchè è già così di default
            s = s + 1;
            break;
        }
      }
    }
    
    //transition
    curstate = fstate;
  }
}
