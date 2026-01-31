# 🚤 Autonomous Underwater Submarine Robot

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python&logoColor=white)
![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-5-C51A4A?style=for-the-badge&logo=Raspberry-Pi)
![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=for-the-badge&logo=flask)
![OpenCV](https://img.shields.io/badge/OpenCV-4.13-5C3EE8?style=for-the-badge&logo=opencv)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**An AI-powered autonomous submarine with computer vision, real-time control, and multi-sensor integration for underwater exploration.**

[Features](#-features) • [Hardware](#-hardware) • [Installation](#-installation) • [Usage](#-usage) • [Documentation](#-documentation)

---

### 🎥 Demo

![Submarine Demo](https://via.placeholder.com/800x400/0f2027/ffffff?text=Submarine+Demo+Video)

*Real-time autonomous object detection and tracking underwater*

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Hardware Components](#-hardware-components)
- [Software Stack](#-software-stack)
- [Installation](#-installation)
- [Wiring Guide](#-wiring-guide)
- [Usage](#-usage)
- [API Reference](#-api-reference)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌊 Overview

This project is a fully autonomous underwater submarine robot built with **Raspberry Pi 5**, featuring advanced **computer vision** for object detection, **multi-sensor integration** for environmental monitoring, and a **responsive web interface** for real-time control and telemetry.

### 🎯 Key Highlights

- **Dual Control Modes**: Manual web control + AI autonomous navigation
- **Computer Vision**: YOLOv8 object detection + custom target tracking  
- **Real-time Streaming**: 1080p HD camera with underwater image enhancement
- **Multi-Sensor**: IMU, pressure, temperature, ultrasonic integration
- **Web Dashboard**: Beautiful responsive interface with live data
- **Open Source**: Complete documentation and customizable code

---

## 🌟 Features

### 🎮 Control Systems

#### Manual Control
- **Web Interface**: Intuitive HTML5 dashboard accessible from any device
- **Real-time Response**: <100ms control latency
- **Multi-input Support**: Button controls + keyboard shortcuts (WASD/Arrows)
- **Emergency Stop**: Instant motor cutoff for safety
- **Live Telemetry**: Real-time sensor data display (depth, temperature, orientation)

#### Autonomous Mode
- **YOLO Detection**: 80+ object classes detection using YOLOv8n
- **Custom Target Search**: Upload image and track specific objects using feature matching
- **Auto Navigation**: Follow and track detected targets
- **Smart Capture**: Automatic photo capture on detection
- **Mission Complete**: Auto-surface after successful target acquisition

### 📷 Vision System

- **Camera**: Raspberry Pi Camera Module 3 (12MP, 1080p @ 30fps)
- **Image Enhancement**: 
  - Underwater color correction (blue/green compensation)
  - CLAHE contrast enhancement
  - Sharpening filters for clarity
- **Object Detection**: YOLOv8 neural network for real-time detection
- **Feature Matching**: ORB algorithm for custom target tracking
- **Live Streaming**: MJPEG over HTTP for real-time video feed

### 🧭 Sensor Suite

| Sensor | Model | Purpose | Interface |
|--------|-------|---------|-----------|
| **IMU** | MPU9250 | 9-axis orientation (gyro + accel + magnetometer) | I2C (0x68) |
| **Pressure** | BMP280 | Depth & altitude measurement | I2C (0x76) |
| **Temperature** | DS18B20 | Waterproof water temperature sensor | 1-Wire (GPIO4) |
| **Ultrasonic** | JSN-SR04T | Waterproof distance/obstacle detection | GPIO (23/24) |
| **Buzzer** | Active 5V | Audio alerts & notifications | GPIO (17) |

### 🎛️ Motor Control

- **Main Propulsion**: Brushless motor via SimonK 30A ESC
- **Servo 1** (Ch0): Rudder for yaw control (45-135°)
- **Servo 2** (Ch1): Elevator 1 for pitch control
- **Servo 3** (Ch2): Elevator 2 for pitch control
- **PWM Driver**: PCA9685 16-channel I2C controller (0x40)

---

## 🔧 Hardware Components

### Electronics

| Component | Specification | Purpose |
|-----------|--------------|---------|
| **Microcontroller** | Raspberry Pi 5 (4GB/8GB) | Main processor |
| **Motor Controller** | SimonK 30A ESC | Brushless motor control |
| **Servo Driver** | PCA9685 16-Channel | I2C servo/ESC control |
| **IMU** | MPU9250 | Orientation tracking |
| **Pressure Sensor** | BMP280 | Depth measurement |
| **Temperature** | DS18B20 Waterproof | Water temperature |
| **Ultrasonic** | JSN-SR04T | Distance sensing |
| **Camera** | Pi Camera Module 3 | 1080p video |
| **Buzzer** | Active 5V | Audio alerts |

### Power System

| Component | Specification |
|-----------|--------------|
| **Battery** | 8x AA (3000mAh, 12V total) or 3S LiPo (11.1V) |
| **Buck Converter** | LM2596S 5A (12V → 5V) |
| **Switch** | 40A Rocker Switch |
| **Connectors** | XT60 Male/Female |

### Motors & Servos

- **Brushless Motor**: 1000-1400 KV BLDC
- **Servos**: 3x Standard servos (SG90/MG90S)
- **Propeller**: 3-blade, 50-70mm diameter

---

## 💻 Software Stack

### Backend
