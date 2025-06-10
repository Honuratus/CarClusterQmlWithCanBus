import QtQuick 2.15

Rectangle {
    id: road
    width: parent.width * 0.5
    height: parent.height - 500
    anchors.horizontalCenter: parent.horizontalCenter
    anchors.bottom: parent.bottom
    color: "transparent"
    clip: true
    z: -1

    property bool isMoving: true
    property real speed: 0
    property real maxSpeed: 30
    property int railCount: 10
    property real scrollSpeed: speed * 0.001

    // Keyboard control properties
    property bool keyPressed: false
    property real acceleration: 0.1
    property real deceleration: 0.3
    property real friction: 0.05

    property bool leftSignalOpen: false
    property bool rightSignalOpen: false
    property bool breakSignalOpen : false

    // Simplified perspective calculations
    function leftEdge(y) {
        return width * 0.57 + (y / height) * width * 0.17
    }

    function rightEdge(y) {
        return width * 0.42 - (y / height) * width * 0.17
    }

    // Static road background
    Image {
        id: staticRoad
        anchors.fill: parent
        source: "images/road(2).png"
        z: 0
    }

    // Rail container
    Item {
        id: railsContainer
        anchors.fill: parent
        z: 1
        height: parent.height * 1.5  // Daha fazla buffer

        property real railWidth: road.width * 0.018
        property real railHeight: railWidth * 1.5
        property real railSpacing: height / railCount  // Sabit aralık

        // Left rails
        Repeater {
            model: railCount * 2  // Daha fazla rail ekleyerek kesintisiz görünüm
            delegate: Image {
                source: "images/rail2.png"
                width: railsContainer.railWidth
                height: railsContainer.railHeight
                z: Math.floor(y / height * 10)

                property real baseY: index * railsContainer.railSpacing
                property real yPos: (baseY - (scrollSpeed * 20)) % (railsContainer.railSpacing * railCount)

                x: leftEdge(yPos + railsContainer.y) - width / 2
                y: yPos
                scale: 0.8 + ((yPos + railsContainer.y) / road.height) * 0.4
                opacity: {
                    var visibleY = yPos + railsContainer.y
                    if (visibleY < 0) return visibleY / railsContainer.railHeight + 1
                    if (visibleY > road.height - railsContainer.railHeight) return 1 - (visibleY - (road.height - railsContainer.railHeight)) / railsContainer.railHeight
                    return 1
                }

                Timer {
                    interval: 16
                    running: road.isMoving
                    repeat: true
                    onTriggered: {
                        parent.yPos = (parent.yPos + road.scrollSpeed) % (railsContainer.railSpacing * railCount)
                        parent.y = parent.yPos
                        parent.x = leftEdge(parent.yPos + railsContainer.y) - width / 2
                        parent.scale = 0.8 + ((parent.yPos + railsContainer.y) / road.height) * 0.4
                    }
                }
            }
        }

        // Right rails
        Repeater {
            model: railCount * 2  // Daha fazla rail ekleyerek kesintisiz görünüm
            delegate: Image {
                source: "images/rail.png"
                width: railsContainer.railWidth
                height: railsContainer.railHeight
                z: Math.floor(y / height * 10)

                property real baseY: index * railsContainer.railSpacing
                property real yPos: (baseY - (scrollSpeed * 20)) % (railsContainer.railSpacing * railCount)

                x: rightEdge(yPos + railsContainer.y) - width / 2
                y: yPos
                scale: 0.8 + ((yPos + railsContainer.y) / road.height) * 0.4
                opacity: {
                    var visibleY = yPos + railsContainer.y
                    if (visibleY < 0) return visibleY / railsContainer.railHeight + 1
                    if (visibleY > road.height - railsContainer.railHeight) return 1 - (visibleY - (road.height - railsContainer.railHeight)) / railsContainer.railHeight
                    return 1
                }

                Timer {
                    interval: 16
                    running: road.isMoving
                    repeat: true
                    onTriggered: {
                        parent.yPos = (parent.yPos + road.scrollSpeed) % (railsContainer.railSpacing * railCount)
                        parent.y = parent.yPos
                        parent.x = rightEdge(parent.yPos + railsContainer.y) - width / 2
                        parent.scale = 0.8 + ((parent.yPos + railsContainer.y) / road.height) * 0.4
                    }
                }
            }
        }
    }

    // Car
    Image {
        id: car
        source: "images/car.png"
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.leftMargin: 50
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 25
        width: road.width * 0.4  // Genişliği biraz daralttım
        height: road.height * 0.6  // Yüksekliği biraz artırdım
        fillMode: Image.PreserveAspectFit
        z: 2
        Image {
            id: leftSignal
            width: car.width
            height: car.height
            visible: false
            source: "images/leftsignal.png"
            fillMode: Image.PreserveAspectFit
            z: 3
            Timer {
                id: leftSignalTimer
                interval: 300
                running: road.leftSignalOpen
                repeat: true
                onTriggered: {
                    leftSignal.visible = !leftSignal.visible
                }
                onRunningChanged: {
                    if(leftSignalTimer.running == false) leftSignal.visible = false;
                }
            }
        }

        Image{
            id: rightSignal
            width: car.width
            height: car.height
            visible: false
            source: "images/rightsignal.png"
            fillMode: Image.PreserveAspectFit
            z: 3
            Timer {
                id: rightSignalTimer
                interval: 300
                running: road.rightSignalOpen
                repeat: true
                onTriggered: {
                    rightSignal.visible = !rightSignal.visible
                }
                onRunningChanged: {
                    if(rightSignalTimer.running == false) rightSignal.visible = false;
                }
            }
        }

        Image{
            id: breakSignal
            width: car.width
            height: car.height
            visible: breakSignalOpen
            source: "images/break.png"
            fillMode: Image.PreserveAspectFit
            z: 3
        }

        // Perspektif için dönüşüm ayarları
        transform: [
            Rotation {
                origin.x: car.width / 2
                origin.y: car.height
                axis { x: 1; y: 0; z: 0 }
                angle: -10  // Arabayı hafifçe öne eğiyoruz (3D efekti için)
            },
            Scale {
                origin.x: car.width / 2
                origin.y: car.height
                xScale: 1 + road.speed / road.maxSpeed * 0.1  // Yatay ölçek
                yScale: 1 + road.speed / road.maxSpeed * 0.2  // Dikey ölçek (daha fazla)
            }
        ]

        // Hız efekti için ekstra ölçeklendirme
        scale:startIntroAnimation.running ? 0 : 1 + road.speed / road.maxSpeed * 0.1
        Behavior on scale {
            NumberAnimation { duration: 100 }
        }
    }

    // Speed control timer
    Timer {
        interval: 16
        running: true
        repeat: true
        onTriggered: {
            if (!keyPressed && speed > 0) {
                speed = Math.max(0, speed - friction)
            }
            scrollSpeed = speed * 0.5
        }
    }
    Component.onCompleted: {
        // Rails opacity başta sıfır olsun
        let leftRails = railsContainer.children[0].children
        let rightRails = railsContainer.children[1].children
        for (var i = 0; i < leftRails.length; i++) leftRails[i].opacity = 0;
        for (let i = 0; i < rightRails.length; i++) rightRails[i].opacity = 0;
        car.opacity = 0;
        staticRoad.opacity = 0
        railsContainer.opacity = 0
    }

    Connections {
        target: mainWindow
        onIsFinishedChanged: {
            if(mainWindow.isFinished) {
                startIntroAnimation.start()
            }
        }
    }


    SequentialAnimation {
        id: startIntroAnimation
        running: false
        PropertyAnimation {
            target: staticRoad
            property: "opacity"
            from: 0
            to: 1
            duration: 500
        }

        PropertyAnimation {
            target: railsContainer
            property: "opacity"
            from: 0
            to: 1
            duration: 500
        }

        PauseAnimation { duration: railsContainer.children[0].children.length * 80 }
        PropertyAnimation {
            target: car
            property: "opacity"
            from: 0.0
            to: 1
            duration: 500
        }
    }
}
