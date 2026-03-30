import QtQuick 2.15
import QtQuick.Layouts 1.15

Rectangle {
    id: root
    Layout.fillWidth: true
    Layout.fillHeight: true
    color: "transparent"

    // 自定义信号
    signal logCleared()

    // 颜色属性
    property color primaryColor: "#3498db"
    property color panelBgColor: Qt.rgba(22/255, 33/255, 62/255, 0.9)
    property color textColor: "#ffffff"
    property color textMutedColor: "#a0a0a0"
    property color logColor: "#00ff00"
    property color errorColor: "#ff6b6b"
    property color successColor: "#51cf66"

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

        // 标题栏
        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Text {
                text: "输出日志："
                font.pixelSize: 16
                font.bold: true
                color: root.textColor
            }

            // 清空按钮
            Rectangle {
                Layout.preferredWidth: 80
                Layout.preferredHeight: 30
                color: clearMouse.pressed ? "#c0392b" : "#e74c3c"
                radius: 6

                Behavior on color { ColorAnimation { duration: 150 } }

                Text {
                    anchors.centerIn: parent
                    text: "清空"
                    font.pixelSize: 12
                    color: "#ffffff"
                }

                MouseArea {
                    id: clearMouse
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        logModel.clear()
                        root.logCleared()
                    }
                }
            }

            Item { Layout.fillWidth: true }
        }

        // 日志显示区域 - 使用 ListView
        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "transparent"
            clip: true

            // 背景
            Rectangle {
                anchors.fill: parent
                color: Qt.rgba(0, 0, 0, 0.2)
                radius: 5
            }

            ListView {
                id: logView
                anchors.fill: parent
                anchors.margins: 10
                model: logModel
                spacing: 4
                clip: true

                // 自动滚动到底部
                onCountChanged: {
                    if (count > 0) {
                        positionViewAtEnd()
                    }
                }

                // 滚动条 - 简单实现
                Rectangle {
                    width: 10
                    height: logView.height
                    anchors.right: parent.right
                    color: "#202020"
                    radius: 5
                    
                    Rectangle {
                        width: parent.width - 2
                        height: Math.max(30, logView.height / Math.max(1, logModel.count) * 5)
                        color: "#505050"
                        radius: 3
                        anchors.horizontalCenter: parent.horizontalCenter
                    }
                }

                // 项的动画
                add: Transition {
                    NumberAnimation {
                        properties: "opacity"
                        from: 0
                        to: 1.0
                        duration: 200
                    }
                }

                delegate: logDelegate
            }
        }
    }

    // 日志数据模型
    ListModel {
        id: logModel
    }

    // 公共方法
    function appendLog(message) {
        var now = new Date()
        var timestamp = now.toLocaleTimeString("zh-CN", "hh:mm:ss")
        logModel.append({
            timestamp: timestamp,
            message: message,
            type: "info"
        })
    }

    function appendError(message) {
        var now = new Date()
        var timestamp = now.toLocaleTimeString("zh-CN", "hh:mm:ss")
        logModel.append({
            timestamp: timestamp,
            message: message,
            type: "error"
        })
    }

    function appendSuccess(message) {
        var now = new Date()
        var timestamp = now.toLocaleTimeString("zh-CN", "hh:mm:ss")
        logModel.append({
            timestamp: timestamp,
            message: message,
            type: "success"
        })
    }

    function clearLog() {
        logModel.clear()
    }

    // 日志项代理
    Component {
        id: logDelegate

        RowLayout {
            width: logView.width - 20
            spacing: 8

            // 时间戳
            Text {
                text: "[" + model.timestamp + "]"
                font.pixelSize: 11
                font.family: "Consolas"
                color: root.textMutedColor
                Layout.preferredWidth: 80
            }

            // 日志内容
            Text {
                text: model.message
                font.pixelSize: 13
                font.family: "Consolas"
                color: {
                    if (model.type === "error") return root.errorColor
                    if (model.type === "success") return root.successColor
                    return root.logColor
                }
                wrapMode: Text.Wrap
                Layout.fillWidth: true
            }
        }
    }
}
