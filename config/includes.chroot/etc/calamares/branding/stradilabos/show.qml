import QtQuick 2.0
import calamares.slideshow 1.0

Presentation {
    id: presentation

    Timer {
        interval: 7000
        running: presentation.activatedInCalamares
        repeat: true
        onTriggered: presentation.goToNextSlide()
    }

    Slide {
        centeredText: qsTr("StradilabOS rende semplici e immediati gli strumenti digitali della scuola.")
    }

    Slide {
        centeredText: qsTr("Al primo avvio potrai scegliere l'indirizzo di studio e le raccolte di applicazioni più utili.")
    }

    Slide {
        centeredText: qsTr("Google Workspace, registro elettronico e servizi StradiLab saranno già a portata di clic.")
    }

    function onActivate() {
        presentation.currentSlide = 0
    }

    function onLeave() {
    }
}
