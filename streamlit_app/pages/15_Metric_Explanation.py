import streamlit as st

st.set_page_config(layout="wide")
st.title("📘 Driving Metrics — Explanation Guide")

st.markdown("""
## 🧨 Aggression
Measures how often and how sharply a driver:
- applies full throttle
- brakes hard
- makes large steering changes  
High = fast and risky  
Low = stable but slow  

---

## 🌊 Smoothness
Measures:
- how stable throttle application is
- how gentle braking is
- how clean the steering transitions are  
High = calm, efficient driving  
Low = jerky, inefficient driving  

---

## 🎯 Consistency
Evaluates:
- lap-to-lap variance
- speed variance at key track segments  
High = reliable, repeatable performance  
Low = unpredictable or inconsistent driver  

---

## 🌀 Cornering Skill
Uses:
- yaw rate profile
- mid-corner speed
- how early/late braking occurs
- steering stability  

High = strong cornering control  
Low = late braking, unstable mid-corner control  

---

## ⏱ Lap Time
Pure performance metric computed from track_index cycle time.

Used to correlate:
- smooth drivers = efficient + good lap time
- aggressive drivers = risk high + variable lap times  
""")
