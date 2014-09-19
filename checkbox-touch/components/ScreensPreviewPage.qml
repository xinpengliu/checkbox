/*
 * This file is part of Checkbox
 *
 * Copyright 2014 Canonical Ltd.
 *
 * Authors:
 * - Maciej Kisielewski <maciej.kisielewski@canonical.com>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; version 3.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

import QtQuick 2.0
import Ubuntu.Components 1.1
import QtQuick.Layouts 1.1

Page {
    id: screensPreviewPage
    title: i18n.tr("Screens preview")
    visible: false

    Flickable {
        anchors.fill: parent
        contentHeight: column.height
        contentWidth: column.width
        ColumnLayout {
            id: column
            spacing: units.gu(3)
            anchors {
                top: parent.top
                left: parent.left
                right: parent.right
                margins: units.gu(1)
            }
            Label {
                fontSize: "x-large"
                Layout.alignment: Qt.AlignHCenter
                Layout.fillWidth: true
                wrapMode: Text.WrapAtWordBoundaryOrAnywhere
                text: i18n.tr("This is a developer screen that allows you to preview particular part of the app.\nSelect which screen to preview")
            }
            Button {
                text: i18n.tr("Welcome page")
                onClicked: {
                    var newPage = Qt.createComponent(Qt.resolvedUrl("WelcomePage.qml")).createObject();
                    newPage.welcomeText = i18n.tr("This application is under development.\nThere is nothing beyond this screen yet");
                    newPage.startTestingTriggered.connect(function() { pageStack.pop() })
                    pageStack.push(newPage);
                }
            }
            Button {
                text: i18n.tr("Automated test page")
                onClicked: {
                    var newPage = Qt.createComponent(Qt.resolvedUrl("AutomatedTestPage.qml")).createObject();
                    newPage.testName = "memory/info";
                    newPage.testDescription = "This test checks the amount of memory which is reporting \
in meminfo against the size of the memory modules detected by DMI."
                    pageStack.push(newPage);
                }
            }
            Button {
                text: i18n.tr("User-Interact-Verify test page")
                onClicked: {
                    var newPage = Qt.createComponent(Qt.resolvedUrl("InteractIntroPage.qml")).createObject();
                    newPage.testName = "Headphones playback";
                    newPage.testDescription = "This test will check that headphones connector works correctly.\n\
STEPS:\n\
  1. Connect a pair of headphones to your audio device\n\
  2. Click the Test button to play a sound to your audio device";
                    newPage.testStarted.connect(userInteractVerifyTestStarted);
                    newPage.testSkipped.connect(skipTest);
                    //Triggering of timer should change the state on intro page
                    interactIntroTimer.triggered.connect(newPage.stopActivity)
                    pageStack.push(newPage);
                }
            }
            Button {
                objectName: "resumeSessionPageButton"
                text: i18n.tr("Resume session page")
                onClicked: {
                    var newPage = Qt.createComponent(Qt.resolvedUrl("ResumeSessionPage.qml")).createObject();
                    newPage.resumeText = "Checkbox did not finish completely.\n\n\
Do you want to rerun the last test, continue to the next test, or restart from the beginning?";
                    newPage.rerunLast.connect(function() {
                        console.log("Rerun last test selected");
                        replaceOnPageStack(screensPreviewPage);
                    });
                    newPage.continueSession.connect(function() {
                        console.log("Continue session selected");
                        replaceOnPageStack(screensPreviewPage);
                    });
                    newPage.restartSession.connect(function() {
                        console.log("Restart session selected");
                        replaceOnPageStack(screensPreviewPage);
                    });
                    replaceOnPageStack(newPage);
                }
            }
            Button {
                objectName: "manualIntroPageButton"
                text: i18n.tr("Manual test page")
                onClicked: {
                    var newPage = Qt.createComponent(Qt.resolvedUrl("ManualIntroPage.qml")).createObject();
                    newPage.testName = "Volume Down Key";
                    newPage.testDescription = "PURPOSE:\n    This test will test the volume down key\n\
STEPS:\n    1. Click the volume down key of your phone"
                    newPage.testSkipped.connect(skipTest);
                    newPage.continueClicked.connect(function() {
                        var verificationPage = Qt.createComponent(Qt.resolvedUrl("TestVerificationPage.qml")).createObject();
                        verificationPage.testName = "Volume Down Key"
                        verificationPage.verificationDescription = "Did the volume go down when you pressed the volume down key?"
                        verificationPage.verificationDone.connect(verificationDone);
                        verificationPage.testSkipped.connect(skipTest);
                        pageStack.push(verificationPage);
                    });
                    pageStack.push(newPage);
                }
            }
            Row {
                spacing: units.gu(3)
                Button {
                    text: i18n.tr("User-Interact test page")
                    onClicked: {
                        var newPage = Qt.createComponent(Qt.resolvedUrl("InteractIntroPage.qml")).createObject();
                        newPage.testName = "Finger Expand";
                        newPage.testDescription = "PURPOSE:\n    Check touchscreen expand gesture for zoom\n\
    STEPS:\n\
      1. Press the Test button\n\
      2. Using 2 fingers, resize the blue square until it turns green, then release it.";
                        newPage.testSkipped.connect(skipTest);
                        newPage.testStarted.connect(userInteractTestStarted);
                        interactIntroTimer.triggered.connect(newPage.stopActivity)
                        pageStack.push(newPage);
                    }
                }
                Label {
                    text: "Should pass?"
                }

                Switch {
                    id: userInteractShouldFail
                }
            }
            Button {
                id: verificationPageButton
                text: i18n.tr("Test verification page")
                onClicked: {
                    interactIntroTimer.triggered.disconnect(verificationPageButton.clicked);
                    var newPage = Qt.createComponent(Qt.resolvedUrl("TestVerificationPage.qml")).createObject();
                    newPage.testName = "Headphones playback";
                    newPage.verificationDescription = "Did you hear a sound through the headphones and did the sound \
play without any distortion, clicks or other strange noises from your headphones?";
                    newPage.testSkipped.connect(skipTest);
                    newPage.verificationDone.connect(verificationDone);
                    pageStack.push(newPage);
                }
            }
            Button {
                text: i18n.tr("Results page")
                onClicked: {
                    var newPage = Qt.createComponent(Qt.resolvedUrl("ResultsPage.qml")).createObject();
                    newPage.results = {"totalPassed": 15, "totalFailed": 3, "totalSkipped": 5};
                    pageStack.push(newPage);
                }
            }
            LatchButton {
                objectName: "latchButton"
                text: "Latch button"
            }
        }
    }
    /*
      This timer emulates running test.
    */
    Timer {
        id: interactIntroTimer
        interval: 2000; running: false; repeat: false
    }
    function skipTest() {
        console.log("Test skipped");
        unwindStack();
    }
    function replaceOnPageStack(newPage) {
        pageStack.pop();
        pageStack.push(newPage);
    }
    function userInteractVerifyTestStarted() {
        interactIntroTimer.triggered.connect(verificationPageButton.clicked);
        interactIntroTimer.start();
    }
    function showUserInteractSummaryPage() {
        interactIntroTimer.triggered.disconnect(showUserInteractSummaryPage)
        var newPage = Qt.createComponent(Qt.resolvedUrl("UserInteractSummaryPage.qml")).createObject();
        newPage.testName = "Finger Expand";
        newPage.passed = userInteractShouldFail.checked;
        newPage.endOfTest.connect(verificationDone);
        newPage.testSkipped.connect(skipTest);
        pageStack.push(newPage);
    }
    function userInteractTestStarted() {
        interactIntroTimer.triggered.connect(showUserInteractSummaryPage);
        interactIntroTimer.start();
    }
    function unwindStack() {
        /*
            This function pops pages of from the stack until we're on screensPreviewPage
            Ordinary pageStack.pop() would'n work as there might be 1 or 2 pages on stack
        */
        while(pageStack.currentPage!=screensPreviewPage) {
            pageStack.pop();
        }
    }
    function verificationDone(result) {
        console.log("verificationDone called with result: " + result);
        unwindStack();
    }
}