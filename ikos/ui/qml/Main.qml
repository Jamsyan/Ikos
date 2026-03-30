import QtQuick 2.15
import QtQuick.Layouts 1.15
import QtQuick.Window 2.15

Window {
    id: root
    visible: true
    title: "Ikos - 智能知识构建系统"
    width: 1280
    height: 800
    minimumWidth: 800
    minimumHeight: 600

    // 颜色主题
    readonly property color primaryColor: "#3498db"
    readonly property color primaryDark: "#2980b9"
    readonly property color successColor: "#27ae60"
    readonly property color errorColor: "#e74c3c"
    readonly property color backgroundColor: "#1a1a2e"
    readonly property color panelColor: "#16213e"
    readonly property color textColor: "#ffffff"
    readonly property color textMutedColor: "#a0a0a0"

    // 自定义信号 - 与 Python 通信
    signal startTask(string userInput)
    signal requestInitializePipeline()
    signal windowClosing()

    // 背景 - 渐变效果
    Rectangle {
        anchors.fill: parent
        color: root.backgroundColor

        Gradient {
            id: bgGradient
            GradientStop { position: 0.0; color: "#0f0c29" }
            GradientStop { position: 0.5; color: "#302b63" }
            GradientStop { position: 1.0; color: "#24243e" }
        }
    }

    // 主布局
    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 15
        spacing: 15

        // 标题栏
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 60
            color: "transparent"

            Text {
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                text: "Ikos - Intelligent Knowledge Building System"
                font.pixelSize: 24
                font.bold: true
                color: root.textColor
            }

            // 状态指示器
            Row {
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                spacing: 8

                Rectangle {
                    width: 12
                    height: 12
                    radius: 6
                    color: statusColor
                    Behavior on color { ColorAnimation { duration: 300 } }
                }

                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: statusText
                    font.pixelSize: 14
                    color: root.textMutedColor
                }
            }
        }

        // 分割器 - 输入和输出区域
        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 10

            // 输入面板
            InputPanel {
                id: inputPanel
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredHeight: 200

                onStartTaskRequested: {
                    root.startTask(text)
                }
            }

            // 输出面板
            OutputPanel {
                id: outputPanel
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredHeight: 400

                onLogCleared: {
                    // 可以添加清理逻辑
                }
            }
        }
    }

    // 状态栏对象
    property string statusText: "就绪"
    property color statusColor: root.successColor

    function setReady() {
        statusText = "就绪"
        statusColor = root.successColor
    }

    function setRunning() {
        statusText = "任务执行中..."
        statusColor = root.primaryColor
    }

    function setError() {
        statusText = "任务失败"
        statusColor = root.errorColor
    }

    function setSuccess() {
        statusText = "任务完成"
        statusColor = root.successColor
    }

    // 连接 Python 信号
    Connections {
        target: pythonBridge

        function onTaskStarted() {
            setRunning()
            inputPanel.setBusy(true)
        }

        function onTaskFinished(result) {
            setSuccess()
            inputPanel.setBusy(false)
            outputPanel.appendLog("\n✅ 任务执行成功")
            
            if (result.output_files) {
                outputPanel.appendLog("\n输出文件:")
                for (var i = 0; i < result.output_files.length; i++) {
                    var file = result.output_files[i]
                    outputPanel.appendLog(
                        "  - " + file.filename + " (" + file.path + ")"
                    )
                }
            }
        }

        function onTaskError(error) {
            setError()
            inputPanel.setBusy(false)
            outputPanel.appendLog("\n❌ 错误：" + error)
        }

        function onPipelineInitialized() {
            outputPanel.appendLog("管道初始化完成")
        }

        function onPipelineInitError(error) {
            outputPanel.appendLog("管道初始化失败：" + error)
            inputPanel.setBusy(false)
        }

        function onLogMessage(message) {
            outputPanel.appendLog(message)
        }
    }
}
