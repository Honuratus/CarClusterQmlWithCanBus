import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Window {
    id: debugWindow
    title: "CAN Debug Console"
    width: 800
    height: 600
    visible: false

    property var canMessages: []
    property bool isStopped: false    // Yeni: Veri eklemeyi durdurmak için

    function addCanMessage(frameId, length, dataHex) {
        if (isStopped) {
            console.log("Ekleme durduruldu, mesaj atlandı.");
            return;
        }

        console.log("Adding message:", frameId, length, dataHex); // Debug için
        var timestamp = new Date().toLocaleTimeString();
        canMessages.unshift({
            "timestamp": timestamp,
            "frameId": frameId.toString(16).toUpperCase(),
            "length": length,
            "dataHex": dataHex
        });

        // Keep only last 100 messages
        if (canMessages.length > 100) {
            canMessages = canMessages.slice(0, 100);
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 10

        Text {
            text: "CAN Debug Console"
            font.bold: true
            font.pixelSize: 20
            Layout.alignment: Qt.AlignHCenter
        }

        RowLayout {
            Button {
                text: "Clear"
                onClicked: canMessages = []
            }
            Button {
                id: stopButton
                text: isStopped ? "Start" : "Stop"     // Butonun durumu gösterilsin
                onClicked: {
                    isStopped = !isStopped
                }
            }
            Button {
                text: "Close"
                onClicked: debugWindow.close()
            }
        }

        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true

            ListView {
                id: messageList
                model: canMessages
                clip: true
                delegate: Rectangle {
                    width: parent ? parent.width : 0
                    height: 60
                    color: index % 2 === 0 ? "#f0f0f0" : "white"

                    Row {
                        anchors.fill: parent
                        anchors.margins: 5
                        spacing: 15

                        Text {
                            text: modelData.timestamp
                            width: 100
                            font.pixelSize: 12
                        }
                        Text{
                            text: {
                                if(modelData.frameId == 2601){
                                    return "Motor";
                                }
                                else if(modelData.frameId == 2301){
                                    return "Mesafe";
                                }
                                else if(modelData.frameId == 2801){
                                    return "Sıcaklık";
                                }
                                else if(modelData.frameId == 2901){
                                    return "Sol Sinyal";
                                }
                                else if(modelData.frameId == 3001){
                                    return "Sag Sinyal";
                                }
                                else if(modelData.frameId == 3101){
                                    return "Fren";
                                }
                                return "Bilinmeyen";
                            }

                            width: 100
                            font.pixelSize: 12
                        }

                        Text {
                            text: "ID: 0x" + modelData.frameId
                            width: 100
                            font.pixelSize: 12
                        }
                        Text {
                            text: "Len: " + modelData.length
                            width: 50
                            font.pixelSize: 12
                        }
                        Text {
                            text: "Data: " + modelData.dataHex
                            width: 100
                            font.pixelSize: 12
                        }
                        Text{
                            text: {
                                let rawData = parseInt(modelData.dataHex, 16);
                                if(modelData.frameId == 2601) rawData -= 15;
                                if(rawData <= 0) rawData = 0;
                                return "Ondalık: " + rawData;
                            }
                            width: 300
                            font.pixelSize: 12
                        }
                    }
                }
            }
        }
    }
}
