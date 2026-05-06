# ClaimSure — AI-Powered Crop Insurance Claim Assistant for Farmers

## Overview

ClaimSure is an AI-powered platform designed to help farmers file, track, and defend crop insurance claims with transparency and accountability.

In many rural areas, farmers suffer devastating crop losses due to floods, hailstorms, droughts, pest attacks, and unpredictable climate events. Even after paying insurance premiums, they often face:

* Delayed claim processing
* Underpaid settlements
* Missing documentation
* Lack of legal awareness
* Corruption and middlemen exploitation
* Poor communication from insurance providers

ClaimSure aims to solve this problem using AI, automation, and evidence-driven workflows.

---

# Problem Statement

A farmer loses his crop due to a natural disaster.

He files an insurance claim.

Then:

* The claim remains “under process” for months
* Insurance agents delay field visits
* Farmers don’t know the correct compensation amount
* Evidence gets rejected
* Farmers lack legal support
* Many claims are partially settled unfairly

As a result, even insured farmers continue to suffer major financial losses.

---

# Solution

ClaimSure simplifies and strengthens the crop insurance claim process through:

## Core Features

### 1. Geo-tagged Evidence Collection

* Farmers can upload:

  * Photos
  * Videos
  * Crop damage proof
* Evidence is:

  * Timestamped
  * Geo-tagged
  * Organized automatically

---

### 2. AI-Based Claim Assistance

* Helps farmers:

  * Understand insurance policies
  * Know required documents
  * Generate claim forms automatically

---

### 3. Claim Status Tracking

* Real-time tracking of claim progress
* Farmers can monitor:

  * Submission date
  * Pending actions
  * Insurance response timeline

---

### 4. Auto Escalation System

If insurers fail to respond within a specified period:

* ClaimSure automatically flags delays
* Escalation reminders are generated
* Farmers receive guidance on next legal steps

---

### 5. Multi-language Support

Designed for accessibility:

* Voice-friendly interface
* Regional language support
* Simple UI for low digital literacy users

---

### 6. Community Claim Intelligence

If multiple farmers from the same area report similar damage:

* Claims can be grouped
* Pattern detection becomes easier
* Insurance fraud/delay trends become visible

---

# Tech Stack

## Frontend

* HTML
* CSS
* JavaScript

## Backend

* Python
* Flask

## Additional Features

* Geo-location metadata processing
* EXIF extraction
* File upload handling
* AI-assisted workflows

---

# Project Structure

```bash
ClaimSure/
│
├── app.py
├── geo_exif.py
├── i18n.py
├── requirements.txt
│
├── static/
│   ├── css/
│   ├── js/
│   └── uploads/
│
├── templates/
│   ├── index.html
│   ├── upload.html
│   └── result.html
│
└── README.md
```

---

# Installation

## Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/ClaimSure-for-farmers.git
```

## Navigate to project folder

```bash
cd ClaimSure-for-farmers
```

## Create virtual environment

```bash
python -m venv venv
```

## Activate virtual environment

### Windows

```bash
venv\Scripts\activate
```

### Mac/Linux

```bash
source venv/bin/activate
```

## Install dependencies

```bash
pip install -r requirements.txt
```

---

# Run the Application

```bash
python app.py
```

Then open:

```bash
http://127.0.0.1:5000
```

---

# Future Scope

* AI-powered crop damage assessment
* Insurance fraud detection
* Satellite/weather integration
* Blockchain-based claim verification
* Mobile application deployment
* Government scheme integration
* Legal advisory support
* WhatsApp-based farmer assistance

---

# Social Impact

ClaimSure is designed to:

* Protect vulnerable farmers
* Improve insurance transparency
* Reduce claim delays
* Increase financial resilience in agriculture
* Support rural communities during climate disasters

---

# Inspiration

This project was inspired by real-world problems faced by Indian farmers dealing with:

* Crop destruction
* Insurance delays
* Financial stress
* Bureaucratic complexity
* Lack of digital support systems

---

# Contributors

Developed by:

* Shreya Hiremath

---

# License

This project is developed for educational, innovation, and social impact purposes.
