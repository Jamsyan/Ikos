import QtQuick 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "transparent"

    // 自定义信号
    signal startTaskRequested(string text)

    // 颜色属性
    property color primaryColor: "#3498db"
    property color primaryDark: "#2980b9"
    property color panelBgColor: Qt.rgba(22/255, 33/255, 62/255, 0.9)
    property color textColor: "#ffffff"
    property color textMutedColor: "#a0a0a0"
    property bool busyState: false

    // 背景
    Rectangle {
        anchors.fill: parent
        color: root.panelBgColor
        radius: 10
        border.color: root.primaryColor
        border.width: 1
    }

    // 内容布局
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 15

        // 标题
        Text {
            text: "输入查询："
            font.pixelSize: 18
            font.bold: true
            color: root.textColor
        }

        // 输入框 - 使用 Rectangle + TextInput
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 50
            color: inputField.activeFocus ? "rgba(52, 152, 219, 0.2)" : "rgba(255, 255, 255, 0.05)"
            radius: 8
            border.color: inputField.activeFocus ? root.primaryColor : "transparent"
            border.width: 2

            Behavior on color { ColorAnimation { duration: 200 } }
            Behavior on border.color { ColorAnimation { duration: 200 } }

            TextInput {
                id: inputField
                anchors.fill: parent
                anchors.leftMargin: 15
                anchors.rightMargin: 15
                color: root.textColor
                font.pixelSize: 14
                verticalAlignment: Text.AlignVCenter
                enabled: !root.busyState

                Text {
                    text: "例如：量子力学基础概念、傅里叶变换的数学原理..."
                    color: root.textMutedColor
                    font.pixelSize: 14
                    anchors.fill: parent
                    anchors.leftMargin: 15
                    visible: inputField.text === "" && !inputField.activeFocus
                }

                Keys.onPressed: {
                    if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
                        if (inputField.text.trim() !== "") {
                            root.startTaskRequested(inputField.text.trim())
                            event.accepted = true
                        }
                    }
                }
            }
        }

        // 按钮
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 50
            color: root.busyState ? "#505050" : (mouseArea.pressed ? root.primaryDark : root.primaryColor)
            radius: 8

            Behavior on color { ColorAnimation { duration: 150 } }

            Text {
                anchors.centerIn: parent
                text: root.busyState ? "执行中..." : "开始执行"
                font.pixelSize: 16
                font.bold: true
                color: root.busyState ? "#808080" : "#ffffff"
            }

            MouseArea {
                id: mouseArea
                anchors.fill: parent
                enabled: !root.busyState
                cursorShape: Qt.PointingHandCursor

                onClicked: {
                    if (inputField.text.trim() !== "") {
                        root.startTaskRequested(inputField.text.trim())
                    }
                }
            }
        }
    }

    // 公共方法
    function setBusy(busy) {
        root.busyState = busy
        if (busy) {
            inputField.enabled = false
        } else {
            inputField.enabled = true
            inputField.focus = true
        }
    }

    function clearInput() {
        inputField.text = ""
    }

    function getInputText() {
        return inputField.text.trim()
    }
}
