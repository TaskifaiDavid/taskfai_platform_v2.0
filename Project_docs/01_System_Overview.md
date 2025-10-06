# 1. System Overview

## TaskifAI Multi-Tenant SaaS Platform
**Sales Data Analytics & Intelligence Platform**

## 1.1. Core Purpose

The primary purpose of this system is to provide a multi-tenant SaaS platform that ingests, cleans, standardizes, and analyzes sales data from a variety of third-party resellers. It acts as a central hub for sales intelligence, transforming raw, inconsistent data files into a unified format suitable for analytics and reporting.

The key business goal is to provide each customer with a clear, consolidated view of product performance across all retail channels without manual data manipulation, with complete data isolation and customizable data processing rules.

## 1.2. Core Functionality

The system is designed to:
- **Ingest Data:** Allow users to upload sales reports in various formats (e.g., CSV, XLSX) from multiple vendors with automatic format detection.
- **Process and Clean Data:** Automatically apply vendor-specific transformations to standardize the incoming data. This includes mapping column names, converting data types, normalizing values, and handling multi-channel sales (online D2C and offline B2B).
- **Store Data:** Persist the cleaned, structured data in a relational database with complete user isolation.
- **AI-Powered Analysis:** Enable users to query their sales data using natural language through an AI chat interface, eliminating the need for SQL knowledge.
- **External Dashboard Integration:** Allow users to embed and manage external analytics dashboards (Looker, Tableau, Power BI, etc.) directly within the platform.
- **Automated Reporting:** Provide email notifications for upload success/failure and scheduled report generation in multiple formats (PDF, CSV, Excel).
- **Interactive Analytics:** Provide web-based dashboards for users to view aggregated sales analytics, track key performance indicators, and explore multi-channel performance.

## 1.3. Target Users

### SaaS Customers (Tenants)
The platform serves multiple independent customers (tenants), each with their own:
- **Isolated database** - Complete data separation for security and compliance
- **Custom vendor configurations** - Tailored data processing rules for their specific resellers
- **Branded subdomain** - Access via customer-specific URL (e.g., customer1.taskifai.com)
- **Dedicated user accounts** - Role-based access for their team members

### End Users (Per Customer)
Within each customer organization, the intended users include:
- **Sales Analysts:** To track performance, identify trends, and use AI chat for ad-hoc data exploration
- **Account Managers:** To monitor the sales activity of their respective reseller partners across both online and offline channels
- **Business Intelligence Teams:** To feed standardized data into larger analytics platforms and embed external dashboards
- **Management:** To get a high-level overview of company-wide sales performance through interactive dashboards and scheduled reports

## 1.4. Key Differentiators

What makes this system unique:
- **True Multi-Tenancy:** Each customer gets their own isolated database with complete data separation
- **Configurable Data Processing:** Customer-specific vendor configurations without code changes
- **Multi-Vendor Support:** Automatic detection and processing of 9+ different vendor data formats
- **Multi-Channel Analytics:** Unified view of both online (D2C ecommerce) and offline (B2B wholesale) sales
- **Natural Language Querying:** AI-powered chat interface eliminates the need for SQL knowledge
- **Dashboard Aggregation:** Single platform to access all analytics dashboards without context switching
- **Automated Data Processing:** Vendor-specific transformation rules handle complex data normalization automatically
- **Subdomain Access:** Each customer accesses via their branded subdomain (customer.taskifai.com)
