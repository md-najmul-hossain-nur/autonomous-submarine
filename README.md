# 🚤 Autonomous Underwater Submarine Robot

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python&logoColor=white)
![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-5-C51A4A?style=for-the-badge&logo=Raspberry-Pi)
![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=for-the-badge&logo=flask)
![OpenCV](https://img.shields.io/badge/OpenCV-4.13-5C3EE8?style=for-the-badge&logo=opencv)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**An AI-powered autonomous submarine with computer vision, real-time web control, multi-sensor integration, and automated deployment.**

[Features](#-features) • [Quick Start](#-quick-start) • [Installation](#-installation) • [Hardware](#-hardware) • [API](#-api-reference) • [Troubleshooting](#-troubleshooting)

---

### 🎥 Demo

![Submarine Demo](https://via.placeholder.com/800x400/0f2027/ffffff?text=Autonomous+Submarine+Robot+Demo)

*Real-time autonomous object detection and tracking underwater with HD camera streaming*

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Quick Start](#-quick-start)
- [Hardware Components](#-hardware-components)
- [Installation](#-installation)
  - [Automated Setup](#automated-installation-recommended)
  - [Manual Setup](#manual-installation)
- [Auto-Start Configuration](#-auto-start-configuration)
- [Network Setup](#-network-configuration)
- [Wiring Guide](#-wiring-guide)
- [Usage](#-usage)
- [Configuration](#-configuration)
- [API Reference](#-api-reference)
- [Scripts & Tools](#-scripts--tools)
- [Troubleshooting](#-troubleshooting)
- [Performance](#-performance)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌊 Overview

This is a fully autonomous underwater submarine robot designed for exploration, research, and educational purposes. Built on **Raspberry Pi 5** with advanced **computer vision** capabilities, **multi-sensor integration**, and both **manual** and **autonomous** control modes.

### 🎯 What Makes This Special

- ✅ **One-Command Installation**: Automated setup script handles everything
- ✅ **Auto-Start on Boot**: Systemd service starts backend automatically
- ✅ **WiFi Hotspot Mode**: Built-in access point for direct connection
- ✅ **Dual Control**: Manual web interface + AI autonomous navigation
- ✅ **Computer Vision**: YOLOv8 detection + custom target tracking
- ✅ **Real-time Streaming**: 1080p HD camera with underwater enhancement
- ✅ **Multi-Sensor**: IMU, pressure, temperature, ultrasonic integration
- ✅ **Web Dashboard**: Beautiful responsive interface with live telemetry
- ✅ **Open Source**: Complete documentation and customizable code

---

## 🌟 Features

### 🎮 Control Systems

#### Manual Control
- **Web Interface**: Responsive HTML5 dashboard (desktop/tablet/mobile)
- **Real-time Response**: <100ms control latency
- **Multi-input Support**: Touch buttons + keyboard shortcuts (WASD/Arrows)
- **Emergency Stop**: Instant motor cutoff for safety
- **Live Telemetry**: Real-time sensor data (depth, temp, orientation, battery)

#### Autonomous Mode
- **YOLO Detection**: 80+ object classes using YOLOv8n neural network
- **Custom Target Search**: Upload image and track specific objects
- **Feature Matching**: ORB algorithm for robust target recognition
- **Auto Navigation**: Follow and track detected targets
- **Smart Capture**: Automatic photo on detection with metadata
- **Mission Complete**: Auto-surface after successful target acquisition

### 📷 Vision System

- **Camera**: Raspberry Pi Camera Module 3 (12MP, 1080p @ 30fps)
- **Image Enhancement**: 
  - Underwater color correction (blue/green compensation)
  - CLAHE contrast enhancement for clarity
  - Sharpening filters for detail
- **Object Detection**: YOLOv8 neural network for real-time detection
- **Feature Matching**: ORB keypoint detection and matching
- **Live Streaming**: MJPEG over HTTP for low-latency video feed
- **Photo Gallery**: Capture, view, and download images

### 🧭 Sensor Suite

| Sensor | Model | Purpose | Interface | Address |
|--------|-------|---------|-----------|---------|
| **IMU** | MPU9250 | 9-axis orientation (gyro + accel + mag) | I2C | 0x68 |
| **Pressure** | BMP280 | Depth & altitude measurement | I2C | 0x76 |
| **Temperature** | DS18B20 | Waterproof water temperature | 1-Wire | GPIO4 |
| **Ultrasonic** | JSN-SR04T | Waterproof obstacle detection (20cm-6m) | GPIO | 23/24 |
| **Buzzer** | Active 5V | Audio alerts & notifications | GPIO | 17 |

### 🎛️ Motor Control

- **Main Propulsion**: Brushless DC motor via SimonK 30A ESC
- **Servo 1** (Channel 0): Rudder for yaw/steering (45-135°)
- **Servo 2** (Channel 1): Elevator 1 for pitch control (45-135°)
- **Servo 3** (Channel 2): Elevator 2 for pitch control (45-135°)
- **PWM Driver**: PCA9685 16-channel I2C servo controller (0x40)
- **Control Range**: 0-100% throttle, precise angle control

---

## 🚀 Quick Start

### Automated Installation (Recommended)

**One-command setup on fresh Raspberry Pi:**

```bash
# Clone repository
git clone https://github.com/Tanjil-Hassan-Sawan/submarine-robot.git
cd submarine-robot

# Run automated installer
bash setup/install.sh
