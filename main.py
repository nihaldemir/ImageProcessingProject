import cv2
from cvzone.HandTrackingModule import HandDetector
import numpy as np
import cvzone
import mediapipe as mp
from time import sleep
from pynput.keyboard import Controller,Key
import autopy
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

#Mouse için değişkenler
pTime = 0
frameReduction = 100
smoothening = 7
prev_locationX, prev_locationY = 0,0
crnt_locationX, crnt_locationY = 0,0
widthScreen, heightScreen = autopy.screen.size() #ekran boyutları değiştiğinde de width ve heighti alabilmek için

#Volume için değişkenler
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(
    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
volRange = volume.GetVolumeRange()

minVol = volRange[0]
maxVol = volRange[1]
vol = 0
volBar = 400
volPer = 0

# Görüntünün alınması
cap=cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH,1150)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT,800)
cv2.namedWindow("Image", cv2.WINDOW_NORMAL)
cv2.resizeWindow("Image", 1150, 800)

detector = HandDetector(detectionCon=0.8, maxHands=1)

#Klavye harflerinin liste haline getirlimesi
keys=[["0","1","2","3","4","5","6","7","8","9"],
      ["Q","W","E","R","T","Y","U","I","O","P"],
      ["A","S","D","F","G","H","J","K","L","EN"],
      ["Z","X","C","V","B","N","M","."," ","Del"]]

finalText = []

keyboard = Controller()

# Butonların Çizilmesi
def drawButtons(frame,buttonList):

   for button in buttonList:
       x, y = button.pos
       w, h = button.size
       cv2.rectangle(frame, button.pos, (x + w, y + h), (158, 163, 90),cv2.FILLED)  # Dıştaki mavi renkli karenin oluşturulması
       cv2.putText(frame, button.text, (x + 8, y + 50), cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255),3)  # Harflerin yazılması

   return frame

# Klavye tuşlarının oluşturulması
class Button():
    def __init__(self,pos,text,size=[80,80]):
        self.pos = pos
        self.size= size
        self.text = text

buttonList = []

# Tuşların buttonList'e eklenmesi
for i in range(len(keys)):
    for j, key in enumerate(keys[i]):
        buttonList.append(Button([100*j+50, 100*i+30],key))

while True:
    state, frame = cap.read()
    frame = cv2.flip(frame, 1)

    # Ellerin Algılanması
    hands, frame = detector.findHands(frame)
    lmList =[];
    if hands:
        hand1 = hands[0]
        lmList1 = hand1['lmList'] #Eldeki 21 noktanın listesi
        bbox1 = hand1['bbox'] # Çerçeve (x,y,w,h)
        centerPoint1 = hand1['center'] #Elin orta noktası (cx,cy)
        handType1 = hand1['type'] #Sağ el veya sol el
        finger1 = detector.fingersUp(hand1)

        lmList = lmList1

        #MOUSE
        # işaret ve orta parmakların ucunu alınması
        if len(lmList) != 0:
            x1, y1 = lmList[8][0:2]
            x2, y2 = lmList[12][0:2]

            cv2.rectangle(frame, (50, 700), (1000,450),
                      (255, 0, 255), 2)
            # Birinci parmak havadaysa ve ikincisi değilse sadece moving yani gezinme işlemi yapılır.
            if (finger1[1] == 1 and finger1[2] == 0) and (50<=x1 and x1<=1000) and (450<=y1 and y1<=700):
                # 5. convert coordinates
                x3 = np.interp(x1, (50,1000), (0, (widthScreen)))
                y3 = np.interp(y1, (450, 650), (0, (heightScreen)))
                # 6. smoothen values
                # Çok fazla titreme olduğundan smoothing işlemi gerçekleştirilir.
                crnt_locationX = prev_locationX + (x3 - prev_locationX) / smoothening
                crnt_locationY = prev_locationY + (y3 - prev_locationY) / smoothening
                # 7. move mouse
                autopy.mouse.move(crnt_locationX, crnt_locationY)
                cv2.circle(frame, (x1, y1), 15, (255, 0, 255), cv2.FILLED)

                prev_locationX, prev_locationY = crnt_locationX, crnt_locationY
            # Her iki parmakta havadaysa tıklama işlemi yapılır.
            if finger1[1] == 1 and finger1[2] == 1  and (50<=x2 and x2<=1000) and (450<=y2 and y2<=650):
                length, info, frame = detector.findDistance(lmList[8][0:2], lmList[12][0:2], frame)
                # İki parmak arası uzaklık kontrol edilir.
                if(length<=40):
                   cv2.circle(frame,(info[4],info[5]),15,(0,255,0),cv2.FILLED)
                #İki parmak havada ve yan yana ise : tıklama
                   autopy.mouse.click()

        #VOLUME:

        x4, y4 = lmList[4][0:2]
        x5, y5 = lmList[8][0:2]

        cv2.rectangle(frame, (1030, 450), (1250, 700),
                      (255, 0, 255), 2)

        #İki parmağında havada olması ve belirlenen dikdörtgenin içinde bulunması kontrol edilir.
        if (finger1[0] == 1 and finger1[1] == 1 and (1030<=x4 and x4<=1250) and (450<=y4 and y4<=700)):

             length, info, frame = detector.findDistance(lmList[4][0:2], lmList[8][0:2], frame)

             #50,150 parmaklar arasındaki uzaklığı temsil etmektedir.
             vol = np.interp(length, [50, 150], [minVol, maxVol])
             volBar = np.interp(length, [50, 150], [400, 50])
             volPer = np.interp(length, [50, 150], [0, 100])


             #Volum oranının 5'er artması sağlanır.
             smoothnessV = 5
             volPer = smoothnessV * round(volPer / smoothnessV)
             print(int(length), vol)


             volume.SetMasterVolumeLevelScalar(volPer / 100, None)

             #Volum bar'ın görselleştirilir.
             cv2.rectangle(frame, (1100, 50), (1130,400 ), (130, 72, 126), 3)
             cv2.rectangle(frame, (1100, int(volBar)), (1130, 400),(130, 72, 126), cv2.FILLED)
             cv2.putText(frame, f'{int(volPer)} %', (1060, 430), cv2.FONT_HERSHEY_COMPLEX, 1, (130, 72, 126), 3)


    drawButtons(frame,buttonList)

    # Burada butonlara tıklanması halinde oluşacak görsel değişiklikler tanımlandı
    if lmList:
        for button in buttonList:
            x, y = button.pos
            w, h = button.size
            x1, y1 = lmList[4][0:2]

            if x < lmList[4][0] < x + w and y < lmList[4][1] < y + h: # Eğer parmağımızın ucu butonların bulunduğu x ve y değerlri arasındaysa
                # Mevcut durumda üstünde bulunulan butonun rengi koyu mor olur.
                cv2.rectangle(frame, button.pos, (x + w, y + h), (130, 72, 126), cv2.FILLED)
                cv2.putText(frame, button.text, (x + 10, y + 50), cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255), 3)

                # Burada parmak hareketi tanımlandı.
                length, info, frame = detector.findDistance(lmList1[4][0:2], lmList1[8][0:2], frame)

                # Yukarıda belirlenen parmak hareketinin length'ine göre "tıklama" sonucu butonun rengi bej rengi olur.
                if length<30:
                    #Buton üstündeki harflerin klavye üstünden bastırılarak bilgisayar üstünde kullanılması
                    if(x==950 and y==330):
                        #Delete butonu için:
                        keyboard.press(Key.backspace)
                        cv2.rectangle(frame, button.pos, (x + w, y + h), (190, 188, 218), cv2.FILLED)
                        cv2.putText(frame, button.text, (x + 10, y + 50), cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255), 3)
                        sleep(0.17)

                        """
                        if len(finalText) == 0:
                           finalText=[]
                        else:
                           finalText.pop()
                        """
                    elif x == 950 and y == 230:
                        # Enter butonu için:
                        keyboard.press(Key.enter)
                        cv2.rectangle(frame, button.pos, (x + w, y + h), (190, 188, 218), cv2.FILLED)
                        cv2.putText(frame, button.text, (x + 10, y + 50), cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255), 3)
                        sleep(0.17)

                    else:
                        #Diğer butonlar için:
                        keyboard.press(button.text)
                        cv2.rectangle(frame, button.pos, (x + w, y + h), (190, 188, 218), cv2.FILLED)
                        cv2.putText(frame, button.text, (x + 10, y + 50), cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255), 3)
                        sleep(0.15)
                        finalText += button.text

    #cv2.rectangle(frame, (100,450),(700,600), (255, 255, 255), cv2.FILLED)
    #cv2.putText(frame, ''.join(finalText), (100,500), cv2.FONT_HERSHEY_PLAIN, 3, (0, 0, 0), 3)


    cv2.imshow("Image", frame)
    if cv2.waitKey(1) & 0xFF == ord("-"): break
