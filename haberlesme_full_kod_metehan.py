import base64
import json
import socket

import cv2
import imutils
import numpy as np
import requests
from datetime import time

class server_TCP():
    def __init__(self):
        super(server_TCP, self).__init__()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sakla = requests.Session()

    def baglan(self, host, port):
        self.s.bind((host, port))
        self.s.listen(0)
        print('Dinleniyor...')
        self.clientsocket, self.adres = self.s.accept()
        print(f'Bağlantı {self.adres} ile Kuruldu!!!')
        return self.clientsocket

    def sunucu_giris(self, url, kullanici_adi, sifre):
        self.header = {
            'Content-type': 'application/json',
            'Accept': 'application/json'
        }
        self.giris = {
            "kullanici_adi": kullanici_adi, "sifre": sifre
        }
        self.gidecek = json.dumps(self.giris)
        print(self.gidecek)

        self.giden = self.sakla.post(url + '/api/giriş', self.gidecek, headers=self.headers)

        return self.giden.status_code, self.giden.text

    def kamikaze_gonder(self, url, mesaj):
        self.headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json'
        }

        self.mesaj = json.dumps(mesaj)
        print(self.mesaj)

        self.kamikaze = self.sakla.post(url + '/api/kamikaze_bilgisi', self.mesaj, headers=self.headers)

        return self.kamikaze.status_code

    def kilitlenme_gonder(self, url, mesaj):
        self.headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json'
        }

        self.mesaj = json.dumps(mesaj)
        print(self.mesaj)

        self.kilitlenme = self.sakla.post(url + '/api/kilitlenme-bilgisi', self.mesaj, headers=self.headers)

        return self.kilitlenme.status_code

    def telemetri_gonder(self, mesaj):
        self.mesaj = json.dumps(mesaj)
        self.clientsocket.send(self.mesaj.encode("utf-8"))

    def sunucu_saati_al(self, url):
        self.sunucu_saati = self.sakla.get(url + 'api/sunucusaati')

        return self.sunucu_saati.status_code, self.sunucu_saati.text

    def qr_koordinat_al(self, url):
        self.qr_koordinat = self.sakla.get(url + '/api/qr_koordinati')

        return self.qr_koordinat.status_code, self.qr_koordinat.text

    def telemetri_al(self):
        self.cevap = self.clientsocket.recv(512)
        self.sonuc = json.dumps(self.cevap.decode('utf-8'))
        self.sonuc = json.loads(self.sonuc)
        return self.sonuc

    def sunucu_gonder(self, url, mesaj):
        self.headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json'
        }

        self.mesaj = json.dumps(mesaj)

        self.rakip = self.sakla.post(url + '/api/telemetri-gonder', self.mesaj, headers=self.headers)

        return self.rakip.status_code, self.rakip.text

    def sunucu_cikis(self, url):
        self.cikis = self.sakla.get(url + '/api/cikis')

        return self.cikis


class client_TCP():
    def __init__(self):
        super(client_TCP, self).__init__()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def baglan(self, host, port):
        self.s.connect((host, port))
        return self.s

    def telemetri_gonder(self, mesaj):
        self.mesaj = json.dumps(mesaj)
        self.s.sendall(self.mesaj.encode("utf-8"))

    def telemetri_al(self):
        self.cevap = self.s.recv(2048)
        self.sonuc = json.dumps(self.cevap.decode("utf-8"))
        self.sonuc = json.loads(self.sonuc)
        return self.sonuc


class server_UDP():
    def __init__(self):
        super(server_UDP, self).__init__()
        self.BUFF_SIZE = 65536
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.BUFF_SIZE)
        self.host_name = socket.gethostname()

    def baglan(self, host, port):
        self.socket_address = (host, port)
        self.s.bind(self.socket_address)
        print('Listening at:', self.socket_address)
        return self.s

    def video_al(self, vid, BUFF_SIZE, WIDTH):
        vid = cv2.VideoCapture()

        fps, st, frames_to_count, cnt = (0, 0, 20, 0)

        while True:
            self.mesaj, self.client_address = self.s.recvfrom(BUFF_SIZE)
            print("Bağlantı kuruldu:", self.client_address)

            while (vid.isOpened()):
                _, self.frame = vid.read()
                self.frame = imutils.resize(self.frame, width=WIDTH)

                encoded, buffer = cv2.imencode('.jpg', self.frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                # cv2.imencode kullanılarak video istenilen formatta ve kalitede "sıkıştırılarak" alınır.
                # cv2.IMWRITE_JPEG_QUALITY dosyaya görüntüyü alırken istenilen kalitede sıkıştırmak için kullanılmıştır.

                mesaj = base64.b64encode(buffer)  # string olarak gelen veriyi binary olarak çevirir

                self.s.sendto(mesaj, self.client_address)
                cv2.imshow("Video Aktarılıyor...", self.frame)  # Görüntülenecek pencerenin adı ve gösterilecek görüntü
                self.key = cv2.waitKey(1) & 0xFF  # waitKey 'q' tuşuna basana kadar pencereyi kapatmaz.
                if self.key == ord('q'):
                    self.s.close()
                    break

    def mesaj_al(self, mesaj):
        self.mesaj, self.server = self.s.recvfrom(1024)
        return self.mesaj

    def mesaj_gonder(self, mesaj):

        if isinstance(mesaj, dict):
            mesaj = str(mesaj)

        self.mesaj = json.dumps(mesaj)
        mesaj = str.encode(self.mesaj)
        self.s.sendto(mesaj, self.server)


class client_UDP():
    def __init__(self):
        super(client_UDP, self).__init__()
        self.BUFF_SIZE = 65536
        self.WIDTH = 800
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.BUFF_SIZE)
        self.host_name = socket.gethostname()

    def baglan(self, host, port):
        self.client_address = (host, port)

        return self.client_address, self.s

    def video_gonder(self, frame, message, host, port, BUFF_SIZE):
        self.s.sendto(message, (host, port))
        fps, st, frames_to_count, cnt = (0, 0, 20, 0)

        while True:
            packet, _ = self.s.recvfrom(BUFF_SIZE)
            data = base64.b64decode(packet, " /")  # binary text i normal forma dönüştürme
            npdata = np.fromstring(data, dtype=np.uint8)
            frame = cv2.imdecode(npdata,
                                 1)  # görüntü verilerini okumak ve görüntü biçimine dönüştürmek için kullanılır.
            frame = cv2.putText(frame, 'FPS: ' + str(fps), (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            # putText metodu herhangi bir görüntü üzerine text yazabilmek için kullanılır.
            cv2.imshow("RECEIVING VIDEO", frame)  # Görüntülenecek pencerenin adı ve gösterilecek görüntü
            key = cv2.waitKey(1) & 0xFF  # waitKey 'q' tuşuna basana kadar pencereyi kapatmaz.
            if key == ord('q'):
                self.s.close()
                break
            if cnt == frames_to_count:
                try:
                    fps = round(frames_to_count / (time.time() - st))
                    st = time.time()
                    cnt = 0
                except:
                    pass
            cnt += 1

    def mesaj_al(self):
        self.mesaj, self.server = self.s.recvfrom(1024)
        self.mesaj = self.mesaj.decode('utf-8')
        return self.mesaj

    def mesaj_gonder(self, mesaj):
        self.mesaj = str.encode(str(mesaj))
        self.s.sendto(mesaj, self.client_address)
