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

class CANWriter(QObject):
    def __init__(self, serial_connection):
        super().__init__()
        self.serial_connection = serial_connection
        self.can_protocol = CANProtocol()
        self.lock = QMutex()
        self.running = True
        
        # Gamepad state tracking
        self.current_state = {
            'BTN_BASE2': 0,  # A button
            'BTN_BASE': 0,   # B button
            'BTN_WEST': 0,   # X button
            'BTN_NORTH': 0,  # Y button
            'ABS_HAT0X': 0,  # D-pad X axis
            'ABS_HAT0Y': 0,  # D-pad Y axis
            'ABS_Z': 0,      # Left trigger (Gaz)
            'ABS_RZ': 0      # Right trigger (Fren)
        }
        
        # Debounce tracking
        self.last_event_time = 0
        self.debounce_delay = 0.1  # 100ms
        self.last_send_time = 0
        self.send_interval = 0.05  # 50ms

    def handle_gamepad_event(self, event):
        current_time = time.time()
        
        # Trigger butonları için özel işleme
        if event.code in ['ABS_Z', 'ABS_RZ']:
            # Trigger değerlerini normalize et (0-255 arası)
            value = max(0, min(255, int((event.state + 32768) / 256)))
            self.current_state[event.code] = value
            self.last_event_time = current_time
            return
            
        if current_time - self.last_event_time < self.debounce_delay:
            return
            
        if event.code in self.current_state and self.current_state[event.code] != event.state:
            self.current_state[event.code] = event.state
            self.last_event_time = current_time
            
            if event.code == "ABS_HAT0X":
                self.process_dpad_x(event.state)
            elif event.code == "ABS_HAT0Y":
                self.process_dpad_y(event.state)
            else:
                self.process_button(event.code, event.state)

    def process_dpad_x(self, state):
        self.current_state['ABS_HAT0X'] = state
        if state == -1:  # Left
            self.send_can_command(132, (8).to_bytes(1, 'big'))
        elif state == 1:  # Right
            self.send_can_command(133, (7).to_bytes(1, 'big'))

    def process_dpad_y(self, state):
        self.current_state['ABS_HAT0Y'] = state
        if state == -1:  # Up
            self.send_can_command(134, (6).to_bytes(1, 'big'))
        elif state == 1:  # Down
            self.send_can_command(135, (5).to_bytes(1, 'big'))
    
    def process_button(self, button_code, state):
        if button_code in ['BTN_BASE2', 'BTN_BASE', 'BTN_WEST', 'BTN_NORTH']:
            if state == 1:  # Button pressed
                if button_code == "BTN_BASE2":  # A
                    self.send_can_command(130, (10).to_bytes(1, 'big'))
                elif button_code == "BTN_BASE":  # B
                    self.send_can_command(131, (9).to_bytes(1, 'big'))
                elif button_code == "BTN_WEST":  # X
                    self.send_can_command(136, (4).to_bytes(1, 'big'))
                elif button_code == "BTN_NORTH":  # Y
                    self.send_can_command(137, (3).to_bytes(1, 'big'))
            elif state == 0:  # Button released
                # Send a "release" command or stop sending for this button
                self.send_can_command(140, (0).to_bytes(1, 'big'))  # Example release command

    def send_loop(self):
        while self.running:
            current_time = time.time()
            if current_time - self.last_send_time >= self.send_interval:
                self.lock.lock()
                try:
                    # Trigger (gaz/fren) değerlerini sürekli gönder
                    if self.current_state['ABS_Z'] > 10:  # Gaz (Left trigger)
                        value = self.current_state['ABS_Z']
                        self.send_can_command(138, value.to_bytes(1, 'big'))
                        
                    if self.current_state['ABS_RZ'] > 10:  # Fren (Right trigger)
                        value = self.current_state['ABS_RZ']
                        self.send_can_command(139, value.to_bytes(1, 'big'))
                        
                    # Diğer buton durumlarını kontrol et
                    for btn, state in self.current_state.items():
                        if btn in ['BTN_BASE2', 'BTN_BASE', 'BTN_WEST', 'BTN_NORTH'] and state == 1:
                            self.process_button(btn, state)
                            
                finally:
                    self.lock.unlock()
                    self.last_send_time = current_time
                    
            time.sleep(0.01)  # Daha hassas kontrol

    def send_can_command(self, frame_id, data):
        try:
            packet = self.can_protocol.pack_can_frame(frame_id, data)
            if packet and self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.write(packet)
                print(f"Sent: {frame_id} -> {packet.hex()}")
        except Exception as e:
            print(f"Error sending CAN command: {e}")

    def stop(self):
        self.running = False

class GamepadThread(QThread):
    def __init__(self, can_writer):
        super().__init__()
        self.can_writer = can_writer
        self.running = True
        self.gamepad = None
        
        # Gamepad bağlantısını kontrol et
        if not devices.gamepads:
            print("No gamepad found!")
        else:
            self.gamepad = devices.gamepads[0]
            print(f"Gamepad found: {self.gamepad}")

    def run(self):
        print("Gamepad thread started")
        while self.running:
            try:
                if self.gamepad:
                    events = self.gamepad.read()
                    for event in events:
                        self.can_writer.handle_gamepad_event(event)
                else:
                    time.sleep(1)  # Gamepad yoksa bekle
            except Exception as e:
                print(f"Gamepad error: {e}")
                time.sleep(1)

    def stop(self):
        self.running = False

def main():
    # Seri portu aç
    try:
        ser = serial.Serial('/dev/ttyUSB1', 2000000, timeout=1)
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