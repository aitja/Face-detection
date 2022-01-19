import cv2
import mediapipe as mp
import time
import PySimpleGUI as sg
from skimage.metrics import structural_similarity as ssim
import mysql.connector 
import random, os
import numpy as np
import serial

class FaceMeshDetector():

    def __init__(self, staticMode=False, maxFaces=2, refine_landmarks=False, minTrackCon=0.5, minDetectionCon=0.5):

        self.staticMode = staticMode
        self.maxFaces = maxFaces
        self.minDetectionCon = minDetectionCon
        self.minTrackCon = minTrackCon

        self.mpDraw = mp.solutions.drawing_utils
        self.mpFaceMesh = mp.solutions.face_mesh
        self.faceMesh = self.mpFaceMesh.FaceMesh(self.staticMode, self.maxFaces, refine_landmarks, self.minDetectionCon, self.minTrackCon)
        self.drawSpec = self.mpDraw.DrawingSpec(thickness=1, circle_radius=2)

    def findFaceMesh(self, img, draw=True):
        self.imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.faceMesh.process(self.imgRGB)
        faces = []
        if self.results.multi_face_landmarks:
            for faceLms in self.results.multi_face_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, faceLms, self.mpFaceMesh.FACEMESH_TESSELATION,
                                           self.drawSpec, self.drawSpec)
                face = []
                for id,lm in enumerate(faceLms.landmark):
                    #print(lm)
                    ih, iw, ic = img.shape
                    x,y = int(lm.x*iw), int(lm.y*ih)
                    #cv2.putText(img, str(id), (x, y), cv2.FONT_HERSHEY_PLAIN,
                     #           0.7, (0, 255, 0), 1)

                    #print(id,x,y)
                    face.append([x,y])
                faces.append(face)
        return img, faces
    
    def dbconnect(self):
        #Create the connection object   
        myconn = mysql.connector.connect(host = "localhost", user = "root",passwd = "",  database = "facedetection")  
        return myconn

    def dbAddUser(self, user):
        myconn = self.dbconnect()
        cur = myconn.cursor()

        insert_stmt = ("INSERT INTO users( name )" "VALUES (%s)")
        data = (user,)
        try:
            # Executing the SQL command
            cur.execute(insert_stmt, data)

            # Commit your changes in the database
            myconn.commit()
            return cur.lastrowid 

        except:
            # Rolling back in case of error
            myconn.rollback()
        finally:
            cur.close()
            myconn.close()
            
    def dbAddFaces(self, user_id, image):
        myconn = self.dbconnect()
        cur = myconn.cursor()

        insert_stmt = ("INSERT INTO faces( user_id, image )" "VALUES (%s, %s)")
        data = (user_id, image)
        try:
            # Executing the SQL command
            cur.execute(insert_stmt, data)

            # Commit your changes in the database
            myconn.commit()

        except:
            # Rolling back in case of error
            myconn.rollback()
        finally:
            cur.close()
            myconn.close()
        
            
    def dbdelete(self):
        myconn = self.dbconnect()
        cur = myconn.cursor()
    
        delete_stmt = ("DELETE FROM users")
        delete_imgs = ("DELETE FROM faces")
        try:
           # Executing the SQL command
           cur.execute(delete_imgs)
           cur.execute(delete_stmt)

           # Commit your changes in the database
           myconn.commit()

        except:
           # Rolling back in case of error
           myconn.rollback()
        finally:
            cur.close()
            myconn.close()
        
    def dbselect(self):
        myconn = self.dbconnect()
        cur = myconn.cursor()
    
        select = ("SELECT user_id, image FROM faces")
        try:
           # Executing the SQL command
           cur.execute(select)
           return cur.fetchall() 

        except:
           # Rolling back in case of error
           return False
        finally:
            cur.close()
            myconn.close()

    def dbselectuser(self, user_id):
        myconn = self.dbconnect()
        cur = myconn.cursor()
        print(user_id)
        select = ("SELECT name FROM users WHERE id = %s")
        try:
            # Executing the SQL command
            cur.execute(select, (user_id,))
            return cur.fetchone()

        except:
            # Rolling back in case of error
            return False
        finally:
            cur.close()
            myconn.close()

    def mse(self, imageA, imageB):
        err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
        err /= float(imageA.shape[0] * imageA.shape[1])
        return err

    def compare_images(self, imageA, imageB):
        path = 'C:/Users/dell/OneDrive/Bureau/facereco/faces'
        s = 0
        imageA = cv2.imread(os.path.join(path, imageA))
        imageA = cv2.cvtColor(imageA, cv2.COLOR_BGR2GRAY)
        imageB = cv2.cvtColor(imageB, cv2.COLOR_BGR2GRAY)
        m = self.mse(imageA, imageB)
        s = ssim(imageA, imageB)

        return s

    def arduino_code(self, check):
        m = 1
        ard = serial.Serial('com5', 9600)
        if check:
            time.sleep(2)
            var = 'a'
            c = var.encode()
            print("Face recognition complete..it is matching with database...welcome..sir..Door is openning for 5 seconds")
            ard.write(c)
        else:
            time.sleep(2)
            var = 'b'
            print(var)
            c = var.encode()
            print("Face recognition complete..it is not matching with database...")
            ard.write(c)
        time.sleep(4)
    
def main():
    path = 'C:/Users/dell/OneDrive/Bureau/facereco/faces'
    cap = cv2.VideoCapture(0)

    pTime = 0
    detector = FaceMeshDetector(maxFaces=2)
    ssim_accuracy = 0.50

    # init Windows Manager
    sg.theme("DarkBlue")

    # def webcam col
    colwebcam1_layout = [[sg.Text("Camera View", size=(20, 1), justification="center")],
                        [sg.Image(filename="", key="cam1")]]
    colwebcam1 = sg.Column(colwebcam1_layout, element_justification='center')
    file1 = os.path.join('C:/Users/dell/OneDrive/Bureau/facereco/', 'ensias.png')
    file2 = os.path.join('C:/Users/dell/OneDrive/Bureau/facereco/', 'bioui.png')
    print(file1)
    buttons = [
                  [sg.Image(file1, size=(200, 200), key="img1"), sg.Image(file2, size=(200, 200), key="img2")],
                  [ sg.Button('STREAMING', size=(35, 1), font='Helvetica 14', button_color=('white', 'green'), key='-b-') ],
                  [ sg.InputText(size=(50, 4), key='-input-') ],
                  [
                    sg.Button('STREAM CAMERA', size=(17, 1), font='Helvetica 14', button_color=('white', 'red')), 
                    sg.Button('DETECT FACES', size=(17, 1), font='Helvetica 14', button_color=('white', 'red')),
                  ],
                  [ sg.Button('ADD USER', size=(10, 1), font='Helvetica 14', button_color=('white', 'red')) ],
                  [ sg.Text('Captured Faces', font='Helvetica 14') ],
                  [sg.Multiline(default_text='', size=(50, 5), key='-users-', disabled=True) ],
                  [ sg.Button('DELETE ALL', size=(10, 1), font='Helvetica 14', button_color=('white', 'red')) ]
              ]
    colbuttons = sg.Column(buttons, element_justification='center')
    
    colslayout = [colwebcam1, colbuttons]

    rowfooter = []
    layout = [colslayout, rowfooter]

    window    = sg.Window("FACE DETECTION", layout, 
                    no_titlebar=False, alpha_channel=1, grab_anywhere=False, 
                    return_keyboard_events=True, location=(100, 100))
    
    detection = True
    
    while True:
        success, img = cap.read()
#         start_time = time.time()
        event, values = window.read(timeout=20)

        if event == sg.WIN_CLOSED:
            break
        
        if event == 'DETECT FACES':
                
            result = detector.dbselect()

            if result:
                
                for x in result:

                    if detector.compare_images(imageA=x[1], imageB=img) > ssim_accuracy:

                        img, faces = detector.findFaceMesh(img)
                        user_id = x[0]
                        user_name = detector.dbselectuser(user_id)
                        print(user_name)
                        if len(faces) != 0:
                            detection = False
                            img = np.full((480, 640), 255)
                            # this is faster, shorter and needs less includes
                            imgbytes = cv2.imencode('.png', img)[1].tobytes()
                            window["-b-"].update(user_name[0].upper() + ' FACE DETECTED')
                            window['cam1'].update(data=imgbytes)
                            detector.arduino_code(1)
                            break
                    else:
                        window["-b-"].update('UNKNOWN USER')
                        detector.arduino_code(0)
            else:
                window["-b-"].update('UNKNOWN USER')
                detector.arduino_code(0)
            
        if event == 'STREAM CAMERA':
            detection = True
            window["-b-"].update('STREAMING')
            success, img = cap.read()
            
        if event == 'ADD USER':
            
            if len(values["-input-"]) != 0:
                
                user_id =  detector.dbAddUser(values['-input-'])
                
                if user_id:
                    window["-users-"].update(values['-users-'] +  values['-input-'] + '\n')
                    window["-input-"].update('')
                    for x in range(5):
                        img_name = str(random.randrange(111111, 999999)) +'.png'
                        cv2.imwrite(os.path.join(path , img_name), img)
                        detector.dbAddFaces(user_id, img_name)
                        window["-b-"].update(str(x+1)+' SAMPLES UPDATED')
                        
                        
            

        if event == 'DELETE ALL':
            detector.dbdelete()
            window["-users-"].update('')
        if detection:    
            cTime = time.time()
            fps = 1 / (cTime - pTime)
            pTime = cTime
            cv2.putText(img, f'FPS: {int(fps)}', (20, 70), cv2.FONT_HERSHEY_PLAIN,
                    3, (0, 255, 0), 3)
    #         cv2.imshow("Image", img)
    #         cv2.waitKey(1)
            imgbytes = cv2.imencode(".png", img)[1].tobytes()
            window["cam1"].update(data=imgbytes)


if __name__ == "__main__":
    main()
    