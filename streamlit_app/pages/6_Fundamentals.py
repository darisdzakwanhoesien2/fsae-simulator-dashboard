# import streamlit as st
# import json

# st.title("1️⃣ Fundamentals of the Idea")

# with open("data/driver_sim.json") as f:
#     data = json.load(f)

# section = data["1_fundamentals_of_the_idea"]

# st.header("Summary")
# st.write(section["summary"])

# st.header("Core Principles")
# for item in section["core_principles"]:
#     st.markdown(f"- {item}")

# st.header("Goal")
# st.success(section["goal"])

import streamlit as st
import json

st.set_page_config(page_title="Driver Simulation Proposal", layout="wide")

# Load JSON
with open("data/driver_sim.json") as f:
    data = json.load(f)

# Sidebar Navigation
section = st.sidebar.selectbox(
    "📑 Select a Section",
    [
        "1. Fundamentals of the Idea",
        "2. Detailed Concept",
        "3. Impact of Implementing the Idea",
        "4. Manufacturing Methods",
        "5. Mounting / Implementation",
        "6. Future Testing Methods",
        "7. Additional Considerations"
    ]
)

st.title("🚗 Driver Simulation Training System Proposal")

# === SECTION 1 ===
if section.startswith("1"):
    s = data["1_fundamentals_of_the_idea"]
    st.header("1️⃣ Fundamentals of the Idea")
    st.subheader("Summary")
    st.write(s["summary"])

    st.subheader("Core Principles")
    for item in s["core_principles"]:
        st.markdown(f"- {item}")

    st.subheader("Goal")
    st.success(s["goal"])

# === SECTION 2 ===
elif section.startswith("2"):
    s = data["2_detailed_concept"]
    st.header("2️⃣ Detailed Concept")

    st.subheader("System Components")
    st.json(s["system_components"])

    st.subheader("Training Method")
    for step in s["training_method"]["steps"]:
        st.markdown(f"- {step}")

# === SECTION 3 ===
elif section.startswith("3"):
    s = data["3_impact_of_implementing_the_idea"]
    st.header("3️⃣ Impact of Implementing the Idea")

    st.subheader("Competitive Benefits")
    st.write(s["competitive_benefits"])

    st.subheader("Team Improvements")
    st.write(s["team_improvements"])

    st.subheader("Long-Term Value")
    st.write(s["long_term_value"])

# === SECTION 4 ===
elif section.startswith("4"):
    s = data["4_manufacturing_methods_and_considerations"]
    st.header("4️⃣ Manufacturing Methods & Considerations")

    st.subheader("Physical Components")
    st.write(s["physical_components"])

    st.subheader("Software Development")
    st.write(s["software_development"])

    st.subheader("Considerations")
    st.write(s["considerations"])

# === SECTION 5 ===
elif section.startswith("5"):
    s = data["5_mounting_and_implementation_on_car"]
    st.header("5️⃣ Mounting / Implementation on the Car")

    st.subheader("Note")
    st.info(s["note"])

    st.subheader("Implementation Links")
    st.write(s["implementation_links"])

    st.subheader("Sync Requirements")
    st.write(s["sync_requirements"])

# === SECTION 6 ===
elif section.startswith("6"):
    s = data["6_future_real_life_testing_methods"]
    st.header("6️⃣ Future Real-Life Testing Methods")

    st.subheader("Validation Process")
    st.write(s["validation_process"])

    st.subheader("Extensions")
    st.write(s["extension"])

# === SECTION 7 ===
elif section.startswith("7"):
    s = data["7_additional_considerations"]
    st.header("7️⃣ Additional Considerations")

    st.subheader("Risks")
    st.write(s["risks"])

    st.subheader("Opportunities")
    st.write(s["opportunities"])

    st.subheader("Maintenance")
    st.write(s["maintenance"])
