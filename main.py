import serial
import threading
import time
from inputs import get_gamepad, devices

from PySide6.QtCore import QObject, Signal, QThread, QTimer, QMutex
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

import os

# === CAN PROTOCOL === #
class CANProtocol:
    PACKET_HEADER = 0xaa
    END_CODE = 0x55

    FRAME_TYPE_STANDARD = 0b0 << 5
    FRAME_TYPE_EXTENDED = 0b1 << 5
    FRAME_FORMAT_DATA = 0b0 << 4
    FRAME_FORMAT_REMOTE = 0b1 << 4
    BASE_TYEP_BITS = 0b11000000

    def pack_can_frame(self, frame_id: int, data: bytes, is_extended: bool = False, is_remote: bool = False) -> bytes:
        if not (0 <= len(data) <= 8):
            raise ValueError("Data length max 8 byte olabilir.")
        if is_extended:
            if not (0 <= frame_id < (1 << 29)):
                raise ValueError(f"Extended Frame ID must be between 0 and {(1 << 29) - 1}.")
        else:
            if not (0 <= frame_id < (1 << 11)):
                raise ValueError(f"Standard Frame ID must be between 0 and {(1 << 11) - 1}.")

        tyep_byte = self.BASE_TYEP_BITS
        tyep_byte |= self.FRAME_TYPE_EXTENDED if is_extended else self.FRAME_TYPE_STANDARD
        tyep_byte |= self.FRAME_FORMAT_REMOTE if is_remote else self.FRAME_FORMAT_DATA
        tyep_byte |= (len(data) & 0b00001111)

        packed_frame = bytearray([self.PACKET_HEADER, tyep_byte])
        id_bytes = frame_id.to_bytes(4 if is_extended else 2, 'big')
        packed_frame.extend(id_bytes)
        packed_frame.extend(data)
        packed_frame.append(self.END_CODE)

        return bytes(packed_frame)

# === CAN RECEIVER === #
class CANReceiver(QObject):
    canDistanceDataReceived = Signal(int, int, str)  # frame_id, length, data_hex
    canMotorDataReceived = Signal(int, int, str)
    canTempDataReceived = Signal(int, int, str)
    canLeftSignalDataReceived = Signal(int, int, str)
    canRightSignalDataReceived = Signal(int, int, str)
    canBreakSignalDataReceived = Signal(int, int, str)

    def __init__(self, serial_connection):
        super().__init__()
        self.serial_connection = serial_connection
        self.running = False

    def parse_can_packet(self, packet):
        try:
            if len(packet) < 5:
                raise ValueError("Paket çok kısa")
            if packet[0] != 0xAA:
                raise ValueError("Geçersiz başlık")

            type_byte = packet[1]
            frame_type = (type_byte >> 5) & 0x01
            data_length = type_byte & 0x0F

            if frame_type == 0:  # Standard frame
                if len(packet) < 4 + data_length + 1:
                    raise ValueError("Standard frame için paket tam değil")
                frame_id = (packet[2] << 8) | packet[3]
                frame_data = packet[4:4+data_length]
                end_pos = 4 + data_length
            else:  # Extended frame
                if len(packet) < 6 + data_length + 1:
                    raise ValueError("Extended frame için paket tam değil")
                frame_id = (packet[2] << 24) | (packet[3] << 16) | (packet[4] << 8) | packet[5]
                frame_data = packet[6:6+data_length]
                end_pos = 6 + data_length

            if packet[end_pos] != 0x55:
                raise ValueError("Geçersiz sonlandırıcı")

            return frame_id, data_length, frame_data

        except Exception as e:
            print(f"Parse hatası: {e}, Paket: {packet.hex()}")
            raise

    def start_receiving(self):
        self.running = True
        self.buffer = bytearray()
        print("CAN Receiver başlatıldı...")

        while self.running:
            try:
                if self.serial_connection.in_waiting > 0:
                    new_data = self.serial_connection.read(self.serial_connection.in_waiting)
                    self.buffer.extend(new_data)

                    while True:
                        header_pos = self.buffer.find(0xAA)
                        if header_pos == -1:
                            self.buffer.clear()
                            break

                        if header_pos > 0:
                            self.buffer = self.buffer[header_pos:]

                        if len(self.buffer) < 2:
                            break

                        type_byte = self.buffer[1]
                        data_length = type_byte & 0x0F
                        frame_type = (type_byte >> 5) & 0x01

                        min_len = 6 + data_length + 1 if frame_type else 4 + data_length + 1
                        if len(self.buffer) < min_len:
                            break

                        try:
                            frame_id, length, data = self.parse_can_packet(self.buffer[:min_len])

                            if frame_id == 0x2301:
                                self.canDistanceDataReceived.emit(frame_id, length, data.hex())
                            elif frame_id == 0x2601:
                                self.canMotorDataReceived.emit(frame_id, length, data.hex())
                            elif frame_id == 0x2801:
                                self.canTempDataReceived.emit(frame_id, length, data.hex())
                            elif frame_id == 0x2901:
                                self.canLeftSignalDataReceived.emit(frame_id, length, data.hex())
                            elif frame_id == 0x3001:
                                self.canRightSignalDataReceived.emit(frame_id, length, data.hex())
                            elif frame_id == 0x3101:
                                self.canBreakSignalDataReceived.emit(frame_id, length, data.hex())
                            else:
                                print(f"Bilinmeyen ID: {hex(frame_id)}")

                            self.buffer = self.buffer[min_len:]

                        except Exception as e:
                            print(f"Paket işleme hatası: {e}")
                            if len(self.buffer) > 1:
                                self.buffer = self.buffer[1:]
                            else:
                                self.buffer.clear()
                            continue

            except serial.SerialException as e:
                print(f"Seri port hatası: {e}")
                self.running = False

    def stop_receiving(self):
        self.running = False

class CANReceiverThread(QThread):
    def __init__(self, receiver):
        super().__init__()
        self.receiver = receiver

    def run(self):
        self.receiver.start_receiving()

# === CAN WRITER === #
class CANWriter(QObject):
    def __init__(self, serial_connection):
        super().__init__()
        self.serial_connection = serial_connection
        self.can_protocol = CANProtocol()
        self.pressed_keys = set()
        self.lock = QMutex()
        self.running = True

    def create_can_packet(self, frame_id, data_bytes, extended_frame=False, remote_frame=False):
        try:
            return self.can_protocol.pack_can_frame(frame_id, data_bytes, extended_frame, remote_frame)
        except ValueError as e:
            print(f"Paket oluşturulurken hata: {e}")
            return None

    def handle_gamepad_event(self, event):
        """Process gamepad events and update pressed_keys set"""
        key_name = None
        value = event.state
        
        if event.code == "BTN_BASE2":  # A button (Xbox), Cross (PS)
            key_name = 'Button_A'
        elif event.code == "BTN_BASE":  # B button (Xbox), Circle (PS)
            key_name = 'Button_B'
        elif event.code == "BTN_WEST":  # X button (Xbox), Square (PS)
            key_name = 'Button_X'
        elif event.code == "BTN_NORTH":  # Y button (Xbox), Triangle (PS)
            key_name = 'Button_Y'
        elif event.code == "ABS_HAT0X":
            if value == -1:
                key_name = 'Hat_Left'
            elif value == 1:
                key_name = 'Hat_Right'
            else:
                # Centered - remove directional keys
                self.pressed_keys.discard('Hat_Left')
                self.pressed_keys.discard('Hat_Right')
                return
        elif event.code == "ABS_HAT0Y":
            if value == -1:
                key_name = 'Hat_Up'
            elif value == 1:
                key_name = 'Hat_Down'
            else:
                # Centered - remove directional keys
                self.pressed_keys.discard('Hat_Up')
                self.pressed_keys.discard('Hat_Down')
                return
        else:
            print(event.code)
            return

        if key_name:
            if value != 0:
                self.pressed_keys.add(key_name)
            else:
                self.pressed_keys.discard(key_name)

    def send_loop(self):
        while self.running:
            self.lock.lock()
            if self.serial_connection and self.serial_connection.is_open:
                for key_name in list(self.pressed_keys):
                    if key_name == 'Button_A':
                        data = (10).to_bytes(1, 'big')
                        id = 130
                    elif key_name == 'Button_B':
                        data = (9).to_bytes(1, 'big')
                        id = 131
                    elif key_name == 'Hat_Left':
                        data = (8).to_bytes(1, 'big')
                        id = 132
                    elif key_name == 'Hat_Right':
                        data = (7).to_bytes(1, 'big')
                        id = 133
                    elif key_name == 'Hat_Down':
                        data = (6).to_bytes(1, 'big')
                        id = 134
                    else:
                        continue
                    
                    packet = self.create_can_packet(id, data)
                    if packet:
                        try:
                            self.serial_connection.write(packet)
                            print(f"Gönderildi: {key_name} -> {packet.hex()}")
                        except serial.SerialException as e:
                            print(f"Seri porta yazılırken hata: {e}")
            self.lock.unlock()
            time.sleep(0.1)

    def stop(self):
        self.running = False

class GamepadThread(QThread):
    def __init__(self, can_writer):
        super().__init__()
        self.can_writer = can_writer
        self.running = True

    def run(self):
        print("Gamepad thread started. Looking for gamepad...")
        while self.running:
            try:
                events = get_gamepad()
                for event in events:
                    self.can_writer.handle_gamepad_event(event)
            except Exception as e:
                print(f"Gamepad error: {e}")
                time.sleep(1)

    def stop(self):
        self.running = False

def main():
    # Seri portu aç
    try:
        ser = serial.Serial('/dev/ttyUSB0', 2000000, timeout=1)
        print("Seri port açıldı.")
    except serial.SerialException as e:
        print(f"Seri port açılamadı: {e}")
        return

    # PySide uygulaması başlat
    app = QGuiApplication()

    # CANReceiver ve thread'i oluştur
    can_receiver = CANReceiver(ser)
    receiver_thread = CANReceiverThread(can_receiver)
    receiver_thread.start()

    # CANWriter oluştur
    can_writer = CANWriter(ser)

    # Gamepad thread'i başlat
    gamepad_thread = GamepadThread(can_writer)
    gamepad_thread.start()

    # CANWriter gönderim döngüsünü thread ile başlat
    send_thread = threading.Thread(target=can_writer.send_loop)
    send_thread.daemon = True
    send_thread.start()

    # QML engine setup
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("canReceiver", can_receiver)
    engine.load("main.qml")
    
    if not engine.rootObjects():
        return -1

    # Uygulamayı çalıştır
    ret = app.exec()

    # Kapanış işlemleri
    can_receiver.stop_receiving()
    can_writer.stop()
    gamepad_thread.stop()
    receiver_thread.quit()
    receiver_thread.wait()
    gamepad_thread.wait()
    
    if ser and ser.is_open:
        ser.close()
        print("Seri port kapatıldı.")

    return ret

if __name__ == "__main__":
    main()