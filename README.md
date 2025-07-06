# 🐾 OwO Selfbot Guide

A complete setup and usage guide for OwO Selfbot, compatible with PC and Android (Termux).

Live demo: **[GitHub Pages Link Here](https://yourusername.github.io/owo-guide/)**

---

## 📋 Features
- Clear step-by-step installation
- Modern UI (HTML, Prism.js, Copy buttons)
- Runs on PC or Termux Android
- Designed for minimalism + usability

---

## 🚀 Quick Start

### 📁 Clone the Repo
```bash
git clone https://github.com/yourusername/owo-guide.git
cd owo-guide
```

### 💻 Open the Web Guide
Open `index.html` in your browser or deploy via GitHub Pages.

---

## 💻 Setup Overview

### PC
```bash
python -m pip install -r requirements.txt
python main.py
```

### Android (Termux)
```bash
pkg update -y && pkg upgrade -y && termux-setup-storage \
&& pkg install -y python git termux-api \
&& git clone https://github.com/realphamdat/phamdat-selfbot.git \
&& cd phamdat-selfbot
python -m pip install -r requirements.txt
python main.py
```

### iOS
> Coming soon...

---

## 📦 Project Structure
```
📁 owo-guide/
├── index.html      # Main guide UI
└── README.md       # This file
```

---

## 📢 Disclaimer
> This project is for educational purposes only. The author is not responsible for any misuse.

---

## 🌐 License
MIT © [Phạm Thành Đạt](https://github.com/realphamdat)
