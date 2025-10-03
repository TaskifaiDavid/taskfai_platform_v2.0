# Project Rebuild Documentation

This directory contains a set of high-level design documents that serve as a blueprint for rebuilding the sales data analytics platform.

The documentation is intentionally abstract and implementation-agnostic. It focuses on the system's core purpose, architecture, and logic, rather than its current implementation details.

## Developer Guidance

A developer can use these documents to build the entire base system from the ground up. They provide a comprehensive understanding of how all components are intended to work together, ensuring the new implementation aligns with the core business requirements.

## Document Index

The documents are numbered for a sequential read:

### Core Foundation (Read First)
1.  **[01_System_Overview.md](./01_System_Overview.md):** What the system is for and who uses it.
2.  **[02_Architecture.md](./02_Architecture.md):** The main technical components and how they interact.
3.  **[03_Core_Features.md](./03_Core_Features.md):** Key user stories and system capabilities.
4.  **[04_Data_Model.md](./04_Data_Model.md):** The complete database structure including multi-channel sales.
5.  **[05_Data_Processing_Pipeline.md](./05_Data_Processing_Pipeline.md):** The abstract logic for cleaning and normalizing data.
6.  **[06_API_Specification.md](./06_API_Specification.md):** The technical contract for the backend API.

### Advanced Features (Deep Dives)
7.  **[07_AI_Chat_System.md](./07_AI_Chat_System.md):** AI-powered natural language data querying with conversation memory.
8.  **[08_Dashboard_Management.md](./08_Dashboard_Management.md):** External dashboard embedding and multi-dashboard support.
9.  **[09_Email_Reporting_System.md](./09_Email_Reporting_System.md):** Email notifications and automated report generation.
10. **[10_Security_Architecture.md](./10_Security_Architecture.md):** Security patterns, authentication, and data privacy.

### User-Facing Documentation (Customer Guide)
11. **[11_Customer_Detail_Views.md](./11_Customer_Detail_Views.md):** Comprehensive end-user guide with workflows, best practices, and troubleshooting.

### Implementation Guidance
12. **[12_Technology_Stack_Recommendations.md](./12_Technology_Stack_Recommendations.md):** Complete technology stack with rationale, alternatives, and cost analysis.

### Additional Resources
- **[PRD.md](./PRD.md):** Product Requirements Document with business context and user personas.
