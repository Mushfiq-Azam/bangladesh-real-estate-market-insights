# **Bangladesh Real Estate Market Insights: A Data-Driven Analysis of Dhaka Housing Prices**

### **A Capstone Project | Data Analysis & Visualization**

---

## **Project Overview**

Dhaka, one of the fastest-growing megacities in the world, faces rapid urbanization and continuous shifts in real estate demand. This project aims to uncover **data-driven insights** into housing prices across major neighborhoods in Dhaka.

Using a combination of **Python, Pandas, data scraping, data cleaning, EDA, statistical analysis, and advanced visualizations**, this study explores:

* Which neighborhoods have the highest/lowest housing prices
* Factors influencing price variations
* Trends, distribution, and patterns in Dhaka’s real estate market
* Data-driven insights useful for buyers, sellers, and policymakers

You can visit the public dashboard [here](https://public.tableau.com/app/profile/mushfiq.azam/viz/Dhakarealestatemarketinsight/Dashboard1?publish=yes).


---

## **Objectives**

1. Collect and prepare real estate listing data.
2. Clean, transform, and structure datasets for analysis.
3. Perform exploratory data analysis (EDA).
4. Visualize patterns in Dhaka’s housing prices.
5. Interpret results and generate actionable insights.

---

## **Project Structure**

```
📦 Bangladesh Real Estate Market Insights
 ├── data/
 │    ├── raw/                 # Scraped/unprocessed data
 │    └── cleaned/             # Final cleaned datasets
 ├── notebooks/
 │    ├── data_cleaning.ipynb
 │    └── eda_visualization.ipynb
 │            # All charts and graphs
 ├── src/
 │    ├── scraping.py
 │    ├── cleaning.py
 │    └── utils.py
 ├── README.md
 └── requirements.txt
```

---

##  **Tools & Technologies**

| Category         | Tools                       |
| ---------------- | --------------------------- |
| Programming      | Python                      |
| Data Wrangling   | Pandas, NumPy               |
| Visualization    | Matplotlib, Seaborn |
| Scraping         | BeautifulSoup / Requests    |
| Version Control  | Git, GitHub                 |
| Optional BI Tool | Tableau                     |

---

## **Key Analyses Performed**

###  Neighborhood-wise price distribution

Which areas of Dhaka are most expensive / affordable.

###  Price vs. apartment size

Scatter plots, regression lines, correlations.


###  Interactive visualizations

Plotly dashboards for exploration.

---

---

## 📑 **Dataset Description**

* **Source**: Scraped from popular real estate platforms / publicly available listings.
* **Fields include**:

  * Location
  * Size (sq ft)
  * Price (total / per sq ft)
  * Bedrooms & bathrooms

---

##  **Insights Summary**

1. **Dhanmondi** and **Gulshan** are the most expensive areas in Dhaka, with average property prices exceeding 60M BDT, highlighting the concentration of premium real estate in these well-established, central locations.

2. Suburban areas like **Mirpur** and **Uttarkhan** offer more affordable properties, making them attractive for first-time buyers or those seeking larger homes at lower costs compared to premium zones.

3. The significant price disparity between locations such as **Dhanmondi** and **Rampura** shows the sharp segmentation in Dhaka’s real estate market, catering to both luxury and budget-conscious buyers.

4. **Rampura** and **Shyamoli** are emerging areas with increasing demand, suggesting future opportunities for development in suburban regions that remain more affordable compared to the city center.

---

## 🚀 **How to Run This Project**

### **1. Clone the repository**

```bash
git clone https://github.com/yourusername/bangladesh-real-estate-market-insights.git
cd bangladesh-real-estate-market-insights
```

### **2. Install requirements**

```bash
pip install -r requirements.txt
```
Download Chrome WebDrive from https://chromedriver.chromium.org/downloads
Run the scraper
scraper.py --chromedriver_path <path_to_chromedriver>
You will get a file named dhaka_real_estate.csv containing all the required fields. Alternatively, check our scraped data here: https://github.com/Mushfiq-Azam/bangladesh-real-estate-market-insights/blob/main/notebooks/dhaka_real_estate.csv

### **3. Run the notebooks**

Open in Jupyter, VS Code, or Google Colab.

---

## 📝 **Future Enhancements**

* Predictive price modeling (Linear Regression, Random Forest)
* Web dashboard (Streamlit)
* Geographic heatmaps using Folium
* Automated scraper with scheduling

---

## 👨‍💻 **Authors**

**Mushfiq Azam**
(BSc in CSE, North South University)

---

## ⭐ **If you find this project helpful, consider giving it a star!**

---
