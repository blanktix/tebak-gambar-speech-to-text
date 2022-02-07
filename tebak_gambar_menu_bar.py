from math import pi
from PyQt5.QtMultimedia import QSound
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys
import speech_recognition as sr
import pandas
import random
# from hitung_jari import HitungJari


class LoadImage(QObject):
    # Class for loading image to application
    imageData=pyqtSignal(dict)
    round=0
    image_round=pyqtSignal(str)
    imageList=list()
    max_round=pyqtSignal(bool)
    @pyqtSlot()
    def game(self):
        data = pandas.read_csv('./soal.csv')
        self.image_round.emit("Gambar ke: "+str(self.round+1)+"/"+str(len(data)))
        index=random.randint(0, len(data)-1)
        while data.iloc[index]["NAMA_FILE_GAMBAR"] in self.imageList:
            index=random.randint(0, len(data)-1)
        self.imageData.emit({
            "NAMA_FILE_GAMBAR": data.iloc[index]["NAMA_FILE_GAMBAR"],
            "TEMA": data.iloc[index]["TEMA"],
            "JAWABAN":data.iloc[index]["JAWABAN"]
        })
        self.imageList.append(data.iloc[index]["NAMA_FILE_GAMBAR"])
        self.round+=1
        print("Executed")
        if len(data) == len(self.imageList):
            self.max_round.emit(False)
            self.imageList=list()
            self.round=0
class VoiceWorker(QObject):
    # Class for handling speech to text
    textChanged = pyqtSignal(str)
    statusProgram = pyqtSignal(str)
    enabled = pyqtSignal(bool)

    @pyqtSlot()
    def task(self):
        self.enabled.emit(False)
        r = sr.Recognizer()
        m = sr.Microphone()
        print("Katakan sesuatu!")
        self.statusProgram.emit("Sedang merekam")
        with m as source:
            audio = r.listen(source)
            try:
                self.statusProgram.emit("Jawaban kamu adalah: ")
                self.textChanged.emit("'{}'".format(r.recognize_google(audio, language="id-ID")))
            except sr.UnknownValueError:
                self.textChanged.emit(" {{GAGAL MEREKAM}}")
            except sr.RequestError:
                self.textChanged.emit(" {{HARUS TERSAMBUNG KE INTERNET}}")
        self.enabled.emit(True)
            


class MainGUI(QMainWindow):
    def __init__(self, parent= None)-> None:
        super(MainGUI, self).__init__(parent)
        self.main_layout=QGridLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        # create menu bar
        self.menu_bar=QMenuBar()
        self.menu_bar.setAutoFillBackground(True)

        self.action_menu=self.menu_bar.addMenu("Mulai")
        self.action_menu.addAction(QAction("Tebak Gambar",self))
        self.action_menu.addAction(QAction("Berhitung",self))
        self.action_menu.addAction(QAction("Kuis", self))

        self.menu_bar.addAction(QAction("Tentang", self))
        self.menu_bar.addAction(QAction("Bantuan", self))

        self.menu_bar.triggered.connect(self.change_view)
        self.main_layout.addWidget(self.menu_bar,0,0)        

        self.tebak_gambar_view=TebakGambar()
        self.welcome=Welcome()
        self.onprogress=OnProgress()
        self.berhitung=Berhitung()

        self.stacked_widget=QStackedWidget(self)
        self.stacked_widget.addWidget(self.welcome)
        self.stacked_widget.addWidget(self.tebak_gambar_view)
        self.stacked_widget.addWidget(self.onprogress)
        self.stacked_widget.addWidget(self.berhitung)

        self.menu_dict={
            "": self.welcome,
            "Tebak Gambar": self.tebak_gambar_view,
            "Berhitung": self.berhitung,
            "Kuis": self.onprogress,
            "Tentang": self.onprogress,
            "Bantuan": self.onprogress,
        }
        
        self.main_widget=QWidget()
        self.main_layout.addWidget(self.stacked_widget,1,0)
        self.main_widget.setLayout(self.main_layout)

        self.setCentralWidget(self.main_widget)
        self.setWindowTitle("AI Media Pembelajaran")
        self.setMinimumWidth(960)
        self.setMinimumHeight(960)
        self.adjustSize()
        self.setWindowIcon(QIcon("./assets/mikir.ico"))
    def change_view(self, event):
        prev = self.stacked_widget.currentWidget()
        prev.destroy(True)
        self.stacked_widget.removeWidget(self.stacked_widget.currentWidget())
        self.stacked_widget.addWidget(prev)
        self.stacked_widget.setCurrentWidget(self.menu_dict[event.text()])




class TebakGambar(QWidget):
    def __init__(self, parent= None):
        super(TebakGambar, self).__init__(parent)
        # initializing other class used
        self.layout=QVBoxLayout()
        self.worker = VoiceWorker()
        self.imager = LoadImage()
        self.threads = QThread()
        self.answer=""  #for storing the correct answer
        self.end_image=False

        #horizontal layout
        self.top_widget=QWidget()
        self.top_layout=QHBoxLayout()
        #label image_round
        self.label_round=QLabel("Gambar ke: ")
        self.label_round.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_round.setFont(QFont("SansSerif", 12, weight=2))
        self.imager.image_round.connect(self.label_round.setText)
        self.top_layout.addWidget(self.label_round)
        # label for title
        self.label_text = QLabel()
        self.label_text.setText("Tebak Gambar")
        self.label_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_text.setFont(QFont("SansSerif", 20, weight=5))
        self.top_layout.addWidget(self.label_text)
        # label tema
        self.label_topic=QLabel("Tema: ")
        self.label_topic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_topic.setFont(QFont("SansSerif", 12, weight=2))
        self.top_layout.addWidget(self.label_topic)
        
        self.top_widget.setLayout(self.top_layout)
        self.layout.addWidget(self.top_widget)

        # label which carrying image as pixmap
        self.pixmap_layout=QGridLayout()
        self.pixmap_widget=QWidget()
        self.image_label = QLabel(self)
        pixmap = QPixmap('')
        self.image_label.setPixmap(pixmap)
        self.image_label.setScaledContents(True)
        self.imager.imageData.connect(self.setImageData)
        self.pixmap_layout.addWidget(self.image_label, 0,0, alignment=Qt.AlignmentFlag.AlignJustify)
        self.pixmap_widget.setLayout(self.pixmap_layout)
        self.layout.addWidget(self.pixmap_widget)

        # label for informing whether program is recording or showing the result
        self.label_program=QLabel()
        self.label_program.setText("")
        self.label_program.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.worker.statusProgram.connect(self.label_program.setText)
        self.layout.addWidget(self.label_program)

        # label for showing recorded sound
        self.label_catched=QLabel()
        self.label_catched.setText("")
        self.label_catched.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.worker.textChanged.connect(self.checkAnswer)
        self.layout.addWidget(self.label_catched)

        # label for showing the result wheter answer is correct or not
        self.label_result=QLabel()
        self.label_result.setFont(QFont("SansSerif", 16, weight=5))
        self.label_result.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.label_result)

        #new nested layout
        self.widget_button=QWidget()
        self.widget_button_layout=QHBoxLayout()
        # button change picture
        self.button_layout=QFormLayout()
        self.button_image=QPushButton("Ganti Gambar")
        self.button_image.setMinimumHeight(30)
        self.button_image.setMaximumWidth(200)
        self.imager.max_round.connect(self.button_image.setEnabled)
        self.imager.max_round.connect(self.onEndImage)
        # self.layout.addWidget(self.button_image , alignment=Qt.AlignmentFlag.AlignCenter)
        self.widget_button_layout.addWidget(self.button_image , alignment=Qt.AlignmentFlag.AlignCenter)

        # button to record answer
        self.button_start=QPushButton("Jawab")
        self.button_start.setMinimumHeight(30)
        self.button_start.setMaximumWidth(200)
        # self.layout.addWidget(self.button_start , alignment=Qt.AlignmentFlag.AlignCenter)
        self.widget_button_layout.addWidget(self.button_start , alignment=Qt.AlignmentFlag.AlignCenter)
        
        #button restart
        self.button_restart=QPushButton("Ulangi")
        self.button_restart.setMinimumHeight(30)
        self.button_restart.setMaximumWidth(200)
        self.button_restart.setEnabled(False)
        self.widget_button_layout.addWidget(self.button_restart , alignment=Qt.AlignmentFlag.AlignCenter)

        self.widget_button.setLayout(self.widget_button_layout)
        self.layout.addWidget(self.widget_button)

        # adding action to each button
        self.button_start.clicked.connect(self.onClick)
        self.button_image.clicked.connect(self.onClick)
        self.button_start.clicked.connect(self.worker.task)
        self.button_image.clicked.connect(self.imager.game)
        self.threads.start()
        self.worker.enabled.connect(self.button_start.setEnabled)
        
        # moving the external proccess outside GUI to threads
        self.worker.moveToThread(self.threads)
        self.imager.moveToThread(self.threads)

        # configuring windows
        self.setLayout(self.layout)

    def onClick(self):
        self.label_program.setText("")
        self.label_catched.setText("")
        self.label_result.setText("")

    def checkAnswer(self, text):
        self.label_catched.setText(text)
        print(self.label_catched.text().replace("'","") +':'+self.answer)
        if self.label_catched.text().replace("'","")==self.answer:
            self.label_result.setText("Benar")
            self.label_result.setStyleSheet("color: blue")
            self.sound = QSound("./assets/suara/benar.wav")
            self.sound.play()
        else:
            self.label_result.setText("Salah")
            self.label_result.setStyleSheet("color: red")
            self.sound = QSound("./assets/suara/salah.wav")
            self.sound.play()

    def setImageData(self, data):
        self.sound = QSound("./assets/suara/buka.wav")
        self.sound.play()
        self.label_topic.setText("Tema: "+data["TEMA"])
        pixmap=QPixmap("./gambar/"+data["NAMA_FILE_GAMBAR"])
        # pixmap.scaled(pixmap.size(), aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio, transformMode=Qt.FastTransformation)
        self.image_label.setPixmap(pixmap.scaled(pixmap.size(), aspectRatioMode=Qt.AspectRatioMode.IgnoreAspectRatio))
        self.image_label.setScaledContents(True)
        self.answer=data["JAWABAN"]
    def onEndImage(self, cond):
        if not cond:
            self.end_image=True
            self.button_restart.setEnabled(True)
            self.button_restart.clicked.connect(self.restart)
    def restart(self):
        self.onClick()
        self.image_label.setPixmap(QPixmap(""))
        self.label_round.setText("Gambar ke: ")
        self.label_topic.setText("Tema: ")
        self.button_image.setEnabled(True)
        self.button_restart.setEnabled(False)
        self.button_restart.clicked.connect(self.restart)
class Welcome(QWidget):
    def __init__(self, parent= None):
        super(Welcome, self).__init__(parent)

        self.layout=QVBoxLayout()
        self.title_label=QLabel()
        self.title_label.setText("Selamat datang")
        self.title_label.setFont(QFont("SansSerif", 20, weight=5))
        self.layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.caption=QLabel("""
        Sebuah program sederhana yang memanfaatkan teknologi kecerdasan buatan untuk media pemberlajaran.
        Sasaran utama dari program ini adalah anak-anak usia prasekolah.
        """)
        self.caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.caption.setFont(QFont("SansSerif", 10, weight=2))
        self.layout.addWidget(self.caption, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(self.layout)
class Berhitung(QWidget):
    def __init__(self, parent= None):
        super(Berhitung, self).__init__(parent)
        self.layout=QVBoxLayout()
        self.title_label=QLabel()
        self.title_label.setText("Berhitung")
        self.title_label.setFont(QFont("SansSerif", 20, weight=5))
        self.layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(self.layout)


class Bantuan(QWidget):
    pass
class Tentang(QWidget):
    pass
class OnProgress(QWidget):
    def __init__(self, parent= None):
        super(OnProgress, self).__init__(parent)
        self.layout=QVBoxLayout()
        self.title_label=QLabel()
        self.title_label.setText("On Progress")
        self.title_label.setFont(QFont("SansSerif", 20, weight=5))
        self.title_label.setStyleSheet("color: red")
        self.layout.addWidget(self.title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(self.layout)

if __name__=="__main__":
    app = QApplication(sys.argv)
    speech_to_text = MainGUI()
    speech_to_text.show()
    sys.exit(app.exec_())