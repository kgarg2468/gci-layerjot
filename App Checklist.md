**CLABSI AR Glasses \- Unity Android App Build Checklist**

Project Setup

* Create new Unity project (3D)  
* Set build target to Android  
* Import XREAL SDK (NRSDK) into Unity  
* Configure XREAL glasses permissions (camera, microphone, USB)  
* Set up Android manifest with required permissions  
* Test basic XREAL glasses connection and display output

Home Page (UC-01, UC-12)

* Design home screen UI with app logo and name  
* Add "Procedures" button  
* Add "Procedure Log" button  
* Add "Settings" button  
* Add "Exit" button  
* Implement exit functionality

Navigation System (UC-04)

* Implement voice input listener for page navigation  
* Map voice commands to pages ("Home", "Procedures", "Settings", "Exit")  
* Add fallback tap/gesture navigation

Procedures Page (UC-02)

* Design Procedures page UI  
* Add "Insert" button  
* Add "Maintenance" button  
* Add "Remove" button

Checklist System (Core \- applies to UC-13 through UC-30)

* Build reusable step-by-step checklist UI component  
* Implement step progression logic (one step at a time)  
* Implement voice command to advance steps ("Next", "Done")  
* Implement tap input to advance steps  
* Highlight current active step  
* Show step completion status (checked/unchecked)  
* Block skipping steps (enforce order)

Insert Procedure Checklist (UC-13 to UC-20)

* Create insertion checklist data (steps in order)  
* Sterile field setup verification prompt  
* Hand hygiene reminder prompt  
* Site prep step  
* Gloving step  
* Draping step  
* Catheter placement step  
* "Line inserted" voice confirmation trigger  
* Dressing application verification prompt  
* Completion screen with confirmation  
* Save AI log on completion

Maintenance Procedure Checklist (UC-21 to UC-25)

* Create maintenance checklist data (steps in order)  
* Dressing condition inspection prompt  
* Hand hygiene step  
* Dressing change step  
* Line flush step  
* Site inspection step  
* Completion screen with confirmation  
* Save AI log on completion

Remove Procedure Checklist (UC-26 to UC-30)

* Create removal checklist data (steps in order)  
* Hand hygiene step  
* Clamp line step  
* Remove catheter step  
* Apply pressure step  
* Dress site step  
* "Line removed" voice confirmation trigger  
* Completion screen with confirmation  
* Save AI log on completion

Audio Prompts (UC-05)

* Integrate text-to-speech (TTS) for reading steps aloud  
* Trigger TTS automatically when a new step is displayed  
* Allow user to mute/unmute audio prompts

AI Assistant (UC-06, UC-07)

* Set up voice-to-text input pipeline for user questions  
* Integrate AI model/API for conversational responses  
* Feed AI domain knowledge on sterile technique and CLABSI prevention  
* Implement real-time safety alerts (missed steps, risk flags)  
* Display AI alerts as AR overlay notifications  
* Log every AI alert, warning, and suggestion with timestamps

AR Overlay / XREAL HUD (UC-08, UC-10)

* Render checklist UI on XREAL glasses display using NRSDK  
* Position overlay in a non-obstructive area of the HUD  
* Display current step text and progress indicator  
* Display AI alerts/warnings as overlay popups  
* Test readability (text size, contrast, brightness)

Procedure Log (UC-11)

* Create local database/storage for procedure logs  
* Store per-procedure: steps completed, timestamps, AI alerts, warnings, missed steps  
* Design Procedure Log page accessible from homepage  
* List past procedures with date and type  
* Tap into a log to view full details

Offline Mode (UC-09)

* Ensure all checklists are stored locally  
* Ensure TTS works offline  
* Cache AI model locally or handle graceful fallback when offline  
* Test full procedure flow with no network connection

Settings Page (UC-10)

* Design Settings page UI  
* Add Appearance options (text size, brightness, overlay opacity)  
* Add Terms of Service page  
* Add Privacy Policy page

Testing

* Test on Android device without glasses (mobile-only mode)  
* Test with XREAL glasses connected  
* Test voice navigation end-to-end  
* Test each procedure checklist start to finish  
* Test AI assistant responses during procedure  
* Test procedure log saves and displays correctly  
* Test offline mode  
* Test exit and re-launch state persistence