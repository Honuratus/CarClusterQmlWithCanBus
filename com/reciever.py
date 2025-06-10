import serial

def parse_can_packet(packet):
    if len(packet) < 5:
        raise ValueError("Paket çok kısa")
    if packet[0] != 0xAA:
        raise ValueError("Paket başlığı bulunamadı")

    type_byte = packet[1]
    frame_type = (type_byte >> 5) & 0x01       # bit5
    frame_format = (type_byte >> 4) & 0x01     # bit4
    data_length = type_byte & 0x0F              # bit0~3

    if frame_type == 0:  # standard frame
        frame_id = (packet[2] << 8) | packet[3]
        frame_data = packet[4:4+data_length]
        end_code = packet[4+data_length]
    else:  # extended frame
        frame_id = (packet[2] << 24) | (packet[3] << 16) | (packet[4] << 8) | packet[5]
        frame_data = packet[6:6+data_length]
        end_code = packet[6+data_length]

    if end_code != 0x55:
        raise ValueError("Paket sonu kodu hatalı")

    return frame_id, data_length, frame_data


try:
    ser = serial.Serial('COM6', 2000000, timeout=1)  # USB-CAN cihazının COM portu ve 2M baud
    print("Port açıldı, veri okunuyor...")
    
    while True:
        if ser.in_waiting > 0:
            read_data = ser.read(ser.in_waiting)
            id,length,data = parse_can_packet(read_data)
            print(f"Frame ID: {id} | Data Length: {length}")
            print(f"Data: {data.hex()}")

except serial.SerialException as e:
    print(f"Port açılamadı: {e}")
except KeyboardInterrupt:
    print("Program durduruldu.")
finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
