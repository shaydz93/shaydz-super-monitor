# S h a y d Z Super Monitor

![Python](https://img.shields.io/badge/python-3.7+-blue?logo=python)
![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%20%7C%20Linux-red?logo=raspberry-pi)
![License](https://img.shields.io/github/license/shaydz93/shaydz-super-monitor)
![Issues](https://img.shields.io/github/issues/shaydz93/shaydz-super-monitor)
![Last Commit](https://img.shields.io/github/last-commit/shaydz93/shaydz-super-monitor)
![Stars](https://img.shields.io/github/stars/shaydz93/shaydz-super-monitor?style=social)

![ShaydZ Logo](static/shaydz_logo.png)

**Ultimate White/Grey-Hat Network Defense, Monitoring, and AI Threat Intelligence Dashboard**

---

## About

**S h a y d Z Super Monitor** is a modular, self-learning, all-in-one network defense and threat intelligence system for your home lab or professional use.  
It’s built for Raspberry Pi Zero 2 WH, but works on most Pi/Linux systems.

---

## Features

- **Self-learning anomaly detection:** CPU, RAM, disk, temp, failed logins, multi-device health, rolling baselines, and more.
- **Automated threat intelligence feeds:** CISA, CVE, Reddit, BleepingComputer, OTX, Pastebin leaks, breach trackers, and more.
- **Secure web admin dashboard:** Real-time alerts, logs, intelligence, authentication, remote access, anomaly feedback/correction.
- **Integrated assistant:**  
  - **Local:** Summarizes system/logs for privacy  
  - **Cloud AI:** Use OpenAI GPT (optional, paste your API key in settings)
- **Real-time e-paper output:** Status & critical alerts on Waveshare 2.13" V3 display.
- **Customizable triggers:** Auto-block IPs, notify, run scripts, auto-shutdown on temp, and more.
- **Full branding:** All code and UI show S h a y d Z logos and ASCII art.
- **Easy install:** One-script setup, auto-run with systemd, and modular codebase.

---

## Quick Start

1. **Clone or copy the project to your Pi/Linux host:**

    ```bash
    cd ~
    git clone https://github.com/shaydz93/shaydz-super-monitor.git
    cd shaydz-super-monitor
    ```

2. **Install all requirements and set up the service:**

    ```bash
    sudo bash install.sh
    ```

3. **Access the admin dashboard:**

    - Open [http://YOUR-PI-IP:5001](http://YOUR-PI-IP:5001) from your browser
    - Set up your admin account (first login)

4. **(Optional)** Add OpenAI API key in Assistant Settings for cloud AI answers.

5. **Monitor and secure your lab/network with confidence!**

---

## Directory Structure


---

## Hardware Support

- **Tested on:** Raspberry Pi Zero 2 WH, Pi 3, Pi 4 (should work on all modern Pis)
- **E-Paper:** Waveshare 2.13" V3 HAT  
  - For other displays, edit `display.py` (resolution/fonts).
- **Other Linux**: All software runs on any modern Linux (minus e-paper display).

---

## Screenshots

*Add screenshots of your dashboard and e-paper display here for extra flair!*

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Credits

- Inspired by open-source blue-team and threat intelligence tools.
- E-paper Python libraries © Waveshare.
- Powered by [OpenAI](https://platform.openai.com/) (optional integration).

---

## Contributing

PRs, issues, and feature requests are welcome!  
Open an [issue](https://github.com/shaydz93/shaydz-super-monitor/issues) or submit a pull request.

---

**Monitor smarter. Defend deeper. Hack your home lab with S h a y d Z Super Monitor!**
