import QtQuick 2.0
import calamares.slideshow 1.0

Presentation {
    id: presentation
    titleColor: "#9b2335"
    textColor: "#16130f"
    fontFamily: "Noto Sans"
    property string wallpaper: "file:///usr/share/backgrounds/stradilabos/stradilabos-wallpaper-v3.png"
    property string appIcons: "file:///usr/local/share/icons/hicolor/scalable/apps/"
    property string themeIcons: "file:///usr/share/icons/StradiLab/scalable/"

    Timer {
        interval: 6500
        running: presentation.activatedInCalamares
        repeat: true
        onTriggered: presentation.goToNextSlide()
    }

    Slide {
        Rectangle { anchors.fill: parent; color: "#f6f4ef"; z: -2 }
        Image { anchors.fill: parent; source: presentation.wallpaper; fillMode: Image.PreserveAspectCrop; z: -1 }
        Rectangle {
            x: 38
            anchors.verticalCenter: parent.verticalCenter
            width: Math.min(500, parent.width * 0.58)
            height: 190
            radius: 20
            color: "#f6f4ef"
            opacity: 0.94
        }
        Column {
            x: 70
            anchors.verticalCenter: parent.verticalCenter
            width: Math.min(430, parent.width * 0.5)
            spacing: 16
            Text {
                width: parent.width
                text: qsTr("Benvenuto in StradiLabOS")
                color: "#9b2335"
                font.family: "Noto Sans"
                font.pixelSize: 34
                font.bold: true
                wrapMode: Text.WordWrap
            }
            Text {
                width: parent.width
                text: qsTr("Un ambiente semplice e leggero per studiare, creare e usare i servizi della scuola.")
                color: "#16130f"
                font.family: "Noto Sans"
                font.pixelSize: 21
                wrapMode: Text.WordWrap
            }
        }
    }

    Slide {
        Rectangle { anchors.fill: parent; color: "#f6f4ef"; z: -2 }
        Column {
            anchors.centerIn: parent
            width: parent.width - 80
            spacing: 28
            Text {
                width: parent.width
                text: qsTr("Un desktop coordinato, chiaro e immediato")
                color: "#9b2335"
                font.family: "Noto Sans"
                font.pixelSize: 30
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
            }
            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 26
                Image { width: 92; height: 92; source: presentation.themeIcons + "places/user-home.svg"; fillMode: Image.PreserveAspectFit }
                Image { width: 92; height: 92; source: presentation.themeIcons + "places/folder.svg"; fillMode: Image.PreserveAspectFit }
                Image { width: 92; height: 92; source: presentation.themeIcons + "devices/drive-harddisk.svg"; fillMode: Image.PreserveAspectFit }
                Image { width: 92; height: 92; source: presentation.themeIcons + "places/user-trash.svg"; fillMode: Image.PreserveAspectFit }
            }
            Text {
                width: parent.width
                text: qsTr("Sfondo e icone seguono la palette StradiLab: avorio, nero caldo, bordeaux e i cinque colori degli indirizzi.")
                color: "#16130f"
                font.family: "Noto Sans"
                font.pixelSize: 19
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
            }
        }
    }

    Slide {
        Rectangle { anchors.fill: parent; color: "#f6f4ef"; z: -2 }
        Column {
            anchors.centerIn: parent
            width: parent.width - 80
            spacing: 28
            Text {
                width: parent.width
                text: qsTr("La scuola a portata di clic")
                color: "#9b2335"
                font.family: "Noto Sans"
                font.pixelSize: 30
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
            }
            Row {
                anchors.horizontalCenter: parent.horizontalCenter
                spacing: 26
                Image { width: 92; height: 92; source: presentation.appIcons + "stradilabos.svg"; fillMode: Image.PreserveAspectFit }
                Image { width: 92; height: 92; source: presentation.appIcons + "istituto-stradivari.svg"; fillMode: Image.PreserveAspectFit }
                Image { width: 92; height: 92; source: presentation.appIcons + "mastercom.svg"; fillMode: Image.PreserveAspectFit }
                Image { width: 92; height: 92; source: presentation.appIcons + "stradilabos-workspace.svg"; fillMode: Image.PreserveAspectFit }
            }
            Text {
                width: parent.width
                text: qsTr("StradiLab, sito dell'Istituto, registro elettronico e Google Workspace saranno già raccolti in un unico ambiente. L'accesso Workspace è riservato al dominio @istitutostradivari.it.")
                color: "#16130f"
                font.family: "Noto Sans"
                font.pixelSize: 19
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
            }
        }
    }

    Slide {
        Rectangle { anchors.fill: parent; color: "#f6f4ef"; z: -2 }
        Column {
            anchors.centerIn: parent
            width: parent.width - 90
            spacing: 25
            Image {
                anchors.horizontalCenter: parent.horizontalCenter
                width: 112
                height: 112
                source: presentation.appIcons + "stradilabos-app-center.svg"
                fillMode: Image.PreserveAspectFit
            }
            Text {
                width: parent.width
                text: qsTr("Il sistema giusto per chi lo usa")
                color: "#9b2335"
                font.family: "Noto Sans"
                font.pixelSize: 30
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
            }
            Text {
                width: parent.width
                text: qsTr("Studente con il proprio indirizzo, Docente con tutti gli indirizzi, Segreteria oppure installazione base: StradiLabOS propone solo le raccolte utili al profilo scelto.")
                color: "#16130f"
                font.family: "Noto Sans"
                font.pixelSize: 19
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
            }
        }
    }

    function onActivate() {
        presentation.currentSlide = 0
    }

    function onLeave() {
    }
}
