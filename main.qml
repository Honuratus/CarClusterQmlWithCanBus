import QtQuick
import QtQuick.Window
import QtQuick.Effects
// Main Window
Window {

    property bool isDark : false
    property bool isFinished: false
    property color lightBackground: "#EDEDED"
    property color darkBackground: "#0D0D0D"

    property color lightBoxColor: "#DEDEDE"
    property color darkBoxColor: "#262024"

    property color lightAccent: "#32C53F"

    property color lightBoxBorderColor: "#fff"
    property color darkBoxBorderColor: "#191418"

    property color lightTextColor : "#333337"
    property color lightSecondTextColor: "#5E5E5E"

    property color darkTextColor: "#F6E7FA"
    property color darkSecondTextColor: "#A69BAC"
    property var debugWindow: null


    FontLoader{
        id:interRegular
        source: "fonts/inter/Inter_28pt-Regular.ttf"
    }


    FontLoader{
        id:interThin
        source: "fonts/inter/Inter_28pt-Thin.ttf"
    }

    FontLoader  {
        id:interBold
        source: "fonts/inter/Inter_28pt-Bold.ttf"
    }

    id: mainWindow
    width: 1920
    height: 1080
    visible: true
    title: qsTr("Hello World")
    color: isDark ? darkBackground : lightBackground
    visibility: "FullScreen"

    // Warning Box
    Rectangle{
        id: distanceWarning
        visible: false
        width: mainWindow.width * (0.2)
        height: mainWindow.height * (0.2)
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.topMargin: 20
        color: mainWindow.isDark ? mainWindow.darkBoxColor : mainWindow.lightBoxColor
        radius: 10
        border.width: 1
        border.color: mainWindow.lightAccent
        Text{
            id:distanceText
            font.family: interRegular.name
            font.pointSize: 84
            text: "15"
            color: mainWindow.isDark ? mainWindow.darkTextColor : mainWindow.lightTextColor
            anchors.centerIn: parent
        }

        Text{
            id: distanceTextInfo
            font.family: interThin.name
            font.pointSize: 24
            text: "cm"
            color: mainWindow.isDark ? mainWindow.darkSecondTextColor : mainWindow.lightSecondTextColor
            anchors.bottom:parent.bottom
            anchors.horizontalCenter: parent.horizontalCenter
        }
    }


    Row{
        id: indicators
        anchors.left: leftBox.left
        anchors.bottom: leftBox.top
        anchors.bottomMargin: 20
        spacing: 10
        Image{
            id: rain
            source: "images/rain.png"
            width: 50
            height: 50
        }
        Image{
            id: light
            source: "images/position.png"
            width: 50
            height: 50
        }
        Image{
            id: autolight
            source: "images/auto.png"
            width: 50
            height: 50
        }
        Image{
            id: ready
            source: "images/ready.png"
            width: 50
            height: 50
        }
    }

    // Left Box
    Rectangle{
        id: leftBox
        width: mainWindow.width*(0.3)
        height: mainWindow.height*(0.4)
        anchors.left: parent.left
        anchors.leftMargin: 70
        anchors.verticalCenter: parent.verticalCenter
        color: mainWindow.isDark ? mainWindow.darkBoxColor : mainWindow.lightBoxColor
        border.color: mainWindow.isDark ? mainWindow.darkBoxBorderColor : mainWindow.lightBoxBorderColor
        border.width: 2
        radius:20

        visible: false
        layer.enabled: true


        Text{
            id:speedText
            font.family: interRegular.name
            font.pointSize: 120
            text: ""
            color: mainWindow.isDark ? mainWindow.darkTextColor : mainWindow.lightTextColor
            anchors.verticalCenter: parent.verticalCenter
            anchors.right: parent.right
            anchors.rightMargin: 25
        }
        Text{
            id: speedTextInfo
            font.family: interThin.name
            font.pointSize: 28
            text: "km/h"
            color: mainWindow.isDark ? mainWindow.darkSecondTextColor : mainWindow.lightSecondTextColor
            anchors.top: speedText.bottom
            anchors.right: speedText.right
            anchors.rightMargin: 25
        }
    }
    MultiEffect{
        source:leftBox
        anchors.fill: leftBox
        shadowEnabled: true
        shadowBlur: 1
        shadowColor: "darkgray"
        shadowHorizontalOffset: 0
        shadowVerticalOffset: 0
    }

    // saat ve sıcaklık
    Rectangle{
        id: tempAndDateBox
        width: mainWindow.width * (0.2)
        height: mainWindow.height * (0.2)
        color: mainWindow.isDark ? mainWindow.darkBoxColor : mainWindow.lightBoxColor
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.topMargin: 250
        radius: 10
        border.width: 2
        border.color: mainWindow.lightAccent
        Column{
            id: timeAndTemp
            spacing: 10
            anchors.centerIn: parent
            Text{
                id: tempText
                font.family: interRegular
                font.pointSize: 36
                color: mainWindow.isDark ? mainWindow.darkSecondTextColor : mainWindow.lightSecondTextColor
            }
            Text{
                id: dateText
                font.family: interRegular
                font.pointSize: 36
                color: mainWindow.isDark ? mainWindow.darkSecondTextColor : mainWindow.lightSecondTextColor
                text: {
                    const d = new Date();
                    return d.toLocaleTimeString().slice(0,5)
                }
            }
        }

    }


    // Road
    Road{
        id: road
    }



    //Right Box
    Rectangle{
        id:rightBox
        width: mainWindow.width*(0.3)
        height: mainWindow.height*(0.4)
        anchors.right: parent.right
        anchors.rightMargin: 70
        anchors.verticalCenter: parent.verticalCenter
        color: mainWindow.isDark ? mainWindow.darkBoxColor : mainWindow.lightBoxColor
        border.color: mainWindow.isDark ? mainWindow.darkBoxBorderColor : mainWindow.lightBoxBorderColor
        border.width: 2
        radius:20

        Item{
            id: wrapper
            width: childrenRect.width
            height: childrenRect.height
            anchors.verticalCenter: parent.verticalCenter
            Text{
                id:rangeText
                font.family: interRegular.name
                font.pointSize: 56
                text: "365"
                color: mainWindow.isDark ? mainWindow.darkTextColor : mainWindow.lightTextColor
                anchors.left: parent.left
                anchors.leftMargin: 25
            }
            // Maybe rectangle instead of text
            Text{
                id: chargeText
                font.family: interThin.name
                font.pointSize: 28
                text: "km"
                color: mainWindow.isDark ? mainWindow.darkSecondTextColor : mainWindow.lightSecondTextColor
                anchors.bottom: rangeText.bottom
                anchors.bottomMargin: 5

                anchors.left: rangeText.right
                anchors.leftMargin: 5
            }

        }
        Image{
            id: battery
            source: "images/battery.png"
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            anchors.rightMargin: 20
            width: 150
            height: 150
        }
        Text{
            id: batteryPercentage
            font.family: interRegular
            text: "100%"
            font.pointSize: 24
            anchors.top: battery.bottom
            anchors.topMargin: -20
            anchors.right: battery.right
            anchors.rightMargin: 55
            color: mainWindow.isDark ? mainWindow.darkSecondTextColor : mainWindow.lightSecondTextColor
        }
    }
    MultiEffect{
        source:rightBox
        anchors.fill: rightBox
        shadowEnabled: true
        shadowBlur: 1
        shadowColor: "darkgray"
        shadowHorizontalOffset: 0
        shadowVerticalOffset: 0
    }

    // Vites
    Column {
        property int active: 2
        spacing: 10

        anchors.right: parent.right
        anchors.rightMargin: 20
        anchors.verticalCenter: parent.verticalCenter

        Repeater {
            model: ["R", "N", "D"]

            Text {
                text: modelData
                font.pixelSize: (index == parent.active) ? 28 : 28
                font.family:  (index == parent.active) ? interBold : interRegular
                color: mainWindow.isDark ? ((index == parent.active) ? mainWindow.darkTextColor : "darkgray") : ((index == parent.active) ? mainWindow.lightTextColor :  "lightgrey")
            }
        }
        Rectangle{
            height: 28
            width: 28
            radius: 5
            color: mainWindow.lightAccent
            anchors.horizontalCenter: parent.horizontalCenter
        }
    }


    // Toggler Button
    Rectangle{

        id:togglerButton
        width: 100
        height: 50
        color: "transparent"
        border.width: 2
        border.color: mainWindow.isDark ? mainWindow.darkBoxBorderColor : mainWindow.lightBoxBorderColor
        radius: 20
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 20
        anchors.left: parent.left
        Text{
            font.family: interRegular.name
            text: mainWindow.isDark ? "Light Mode" : "Dark Mode"
            font.pointSize: 12
            anchors.centerIn: parent
            color: mainWindow.isDark ? mainWindow.darkTextColor : mainWindow.lightTextColor
        }


        MouseArea{
            anchors.fill: parent
            onClicked: {
                mainWindow.isDark = !mainWindow.isDark;
            }
        }
    }

    // Debug butonu
    Rectangle {
        id: debugButton
        width: 100
        height: 50
        color: "transparent"
        border.width: 2
        border.color: isDark ? darkBoxBorderColor : lightBoxBorderColor
        radius: 20
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 20
        anchors.left: togglerButton.right
        anchors.leftMargin: 20

        Text {
            font.family: interRegular.name
            text: "Debug Mode"
            font.pointSize: 12
            anchors.centerIn: parent
            color: isDark ? darkTextColor : lightTextColor
        }

        MouseArea {
                anchors.fill: parent
                onClicked: {
                    console.log("Debug button clicked"); // Debug için
                    if (!debugWindow) {
                        console.log("Creating debug window");
                        var component = Qt.createComponent("Debug.qml");
                        if (component.status === Component.Ready) {
                            debugWindow = component.createObject(mainWindow);
                            console.log("Debug window created successfully");
                        } else {
                            console.error("Error loading component:", component.errorString());
                        }
                    }
                    if (debugWindow) {
                        debugWindow.visible = !debugWindow.visible;
                        console.log("Debug window visibility toggled:", debugWindow.visible);
                    }
                }
            }
    }

    Connections {
            target: canReceiver
            function onCanMotorDataReceived(frameId, length, dataHex) {
                var rawValue = parseInt(dataHex, 16) - 15;
                road.speed =(rawValue < 0) ? 0 :  rawValue * 30 / 200;
                speedText.text = (rawValue < 0) ? 0 : rawValue
                if(rawValue <= 0){
                    ready.visible = true;
                }
                else{
                    ready.visible = false;
                }
                if (debugWindow) {
                   debugWindow.addCanMessage(frameId, length, dataHex)
                }
            }
            function onCanDistanceDataReceived(frameId, length, dataHex){
                var rawValue = parseInt(dataHex, 16)
                if(rawValue <= 15)
                {
                    if(rawValue <= 5){
                        distanceWarning.border.color = 'red';
                        distanceWarning.border.width = 3;
                    }
                    else if(rawValue <= 10){
                        distanceWarning.border.color = 'yellow';
                        distanceWarning.border.width = 2;
                    }
                    else{
                        distanceWarning.border.color = mainWindow.lightAccent;
                        distanceWarning.border.width = 1;
                    }


                    distanceWarning.visible = true;
                }
                else distanceWarning.visible = false;
                distanceText.text = (rawValue < 0) ? 0 : rawValue
                if (debugWindow) {
                   debugWindow.addCanMessage(frameId, length, dataHex)
                }
            }
            function onCanTempDataReceived(frameId, length, dataHex){
                var rawValue = parseInt(dataHex, 16) / 10
                tempText.text = rawValue + "°C"
                if (debugWindow) {
                   debugWindow.addCanMessage(frameId, length, dataHex)
                }
            }

            function onCanLeftSignalDataReceived(frameId, length, dataHex){
                console.log("selamunaleykum")
                var rawValue = parseInt(dataHex, 16);
                road.leftSignalOpen = rawValue
                if (debugWindow) {
                   debugWindow.addCanMessage(frameId, length, dataHex)
                }
            }
            function onCanRightSignalDataReceived(frameId, length, dataHex){
                console.log("selamunaleykum")
                var rawValue = parseInt(dataHex, 16);
                road.rightSignalOpen = rawValue
                if (debugWindow) {
                   debugWindow.addCanMessage(frameId, length, dataHex)
                }
            }
            function onCanBreakSignalDataReceived(frameId, length, dataHex){
                var rawValue = parseInt(dataHex, 16)
                road.breakSignalOpen = rawValue
                if(rawValue){
                    tempAndDateBox.border.color = "red"
                }
                else{
                    tempAndDateBox.border.color = mainWindow.lightAccent
                }
                if (debugWindow) {
                   debugWindow.addCanMessage(frameId, length, dataHex)
                }
            }

    }

    Component.onCompleted: {
        leftBox.height = 0
        rightBox.height = 0
        tempAndDateBox.width = 0
        speedText.visible = false;
        speedTextInfo.visible = false;
        wrapper.visible = false;
        tempText.visible = false;
        dateText.visible = false;
        batteryPercentage.visible = false;
        battery.visible = false;
        indicators.opacity = 0;

        fullSequence.start()
    }

    SequentialAnimation {
        id: fullSequence
        onStopped:{
            wrapper.visible = true;
            speedText.visible = true;
            speedTextInfo.visible = true;
            tempText.visible = true;
            dateText.visible = true;
            batteryPercentage.visible = true;
            battery.visible = true;
            mainWindow.isFinished = true;
        }

        PropertyAnimation {
            target: mainWindow
            property: "opacity"
            from: 0
            to: 1
            duration: 500
        }

        ScriptAction {
            script: {
                leftBox.visible = true;
                rightBox.visible = true;
                tempAndDateBox.visible = true
            }
        }

        ParallelAnimation {
            PropertyAnimation {
                target: leftBox
                property: "height"
                from: 0
                to: mainWindow.height*(0.4)
                duration: 500
            }
            PropertyAnimation {
                target: rightBox
                property: "height"
                from: 0
                to: mainWindow.height*(0.4)
                duration: 500
            }
            PropertyAnimation{
                target: tempAndDateBox
                property: "width"
                from: 0
                to: mainWindow.width*(0.2)
                duration: 500
            }
        }
        PropertyAnimation{
            target: indicators
            property: "opacity"
            from: 0
            to: 1
            duration: 500
        }
    }
}


