# 🍎 Classroom Seating & Grouping Tool

A professional-grade Python application designed for educators to generate balanced, ability-aware seating charts and student groupings. This tool automates the tedious task of organizing classes while ensuring pedagogical balance across all periods.

## ✨ Key Features

* **Ability-Balanced Grouping:** Uses a "stratified randomization" algorithm to ensure high-performing and struggling students are distributed evenly across groups.
* **Three Modes of Operation:**
    * **Pairs:** Groups students with similar abilities for peer-tutoring or focused partner work.
    * **Groups of 3-4:** Creates balanced teams for collaborative projects.
    * **7 Tables:** Spreads the class across 7 specific locations (ideal for fixed classroom layouts).
* **Privacy-First Design:** * Student "Competence" scores are used for logic but are **not displayed** on the final chart.
    * Names are shuffled *within* their groups so students cannot discern a hierarchy.
* **Absence Handling:** Automatically skips students marked with an 'A' in the Status column.
* **Batch Processing:** Generates layouts for up to 9 class periods (tabs) simultaneously and exports them into a single, print-ready PDF.

## 📋 File Requirements

The app requires an Excel file (`.xlsx`) with the following structure:
* **Tabs:** Named `Period 1`, `Period 2`, etc., up to `Period 9`.
* **Columns:** * `Name`: Student's name (displayed on chart).
    * `Competence`: A numerical score (1-10) used for balancing groups.
    * `Status`: (Optional) Mark as 'A' to exclude a student from the layout.

## 🚀 Getting Started

### Prerequisites
* Python 3.8+
* The following libraries: `pandas`, `openpyxl`, `matplotlib`, `pillow`, `streamlit`

### Installation
1. Clone this repository or download the files.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
