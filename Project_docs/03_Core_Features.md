# 3. Core Features & User Stories

This document outlines the key features of the system from a user's perspective.

## 3.1. User Authentication

-   **As a user, I can log in to the system** with my credentials to access the application.
-   **As a user, I can log out** to securely end my session.
-   **As an administrator, I can manage user accounts** (create, deactivate).

## 3.2. Data Ingestion

-   **As a user, I can upload a sales data file** (e.g., CSV, XLSX) through the web interface.
-   **As a user, I can see the status of my upload** (e.g., "Pending," "Processing," "Completed," "Failed").
-   **As a user, I can view a history of my previous uploads.**

## 3.3. AI-Powered Data Chat

-   **As a user, I can ask questions about my sales data in natural language** without writing SQL queries (e.g., "What were total sales in May 2024?").
-   **As a user, I can have conversations with the AI** that remembers context from previous questions.
-   **As a user, I can ask comparative questions** like "Compare online vs offline sales this year."
-   **As a user, I can query specific time periods, products, or resellers** using conversational language.
-   **As a user, I receive detailed answers with calculations and insights** based on my actual sales data.
-   **As a user, I can clear my conversation history** to start fresh.

## 3.4. External Dashboard Management

-   **As a user, I can connect external analytics dashboards** (Looker, Tableau, Power BI, etc.) directly into the platform.
-   **As a user, I can view multiple dashboards** in a tab-based interface without leaving the platform.
-   **As a user, I can switch between different dashboards** with a single click.
-   **As a user, I can view dashboards in fullscreen mode** for presentations.
-   **As a user, I can open dashboards in a new tab** for multi-monitor setups.
-   **As a user, I can disconnect dashboards** I no longer need.
-   **As a user, I can set a primary dashboard** that loads by default.

## 3.5. Analytics & Reporting

-   **As a user, I can view key performance indicators (KPIs)** like total revenue, units sold, and top-selling products.
-   **As a user, I can filter data** by date range, reseller, and product.
-   **As a user, I can generate reports** in multiple formats (PDF, CSV, Excel).
-   **As a user, I can analyze both online and offline sales** through multi-channel reporting.
-   **As a user, I can view geographic performance** (countries, cities) for online sales.
-   **As a user, I can analyze marketing effectiveness** (UTM sources, campaigns, device types).

## 3.6. Error Handling

-   **As a user, when a file fails to process, I can view a detailed error report** that clearly explains issues row-by-row.
-   **As a user, I can see specific error messages** (e.g., "Row 15: Invalid product EAN," "Column 'Date': Could not parse value").
-   **As a user, I can download the original file** to fix errors and re-upload.
-   **As a user, I can view error statistics** (total errors, error types, affected rows).

## 3.7. Email Notifications & Scheduled Reports

-   **As a user, I can receive automatic email notifications** when my file is successfully processed.
-   **As a user, I can receive email notifications** if file processing fails, with a link to the error report.
-   **As a user, I can schedule automated reports** (daily, weekly, monthly) delivered to my inbox.
-   **As a user, I can choose report formats** (PDF for presentations, CSV for analysis, Excel for manipulation).
-   **As a user, I can view an audit log** of all emails sent by the system.
