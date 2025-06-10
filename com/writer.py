import serial
from pyjoystick.sdl2 import run_event_loop
import threading
import time

# === CAN PROTOCOL SINIFI === #
class CANProtocol:
    PACKET_HEADER = 0xaa
    END_CODE = 0x55

    FRAME_TYPE_STANDARD = 0b0 << 5
    FRAME_TYPE_EXTENDED = 0b1 << 5
    FRAME_FORMAT_DATA = 0b0 << 4
    FRAME_FORMAT_REMOTE = 0b1 << 4
    BASE_TYEP_BITS = 0b11000000

    def __init__(self): pass

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

# === CAN PROTOKOL NESNESİ === #
can_protocol_handler = CANProtocol()

# === SERİ PORTU AÇ === #
try:
    ser = serial.Serial('COM6', 2000000, timeout=1)
    print("Port açıldı, joystick ile paket gönderimi başlıyor...")
except serial.SerialException as e:
    print(f"Port açılamadı: {e}")
    ser = None

# === CAN PAKET OLUŞTURUCU === #
def create_can_packet(frame_id, data_bytes, extended_frame=False, remote_frame=False):
    try:
        return can_protocol_handler.pack_can_frame(
            frame_id, data_bytes,
            is_extended=extended_frame,
            is_remote=remote_frame
        )
    except ValueError as e:
        print(f"Paket oluşturulurken hata: {e}")
        return None

# === TUŞ BASILI TUTMA VERİ GÖNDERME === #
pressed_keys = set()

def key_received(key):
    print(key)

    # Sadece Button 6 ve 7 kontrol edilir
    if key not in ['Button 6', 'Button 7']:
        return

    if key.value == 1:
        pressed_keys.add(key)
    elif key.value == 0:
        pressed_keys.discard(key)

def message_loop():
    while True:
        if ser and ser.is_open:
            for key_name in list(pressed_keys):
                if key_name == 'Button 7':
                    data = (10).to_bytes(1, 'big')
                elif key_name == 'Button 6':
                    data = (9).to_bytes(1, 'big')
                else:
                    continue

                packet = create_can_packet(126, data)
                if packet:
                    try:
                        ser.write(packet)
                        print(f"-> {key_name} için gönderildi: {packet.hex()}")
                    except serial.SerialException as e:
                        print(f"Seri porta yazılırken hata: {e}")
        time.sleep(0.1)  # 100ms

# === ARKAPLAN THREAD BAŞLAT === #
threading.Thread(target=message_loop, daemon=True).start()

# === JOYSTICK EVENT LOOP === #
try:
    run_event_loop(lambda joy: print('Joystick bağlandı:', joy),
                   lambda joy: print('Joystick çıkarıldı:', joy),
                   key_received)
except KeyboardInterrupt:
    print("Program durduruldu.")
finally:
    if ser and ser.is_open:
        ser.close()
        print("Seri port kapatıldı.")
