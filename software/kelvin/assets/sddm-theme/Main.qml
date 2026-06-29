import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import SddmComponents 2.0

Rectangle {
    id: root

    readonly property color kelvinBlue:  "#A8D8EA"
    readonly property color kelvinDark:  "#2A2A2A"
    readonly property color kelvinIce:   "#5BA4CF"
    readonly property color kelvinWhite: "#F5F5F5"

    width:  Screen.width
    height: Screen.height

    // Deep background gradient
    gradient: Gradient {
        GradientStop { position: 0.0; color: "#1A1A2E" }
        GradientStop { position: 1.0; color: root.kelvinDark }
    }

    // ── Login card ─────────────────────────────────────────────────────────────

    Rectangle {
        anchors.centerIn: parent
        width:  440
        height: loginColumn.implicitHeight + 64
        radius: 16
        color:  Qt.rgba(0, 0, 0, 0.45)
        border.color: Qt.rgba(168/255, 216/255, 234/255, 0.25)
        border.width: 1

        ColumnLayout {
            id: loginColumn
            anchors {
                top:     parent.top
                left:    parent.left
                right:   parent.right
                margins: 36
                topMargin: 36
            }
            spacing: 16

            // Logo
            Text {
                Layout.alignment: Qt.AlignHCenter
                text: "❄"
                font.pixelSize: 42
                color: root.kelvinBlue
            }

            Text {
                Layout.alignment: Qt.AlignHCenter
                text: "K E L V I N"
                font.pixelSize: 22
                font.letterSpacing: 6
                color: root.kelvinBlue
            }

            Item { height: 4 }

            // User selector
            ComboBox {
                id: userCombo
                Layout.fillWidth: true
                model: userModel
                textRole: "name"
                currentIndex: userModel.lastIndex

                contentItem: Text {
                    leftPadding: 14
                    text:  userCombo.displayText
                    font.pixelSize: 14
                    color: root.kelvinWhite
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    radius: 8
                    color:  Qt.rgba(1, 1, 1, 0.07)
                    border.color: root.kelvinIce
                    border.width: 1
                }
                popup.background: Rectangle {
                    radius: 8
                    color:  "#1A1A2E"
                    border.color: root.kelvinIce
                    border.width: 1
                }
            }

            // Password field
            TextField {
                id: passwordField
                Layout.fillWidth: true
                echoMode:         TextInput.Password
                placeholderText:  TextConstants.password
                font.pixelSize:   14
                color:            root.kelvinWhite
                focus:            true

                background: Rectangle {
                    radius: 8
                    color:  Qt.rgba(1, 1, 1, 0.07)
                    border.color: passwordField.activeFocus ? root.kelvinBlue : root.kelvinIce
                    border.width: 1
                    Behavior on border.color { ColorAnimation { duration: 120 } }
                }

                Keys.onReturnPressed: doLogin()
            }

            // Error text
            Text {
                id: errorText
                Layout.alignment: Qt.AlignHCenter
                text:    ""
                color:   "#FF6B6B"
                font.pixelSize: 12
                visible: text.length > 0
            }

            // Login button
            Button {
                id: loginBtn
                Layout.fillWidth: true
                implicitHeight:   44
                text: TextConstants.login
                font.pixelSize: 14
                font.bold:      true

                contentItem: Text {
                    text:                loginBtn.text
                    font:                loginBtn.font
                    color:               root.kelvinDark
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment:   Text.AlignVCenter
                }
                background: Rectangle {
                    radius: 8
                    color:  loginBtn.hovered ? root.kelvinBlue : root.kelvinIce
                    Behavior on color { ColorAnimation { duration: 120 } }
                }
                onClicked: doLogin()
            }

            // Session selector
            ComboBox {
                id: sessionCombo
                Layout.fillWidth: true
                model:            sessionModel
                textRole:         "name"
                currentIndex:     sessionModel.lastIndex

                contentItem: Text {
                    leftPadding: 14
                    text:  sessionCombo.displayText
                    font.pixelSize: 12
                    color: Qt.rgba(1, 1, 1, 0.55)
                    verticalAlignment: Text.AlignVCenter
                }
                background: Rectangle {
                    radius: 8
                    color:  Qt.rgba(1, 1, 1, 0.04)
                    border.color: Qt.rgba(1, 1, 1, 0.15)
                    border.width: 1
                }
                popup.background: Rectangle {
                    radius: 8
                    color:  "#1A1A2E"
                    border.color: Qt.rgba(1, 1, 1, 0.2)
                    border.width: 1
                }
            }
        }
    }

    // ── Power buttons (bottom-right) ───────────────────────────────────────────

    Row {
        anchors.bottom:  parent.bottom
        anchors.right:   parent.right
        anchors.margins: 24
        spacing: 10

        Repeater {
            model: [
                { label: "Suspend",  action: function() { sddm.suspend()  }, enabled: sddm.canSuspend  },
                { label: "Shutdown", action: function() { sddm.powerOff() }, enabled: sddm.canPowerOff },
                { label: "Reboot",   action: function() { sddm.reboot()   }, enabled: sddm.canReboot   },
            ]
            delegate: Button {
                visible: modelData.enabled
                text:    modelData.label
                font.pixelSize: 12

                contentItem: Text {
                    text:  parent.text
                    font:  parent.font
                    color: root.kelvinWhite
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment:   Text.AlignVCenter
                }
                background: Rectangle {
                    radius: 6
                    color:  parent.hovered ? Qt.rgba(1,1,1,0.12) : Qt.rgba(1,1,1,0.06)
                    Behavior on color { ColorAnimation { duration: 100 } }
                }
                onClicked: modelData.action()
            }
        }
    }

    // ── Logic ──────────────────────────────────────────────────────────────────

    function doLogin() {
        errorText.text = ""
        sddm.login(
            userCombo.currentText,
            passwordField.text,
            sessionCombo.currentIndex
        )
    }

    Connections {
        target: sddm
        function onLoginFailed() {
            errorText.text    = TextConstants.loginFailed
            passwordField.text = ""
            passwordField.forceActiveFocus()
        }
    }
}
