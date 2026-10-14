# GestureDrive AI — Camera-Controlled Car Racing Game Using Hand Gestures

> **Tagline:** *"Your Hands. Your Road. Your Race."*  
> **Target Audience:** College Technology Expo / BCA Final Year Exhibition  
> **Platform:** Windows Desktop Native Application (100% Python, No External Hardware Required)

---

## 1. Project Overview

**GestureDrive AI** is an interactive, native desktop car racing game built entirely in **Python**. It enables players to drive a high-performance racing car in real time using intuitive **hand gestures** captured by a standard webcam—completely eliminating the need for keyboards, mice, gamepads, or physical steering wheels.

The application combines **Computer Vision** (OpenCV), **Deep Learning Hand Tracking** (Google MediaPipe), and **Arcade Game Physics with Pseudo-3D Scanline Projection** (Pygame & NumPy) into a responsive 60 FPS gameplay experience designed specifically for live exhibition demonstrations.

---

## 2. Key Features

- **Imaginary Steering Wheel Control:** Hold both hands in the air and tilt left or right to steer smoothly. Hand lateral shifts and single-hand assist are also dynamically supported.
- **Thumbs-Up Accelerator:** Raise a deliberate thumbs-up gesture to accelerate. Releasing the gesture naturally coasts the car down.
- **Open-Palm Brake (Strict Priority):** Flash an open palm with all 5 fingers spread to trigger rapid deceleration and stop the vehicle. Braking **strictly overrides acceleration** to ensure safety.
- **Background Multithreaded Vision Pipeline:** Camera frame capture and MediaPipe landmark tracking execute on an asynchronous worker thread. The game loop maintains a rock-solid **60 FPS** with zero frame stutter or webcam latency.
- **Pseudo-3D Arcade Road Engine:** Classic OutRun-inspired scanline perspective rendering with road curves, rolling elevation hills, alternating asphalt stripes, roadside lampposts, billboards, and trees.
- **AI Traffic & Track Hazards:** Dodge rival AI vehicles weaving between lanes, road barriers, traffic cones, and oil slicks.
- **Near-Miss Dodge Combos:** Earn bonus points and combo multipliers by cutting close to opponent cars at high speeds.
- **Live In-Game Webcam HUD (Picture-in-Picture):** Displays the mirrored camera feed in real-time with neon skeletal landmark tracking, wheel tilt readout, and gesture status badges.
- **Interactive Calibration Wizard:** 5-step guided setup ensuring reliable tracking across diverse lighting conditions and visitor hand sizes.
- **Procedural 44.1 kHz Sound Engine:** Synthesizes realistic multi-harmonic engine RPM roars, tire screeching, collision crunch impacts, and countdown beeps via NumPy and Pygame Mixer without requiring external audio downloads.
- **Fail-Safe Keyboard Fallback:** If a webcam is disconnected, in use, or denied access, the game seamlessly transitions to keyboard fallback (Arrow keys / WASD / Spacebar) without crashing.

---

## 3. Technology Stack

| Layer | Library / Tool | Role in Project |
|---|---|---|
| **Core Language** | Python 3.10 / 3.11 | High-performance, clean, modular object-oriented codebase |
| **Computer Vision** | OpenCV (`opencv-python`) | Multithreaded webcam capture, frame mirroring, color space conversion |
| **Landmark Tracking** | Google MediaPipe (`mediapipe`) | Sub-millimeter 21 3D landmark tracking per hand at 30 FPS |
| **Game Engine & Audio**| Pygame (`pygame`) | 60 FPS graphics rendering, sprite scaling, mixer playback, user inputs |
| **Math & Audio Synthesis**| NumPy (`numpy`) | Real-time procedural audio waveform generation and vector mathematics |
| **Automated Testing** | Pytest (`pytest`) | Unit and integration test suites for gestures and game logic |

---

## 4. Hand Gesture Controls Guide

```
     START RACE (Victory ✌️)        STEERING WHEEL (Both Hands)         ACCELERATOR (Thumbs-Up)          BRAKE (Open Palm)
   
           Either Hand              Left Hand       Right Hand                Either Hand                    Either Hand
              (V)                      [O]             [O]                        (Y)                           (|||||)
              / \                       \               /                         / \                             / \
             /   \                       \  (Rotate)   /                         /   \                           /   \
           Index & Middle                 \___________/                         Fist with                       All 5 Fingers
          Extended Upward                                                     Thumb Raised                    Spread Outward
       Hold 1.0s in Menu to           Tilt Left  -> Turn Left              Smooth Throttle Boost          Immediate Rapid Stop
        Launch the Race               Tilt Right -> Turn Right                                         (Overrides Acceleration!)
```

### Steering Calibration & Neutral Drift Prevention:
1. **Calibrate Center:** Click the **`CALIBRATE CENTER`** button (or press `C` in Camera Test / Calibration screen) while holding your hands comfortably. This records your resting tilt angle and horizontal camera midpoint as the exact zero-reference.
2. **Zero-Drift Neutral Steering:** When hands are level or within the deadzone ($\pm 0.08$), steering output snaps strictly to `0.00 [CENTER]`. The vehicle maintains a perfectly straight course without lateral creeping.
3. **Braking Priority:** If an open palm is detected on either hand, braking activates immediately and **completely cancels any throttle input**.
4. **Single-Fire Start Gesture:** The starting gesture (Victory ✌️ or holding dual hands steady on the wheel) triggers race startup **exactly once**, preventing duplicate starts while held. In-game racing only processes throttle, brakes, and steering.
5. **Debounce Hysteresis:** Discrete gestures (accelerator, brake, start) use temporal voting buffers to eliminate single-frame glitches.
6. **Missing Hand Behavior:** If hands leave the camera frame, steering gently centers to `0.0` and speed coasts down safely.

---

## 5. System Requirements & Windows Installation

### Prerequisites:
- Windows 10 or Windows 11 (64-bit)
- Standard integrated laptop webcam or USB webcam
- Python 3.10 or Python 3.11 installed (Python 3.11 recommended for prebuilt binary wheels)

### Step-by-Step Setup:

1. **Open PowerShell or Command Prompt** in the project directory:
   ```powershell
   cd c:\Users\Dell\Desktop\game
   ```

2. **Create and Activate a Python 3.11 Virtual Environment:**
   ```powershell
   py -3.11 -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Verify Your Webcam Hardware:**
   ```powershell
   python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera 0 Available:', cap.isOpened()); cap.release()"
   ```

---

## 6. How to Launch the Game

You can launch GestureDrive AI using either method:

### Option A: Via Command Line (Recommended)
```powershell
# Using the virtual environment python:
.\venv\Scripts\python.exe main.py

# Or if your venv is activated:
python main.py
```

### Option B: Double-Click Batch Launcher
Double-click `run_game.bat` in the project folder. It automatically detects the virtual environment and launches the game in one click!

---

## 7. Main Menu Navigation

The game starts with a professional Cyberpunk-themed main menu:

1. **START RACE (Key `1`):** Launches directly into the 3-2-1-GO! countdown and race track.
2. **CAMERA TEST (Key `2`):** Opens full-screen webcam diagnostics showing live landmark skeleton tracking, steering wheel angle meters, and camera hardware device switching.
3. **GESTURE CALIBRATION (Key `3`):** Interactive 5-step wizard guiding visitors through neutral steering, turning limits, thumbs-up, and open palm verification.
4. **HOW TO PLAY (Key `4`):** Visual gesture guide cards and College Tech Expo architecture documentation.
5. **SETTINGS (Key `5`):** Functional settings to adjust steering sensitivity, gesture confidence, sound toggles, camera index, difficulty, and fullscreen mode.
6. **EXIT GAME (Key `6` or ESC):** Gracefully releases webcam hardware and exits.

---

## 8. In-Game Controls & Hotkeys

| Action | Primary (Hand Gestures) | Fallback (Keyboard) |
|---|---|---|
| **Steer Left** | Tilt imaginary wheel Left | **Left Arrow** / **A** |
| **Steer Right** | Tilt imaginary wheel Right | **Right Arrow** / **D** |
| **Accelerate** | Thumbs-Up (Either Hand) | **Up Arrow** / **W** |
| **Brake** | Open Palm (Either Hand) | **Down Arrow** / **S** / **Space** |
| **Pause / Resume** | — | **P** or **ESC** |
| **Quick Restart** | — | **R** |
| **Toggle Fullscreen**| — | **F11** |
| **Return to Menu** | — | **Q** (while paused) |

---

## 9. Project Directory Structure

```
c:\Users\Dell\Desktop\game\
├── main.py                  # Primary application entrypoint & state coordinator
├── config.py                # Resolution, colors, physics parameters & persistent settings
├── requirements.txt         # Package dependencies (opencv-python, mediapipe, pygame, numpy)
├── run_game.bat             # 1-Click Windows batch launcher
├── README.md                # Comprehensive documentation and expo guide
├── settings.json            # Persistent user settings profile
│
├── camera/                  # Computer Vision & Gesture Recognition
│   ├── __init__.py
│   ├── camera_manager.py    # Threaded 30 FPS background webcam capture & frame processing
│   ├── hand_tracker.py      # MediaPipe Hands wrapper with cyber neon skeleton overlay
│   ├── gesture_recognizer.py# Trigonometric steering, thumbs-up, open-palm & priority debouncing
│   └── calibration.py       # 5-step guided calibration state machine
│
├── game/                    # 3D Racing Engine & Simulation
│   ├── __init__.py
│   ├── game_engine.py       # Game loop coordinator (Countdown, Racing, Collision, Audio)
│   ├── car.py               # Player sports car physics, tilting chassis & exhaust fire particles
│   ├── road.py              # Pseudo-3D OutRun scanline road projection with curves & hills
│   ├── obstacles.py         # AI traffic vehicles, traffic cones, barriers & oil slicks
│   ├── collision.py         # Bounding box collision detection, near-miss bonuses & screen shake
│   └── scoring.py           # Real-time score metrics, distance meters & high score tracking
│
├── ui/                      # Cyberpunk-Themed User Interface
│   ├── __init__.py
│   ├── dashboard.py         # In-game HUD: speedometer, gear, distance, steering dial, camera PIP
│   ├── main_menu.py         # Main menu with animated cyber grid background & buttons
│   ├── camera_test.py       # Dedicated webcam diagnostic viewport with live telemetry
│   ├── calibration_screen.py# Visual 5-step calibration wizard interface
│   ├── how_to_play.py       # College expo visual cards & system architecture presentation
│   ├── settings_screen.py   # Working sliders, toggles, difficulty & device selector
│   ├── results_screen.py    # Race recap, high score record banner & instant replay
│   └── components.py        # Reusable animated UIButton, UISlider, and UIToggle components
│
├── utils/                   # Utilities & Audio Engine
│   ├── __init__.py
│   ├── helpers.py           # Math clamping, lerp, easing, glow rendering, and drop shadows
│   └── audio.py             # Procedural 44.1kHz audio synthesizer & Pygame Mixer manager
│
├── assets/                  # Generated Local Game Assets
│   └── sounds/              # Synthesized WAV audio (engine, brake, crash, click, beep, go)
│
└── tests/                   # Automated Pytest Test Suite
    ├── test_gestures.py     # 7 tests for steering math, gestures, debouncing & priority
    └── test_game_logic.py   # 7 tests for car physics, collision, scoring & track wrapping
```

---

## 10. College Expo Demonstration Guide

When presenting **GestureDrive AI** at a college technical symposium or exhibition:

### Quick 2-Minute Visitor Demonstration Script:
1. **Welcome Visitor:** Explain the tagline: *"Your Hands. Your Road. Your Race. You drive using only your hands in front of the webcam."*
2. **Camera Test:** Click **"2. CAMERA TEST"** from the main menu. Show the visitor their hands on screen with the 21 cyan joints and electric green bones.
3. **Demonstrate Steering:** Have them hold an imaginary wheel and tilt left and right. Point out the wheel angle readout (`+25°`, `-25°`).
4. **Demonstrate Thumbs-Up:** Have them show a thumbs-up. Show the green `ACCEL ACTIVE [THUMBS UP]` indicator glow.
5. **Demonstrate Open Palm:** Have them show an open palm. Show the crimson `BRAKE ACTIVE [OPEN PALM]` indicator illuminate. Explain that **braking always overrides acceleration**.
6. **Start Race:** Press **"1. START RACE"** or press Key `1`.
7. **Gameplay:** Let the visitor dodge traffic, overtake rival cars, and experience the speed-dependent procedural engine audio.
8. **Results Screen:** When the race completes, show their final score, total distance, and top speed. Click **"RACE AGAIN"** for the next visitor!

---

## 11. Automated Testing

To run the automated test suite verifying gesture mathematics, priority rules, and game physics:

```powershell
.\venv\Scripts\python.exe -m pytest -v tests/
```

**Test Coverage Summary (14 Tests):**
- `test_steering_neutral`: Two level hands generate 0.0 steering.
- `test_steering_left`: Rotating left generates negative steering angle.
- `test_steering_right`: Rotating right generates positive steering angle.
- `test_thumbs_up_acceleration`: Synthetic fist with thumb up triggers acceleration.
- `test_open_palm_braking`: Synthetic extended hand triggers braking.
- `test_braking_overrides_acceleration`: Simultaneous throttle and brake strictly triggers brake.
- `test_missing_hands_returns_to_neutral`: Lost tracking smoothly self-centers steering.
- `test_car_acceleration_and_braking`: Verifies car acceleration and deceleration physics.
- `test_brake_strictly_overrides_accel`: Confirms vehicle physics priority.
- `test_car_offroad_penalty`: Verifies off-road speed cap and grass drag.
- `test_track_wrapping`: Verifies continuous track segment retrieval.
- `test_collision_detection`: Verifies bounding box impact detection.
- `test_near_miss_bonus`: Verifies close dodge recognition (+250 points).
- `test_scoring_system`: Verifies distance meters, speed multipliers, and high score persistence.

---

## 12. Troubleshooting & FAQ

#### Q: The camera preview says "Camera Offline" or "Access Denied".
- **Solution 1:** Make sure no other application (e.g., Zoom, Teams, Chrome, Camera App) is using the webcam.
- **Solution 2:** In Windows Settings -> Privacy & Security -> Camera, ensure **"Allow desktop apps to access your camera"** is toggled ON.
- **Solution 3:** Go to **Settings** in the game and switch from Camera #0 to Camera #1 or Camera #2.
- **Solution 4:** Keyboard fallback is always active! You can still play immediately using Arrow keys or W/A/S/D.

#### Q: Gestures are triggering slowly or missing in dark rooms.
- **Solution:** Ensure adequate front lighting on your hands. In **Settings**, you can lower the **Gesture Detection Confidence** slider to `0.50` for higher sensitivity in dim lighting.

#### Q: Can I run this game on a computer without an internet connection?
- **Yes!** All assets, procedural sounds, and MediaPipe models are bundled locally. Once installed, GestureDrive AI requires **zero internet access**.

---

## 13. Academic Attribution & License

Developed for academic presentation and college technology exhibitions.  
Built with Python, OpenCV, Google MediaPipe, Pygame, and NumPy.  
Free and open source for educational and exhibition purposes.
