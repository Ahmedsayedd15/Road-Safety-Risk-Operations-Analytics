# 🚦 Road Safety Risk & Operations Analytics

An end-to-end Business Intelligence project that analyzes **5 years of UK road collisions (2021–2025)** from the Department for Transport (STATS19) using Python, MySQL, Power BI, and DAX.

The dashboard shows where, when, and under which conditions collisions happen, who is affected, and how much of the trend can actually be trusted, from raw police records to an interactive decision-support dashboard.

## 📌 Project Overview

This project takes real UK road casualty data (513,801 collisions, 937,265 vehicles, 652,821 casualties), audits and cleans it with Python, stores and models it in MySQL, and builds a 6-page interactive Power BI dashboard on a star schema with DAX measures.

The dashboard answers key questions such as:

- How many collisions, casualties, and fatal collisions are there, and how are they changing?
- When do collisions happen: which hours, weekdays, and months?
- Where do they happen: which districts and police forces see the most?
- Which conditions (light, weather, road surface, speed limit) carry the highest share of fatal collisions?
- Who is most affected: which road users, age bands, and vehicle types?
- Is the rise in Serious collisions real, or partly a change in how injuries are recorded?

## 🚀 Dashboard Pages

### 📊 Overview
High-level KPIs (total collisions, casualties, fatal collisions, fatal share, casualties per collision), monthly trend, severity split, top districts, and collisions by hour of day.

### 🕒 When
Hour × weekday heatmap, collisions by weekday and month, and the share of fatal collisions by hour.

### 🗺️ Where
District map (one bubble per district), top districts by fatal collisions, and top police forces.

### 🌦️ Conditions
Light, weather, road surface, and speed limit: collisions (bars) against the share that were fatal (dots/line).

### 👥 Who Is Affected
Casualties by road-user class, age band, severity, and casualty type, plus the vehicle types involved.

### 📈 Severity Trend
Reported vs adjusted Serious and Slight collisions, fatal collisions, and the share of records on injury-based reporting, with a note on how to read them.

## 🛠️ Tech Stack

Python
pandas
MySQL
Power BI
DAX
Data Modeling (Star Schema)
Data Cleaning

## 📂 Project Workflow

Python Data-Quality Audit

⬇️

Python Cleaning & Transformation

⬇️

MySQL Database (3 Fact Tables + 17 Lookup Tables)

⬇️

Data Modeling

⬇️

DAX Measures & KPIs

⬇️

Interactive Power BI Dashboard

## 📸 Dashboard Preview

### Overview
<img width="1220" height="503" alt="Overview" src="https://github.com/user-attachments/assets/255c1618-499f-45b7-a209-6ec300c94306" />

### When
<img width="1218" height="500" alt="When" src="https://github.com/user-attachments/assets/5727f748-312b-4c2b-8eb5-5b32ec0482a7" />

### Where
<img width="1220" height="505" alt="Where" src="https://github.com/user-attachments/assets/ea9b6f79-9976-40f5-9087-b6a96504adb0" />

### Conditions
<img width="1217" height="504" alt="Conditions" src="https://github.com/user-attachments/assets/3b7d1890-1f00-4185-8908-f14a00438c74" />

### Who Is Affected
<img width="1220" height="503" alt="Who" src="https://github.com/user-attachments/assets/5db9d5ae-62eb-46fa-b9d3-8c9129e0317d" />

### Severity Trend
<img width="1219" height="499" alt="Severity Trend" src="https://github.com/user-attachments/assets/6c1ff76b-9a47-4101-882b-be707353bd34" />

## 🗄 Database

The project uses MySQL as the primary data source, with 20 tables: 3 fact tables and 17 lookup tables.

Fact tables:

- Collisions
- Vehicles
- Casualties

Lookup tables (generated from the official DfT data guide so codes and labels match the source):

- Collision Severity
- Casualty Severity
- Day of Week
- Road Type
- Speed Limit
- Light Conditions
- Weather Conditions
- Road Surface Conditions
- Police Force
- Local Authority
- Vehicle Type
- Sex of Driver
- Age Band of Driver
- Casualty Class
- Sex of Casualty
- Age Band of Casualty
- Casualty Type

## 🧹 Data Preparation

The raw STATS19 files looked clean, but two traps could have produced misleading results. The data was audited and every decision documented before any analysis.

The data preparation process included:

- Running a full data-quality audit: duplicates, orphan records, missing values, coordinate and date validity
- Discovering that missing values are coded as -1 (not NULL), and converting them to NULL only in the columns used for analysis, so "missing" stays distinct from real categories such as "unknown"
- Replacing the legacy local_authority_district column (99.96% missing) with local_authority_ons_district
- Keeping the 53 collisions without coordinates and excluding them from the map only
- Flagging 3 district codes missing from the DfT code list (about 0.3% of collisions) instead of dropping them
- Deriving date, hour, month, and weekday columns while preserving the original values
- Building 17 lookup tables programmatically from the official data guide
- Verifying row counts and keys after loading into MySQL (no duplicates, no orphans)
- Using the DfT severity-adjustment guidance to separate real change from reporting change
- Setting up relationships to avoid fan-out and filter context issues

## ⭐ Key Business Insights

<!-- ✏️ Verify these numbers against your dashboard before publishing. -->
- Reported Serious collisions rose about 18% (21,284 in 2021 to 25,191 in 2025), but the share of records on injury-based reporting grew from about half to about two-thirds, so part of the rise comes from how injuries are recorded.
- Fatal collisions stayed roughly stable across the period (about 1,450–1,650 a year).
- Friday is the busiest day, and collisions peak in the afternoon rush hour.
- The share of fatal collisions rises with the speed limit (up to 60 mph), even though most collisions happen on 30 mph roads.
- Birmingham has the most fatal collisions among districts and the Metropolitan Police record the most collisions of any force, but these are counts, not risk: no traffic-volume data is available, so the dashboard reports counts and shares only.
- Built executive-level KPIs and a dashboard that states clearly what it cannot conclude.

## 👨‍💻 Author

Ahmed Sayed

Data Analyst | Computer Engineering Student

LinkedIn: https://linkedin.com/in/ahmed-sayed-b03368283

Portfolio: https://ahmedsayedd15.github.io/my-portfolio

GitHub: https://github.com/Ahmedsayedd15

## 🏷️ Skills Demonstrated

Python pandas MySQL Power BI DAX Data Modeling Data Cleaning Data Quality Auditing Data Visualization Business Intelligence Public-Sector Analytics Road Safety Analytics
