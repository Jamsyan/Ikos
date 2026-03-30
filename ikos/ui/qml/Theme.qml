/* QML 样式配置文件 - 主题和样式 */

pragma Singleton
import QtQuick 2.15

QtObject {
    // 主主题色
    readonly property color primary: "#3498db"
    readonly property color primaryDark: "#2980b9"
    readonly property color primaryLight: "#5dade2"
    
    // 功能色
    readonly property color success: "#27ae60"
    readonly property color warning: "#f39c12"
    readonly property color error: "#e74c3c"
    readonly property color info: "#3498db"
    
    // 背景色
    readonly property color backgroundDark: "#0f0c29"
    readonly property color backgroundMid: "#1a1a2e"
    readonly property color panelBg: "#16213e"
    readonly property color cardBg: "#1f4068"
    
    // 文本色
    readonly property color textPrimary: "#ffffff"
    readonly property color textSecondary: "#a0a0a0"
    readonly property color textMuted: "#606060"
    
    // 边框色
    readonly property color borderPrimary: "#3498db"
    readonly property color borderMuted: "#2c3e50"
    
    // 阴影色
    readonly property color shadow: "rgba(0, 0, 0, 0.3)"
    
    // 字体配置
    readonly property font defaultFont: Qt.font({
        family: "Segoe UI",
        pixelSize: 14,
        weight: Font.Normal
    })
    
    readonly property font titleFont: Qt.font({
        family: "Segoe UI",
        pixelSize: 24,
        weight: Font.Bold
    })
    
    readonly property font headingFont: Qt.font({
        family: "Segoe UI",
        pixelSize: 18,
        weight: Font.Bold
    })
    
    readonly property font monoFont: Qt.font({
        family: "Consolas",
        pixelSize: 13,
        weight: Font.Normal
    })
    
    // 间距配置
    readonly property real spacingXS: 4
    readonly property real spacingSM: 8
    readonly property real spacingMD: 15
    readonly property real spacingLG: 24
    readonly property real spacingXL: 32
    
    // 圆角配置
    readonly property real radiusSM: 4
    readonly property real radiusMD: 8
    readonly property real radiusLG: 12
    readonly property real radiusXL: 20
    
    // 动画时长
    readonly property int animationFast: 150
    readonly property int animationNormal: 300
    readonly property int animationSlow: 500
    
    // 阴影效果
    readonly property var shadowEffect: [
        {
            "color": shadow,
            "offset": Qt.point(0, 2),
            "radius": 8
        }
    ]
}
