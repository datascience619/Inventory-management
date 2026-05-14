Smart Inventory Management System - Dataset Documentation 
Project Overview 
Smart Inventory Management System 2026 is an advanced, AI-powered desktop application 
built with Python that revolutionizes inventory tracking, sales management, and demand 
forecasting for small to medium-sized businesses. 
 
 
�
� Dataset Structure 
 
Database Schema 
The system uses SQLite database ( 
relational structure: 
 
) with the following 
1. Product Table 
Primary inventory management table containing product information. 
 
Column Type Description 
pid INTEGER (PK) Unique product identifier 
name TEXT (UNIQUE) Product name 
price REAL Selling price per unit 
cost REAL Cost price per unit 
qty INTEGER Current quantity in stock 
min_stock INTEGER Minimum stock threshold 
max_stock INTEGER Maximum stock capacity 
reorder_point INTEGER Automatic reorder trigger level 
supplier_id INTEGER (FK) Reference to supplier 
category TEXT Product category/classification 
sku TEXT (UNIQUE) Stock Keeping Unit identifier 
last_updated TEXT Timestamp oflast modification 
 
Business Rules: 
smart_inventory_advanced. db 
 
 
 Triggers low-stock alerts when 
 Supports profit margin calculation: 
 
2. Supplier Table 
Manages supplier information and performance metrics. 
 
Column Type Description 
supplier_id INTEGER (PK) Unique supplier identifier 
name TEXT (UNIQUE) Supplier company name 
email TEXT Contact email address 
phone TEXT Contact phone number 
address TEXT Physical address 
rating REAL Performance rating (0-5 scale) 
delivery_time INTEGER Average delivery time in days 
 
Sample Data: 
 
 
3. Sales Table 
Transactional sales records for revenue tracking and demand analysis. 
 
Column Type Description 
sale_id INTEGER (PK) Unique sale transaction ID 
product_id INTEGER (FK) Reference to product sold 
quantity INTEGER Number ofunits sold 
sale_date TEXT Date and time ofsale 
revenue REAL Total revenue (price × quantity) 
customer_id INTEGER (FK) Reference to customer (optional) 
qty <= reorder_point 
 
Analytics Capabilities: 
 Daily/weekly/monthly revenue aggregation 
 Product sales velocity calculation 
 Seasonal demand pattern recognition 
 
4. Customer Table 
Customer relationship management and loyalty tracking. 
 
Column Type Description 
customer_id INTEGER (PK) Unique customer identifier 
name TEXT Customer name 
email TEXT Customer email 
phone TEXT Contact number 
loyalty_points INTEGER Accumulated loyalty points 
 
 
5. Purchase Order Table 
Tracks procurement orders and supplier delivery status. 
 
Column Type Description 
po_id INTEGER (PK) Purchase order identifier 
supplier_id INTEGER (FK) Reference to supplier 
product_id INTEGER (FK) Product being ordered 
quantity INTEGER Number ofunits ordered 
order_date TEXT Date order was placed 
expected_date TEXT Expected delivery date 
status TEXT Order status (Pending/Completed/Cancelled) 
total_cost REAL Total purchase cost 
 
 
6. InventoryAlert Table 
Automated alert system for inventory management. 
Password: admin123 
 
 Column Type Description 
alert_id INTEGER (PK) Unique alert identifier 
product_id INTEGER (FK) Product triggering alert 
alert_type TEXT Type: 'low_stock' or 'out_of_stock' 
message TEXT Alert message description 
alert_date TEXT Timestamp ofalert generation 
resolved BOOLEAN Alert resolution status 
 
Alert Triggers: 
 Low Stock: When 
 Out ofStock: When 
 
7. User Table 
User authentication and role-based access control. 
 
Column Type Description 
user_id INTEGER (PK) Unique user identifier 
username TEXT (UNIQUE) Login username 
password_hash TEXT SHA-256 hashed password 
role TEXT User role (admin/manager/user) 
email TEXT User email address 
 
Default Credentials: 
 
 
qty <= reorder_point AND qty > 0 
qty = 0 
�
� Problem Statement 
Business Challenges Addressed 
1. 
2. 
3. 
4. 
5. 
Inventory Mismanagement 
Manual tracking leading to stock discrepancies 
Lack ofreal-time visibility into stock levels 
Overstocking and understocking issues 
Demand Forecasting Gaps 
Inability to predict future demand accurately 
Reactive rather than proactive ordering 
Lost sales due to stockouts 
Supplier Management 
No centralized supplier performance tracking 
Inefficient procurement processes 
Delayed deliveries impacting business 
Financial Visibility 
Limited insights into profit margins 
No automated revenue tracking 
Difficulty in identifying profitable products 
Alert Fatigue 
Missing critical reorder points 
No automated notifications 
Manual monitoring required 
�
� Solution Approach 
Technical Architecture 
1. Data Storage Layer 
SQLite Database: Lightweight, serverless, ACID-compliant 
Relational Schema: Normalized design with foreign key constraints 
Transaction Safety: Automatic rollback on failures 
2. Business Logic Layer 
Inventory Management: 
python 
 
UPDATE product SET qty = qty - sold_quantity WHERE pid = product_id 
 
CREATE  alert( type=' low_stock' ,  product_id,  message) 
Revenue Calculation: 
python 
=
=
×
×
3. AI/ML Prediction Engine 
 
Demand Forecasting Algorithm: 
python 
Model: Random Forest Regressor ( 100 estimators) 
day_of_week:  Captures weekly seasonality 
month:  Captures monthly/seasonal patterns 
 
 
Feature Engineering: 
python 
day_of_week' = date. dayofweek 
 
 
month' = date. month 
=
=
 
 
 
4. Presentation Layer (GUI) 
Technologies: 
Tkinter: Native Python GUI framework 
ttk: Themed widgets for modern appearance 
Matplotlib: Data visualization and charting 
 
Pandas: Data manipulation and analysis 
Key Features: 
Dark/Light theme toggle 
Real-time dashboard with KPIs 
Interactive charts and graphs 
Export functionality (CSV, PDF) 
5. Monitoring System 
Background Thread: 
Runs every 5 minutes (300 seconds) 
Checks inventory levels against thresholds 
Generates and stores alerts 
Displays warnings to users 
�
� Business Impact & Insights 
Key Performance Indicators (KPIs) 
1. Total Inventory Value 
 
SELECT SUM( price × qty) as total_value FROM product 
Insight: Real-time visibility ofcapital tied up in inventory 
2. Low-Stock Items Count 
 
SELECT COUNT(*) FROM product WHERE qty <= reorder_point 
Insight: Risk assessment for potential stockouts 
3. 30-Day Revenue 
 
SELECT SUM( revenue) FROM sales 
WHERE sale_date >= date(' now' , ' - 30 days' ) 
Insight: Short-term revenue trending and performance 
4. Pending Purchase Orders 
 
SELECT COUNT(*) FROM purchase_order WHERE status = ' Pending' 
Insight: Outstanding procurement commitments 
Analytics & Reporting 
1. Sales Trend Analysis 
Visualization: Line chart showing daily revenue over 30 days 
Pattern Detection: Identifies peak sales days and seasonal trends 
Business Value: Optimize staffing and inventory during high-demand periods 
2. Inventory Health Distribution 
Visualization: Pie chart showing stock status breakdown 
Green: Healthy stock levels 
Yellow: Low stock (near reorder point) 
Red: Out ofstock 
Business Value: Quick visual assessment ofinventory health 
3. Product Performance 
Metric: Sales velocity (units/day) 
Calculation: 
Business Value: Identify fast-movers vs. slow-movers 
4. Supplier Performance 
Metrics: 
Average delivery time 
Rating (1-5 scale) 
Order fulfillment rate 
 
Business Value: Optimize supplier selection and negotiation 
Demand Forecasting Impact 
Prediction Accuracy 
Model Performance: 
Uses ensemble learning (Random Forest) for robustness 
Handles seasonality through day/month features 
Adapts to trends via rolling averages 
Business Applications: 
1. 
2. 
3. 
4. 
Proactive Ordering: Order stock before depletion 
Cash Flow Optimization: Reduce excess inventory costs 
Customer Satisfaction: Minimize stockouts 
Warehouse Planning: Optimize storage space allocation 
Example Forecast Output 
Product: Widget A - Next 30 Days 
 
 
38
 
 
 
Actionable Insight: Place purchase order for 1,300 units (with safety buffer) 
�
� Recommendations 
Immediate Implementation (0-3 months) 
1. 
2. 
3. 
Data Quality 
Establish data entry standards for consistency 
Implement validation rules for price/cost fields 
Regular database backups (daily recommended) 
Alert System Enhancement 
Configure email notifications for critical alerts 
Set up SMS alerts for out-of-stock situations 
Dashboard widget for unresolved alerts 
User Training 
Document standard operating procedures 
Train staffon AI prediction interpretation 
Create video tutorials for common tasks 
Short-term Enhancements (3-6 months) 
Advanced Analytics 
1. 
ABC analysis for inventory categorization 
2. 
Pareto analysis (80/20 rule) for product focus 
Customer segmentation by purchase patterns 
Integration Capabilities 
3. 
Barcode scanner integration 
Export to accounting software (QuickBooks, Xero) 
API development for third-party systems 
Mobile Accessibility 
Web-based interface for remote access 
Mobile app for on-the-go inventory checks 
Push notifications for critical alerts 
Long-term Strategy (6-12 months) 
1. 
2. 
3. 
Machine Learning Enhancement 
Implement deep learning for complex patterns 
Multi-product demand correlation analysis 
Price optimization using ML 
Scalability 
Migration to PostgreSQL/MySQL for larger datasets 
Cloud deployment (AWS, Azure) 
Multi-location inventory support 
Advanced Features 
Automated purchase order generation 
Supplier bid comparison system 
Predictive maintenance for perishable goods 
�
� Data Flow Diagram 
 
  
 
 
 
 
 
│ 
│ 
│ 
Business Logic Layer 
• Validation  
│ 
│ 
│ 
• Calculations  
 • Generation 
 
 
 
│ 
│ 
│ 
│ 
│ 
SQLite Database 
• Product 
• Sales 
• Supplier  
• Alerts  
 
 
│ 
│ 
│ 
│ 
│ 
│ 
│ 
│ 
│ 
AI/ML Engine 
• Feature Engineering 
• Random Forest Model 
• Demand Prediction 
│ 
│ 
│ 
│ 
�
� Technical Specifications 
Dependencies 
python 
# Core Libraries 
Python 3. 8+ 
 - pandas >= 1. 3. 0 
 
 
>= 0. 24. 0 
 - matplotlib >= 3. 4. 0 
 
python- dateutil >= 2. 8. 0 
 
System Requirements 
OS: Windows 10/11, macOS 10.14+, Linux 
RAM: Minimum 4GB 
Storage: 100MB for application + data 
Display: 1280x720 minimum resolution 
�
� Success Metrics 
Operational Efficiency 
Stockout Reduction: Target 80% decrease in out-of-stock incidents 
Inventory Turnover: Improve by 25% through better demand prediction 
Order Accuracy: 95%+ accuracy in reorder quantities 
Financial Impact 
Cost Savings: 15-20% reduction in excess inventory costs 
Revenue Protection: Prevent lost sales from stockouts 
Profit Margin Visibility: Track and optimize per-product profitability 
User Adoption 
Training Time: < 2 hours for basic proficiency 
DailyActive Users: 90%+ ofinventory staff 
User Satisfaction: Target 4.5/5 rating 
�
� Getting Started 
Installation 
bash 
# Clone repository 
git  clone  https: //github. com/yourusername/smart- inventory- system. git 
 
 
# Run application 
python  smart_inventory. py 
Initial Setup 
1. 
Login with default credentials (admin/admin123) 
2. 
3. 
4. 
5. 
Add suppliers via Suppliers tab 
Import product catalog or add manually 
Begin recording sales transactions 
Access AI predictions after accumulating 5+ sales records 
�
� License 
MIT License - See LICENSE file for details 
�
� Contributing 
Contributions welcome! Please read CONTRIBUTING.md for guidelines. 
�
� Support 
For issues and questions: 
Create GitHub issue 
Email: nafisshaiokh114@gmail.com 
Documentation: Nafees Shaikh         
Last Updated: May 2026 Version: 2.0.0 Status: Production Ready 
