# TaskifAI Documentation

Welcome to the TaskifAI Platform documentation. This directory contains comprehensive technical documentation for developers, operators, and administrators.

## Documentation Structure

### 📚 [API Documentation](./api/)
API endpoint specifications, request/response schemas, and integration guides.

- [Authentication](./api/authentication.md) - JWT authentication and authorization
- [Uploads](./api/uploads.md) - File upload endpoints and processing
- [BIBBI Uploads](./api/bibbi-uploads.md) - B2B reseller upload system
- [Analytics](./api/analytics.md) - Analytics and reporting endpoints
- [Dashboards](./api/dashboards.md) - Dashboard configuration and management
- [AI Chat](./api/chat.md) - AI-powered SQL chat system

### 🏗️ [Architecture](./architecture/)
System design, technical architecture, and design decisions.

- [System Overview](./architecture/SYSTEM_OVERVIEW.md) - High-level architecture and components
- [Refactoring Improvements](./architecture/REFACTORING_IMPROVEMENTS.md) - Architecture evolution and optimizations

### 🚀 [Deployment](./deployment/)
Production deployment guides, infrastructure setup, and operational procedures.

- [Deployment Recommendation](./deployment/00_Deployment_Recommendation.md) - Infrastructure strategy
- [Infrastructure Setup](./deployment/01_Infrastructure_Setup.md) - Cloud infrastructure configuration
- [Customer Onboarding](./deployment/02_Customer_Onboarding_BIBBI_Example.md) - Multi-tenant onboarding
- [Vendor Processor Customization](./deployment/03_Vendor_Processor_Customization.md) - Adding new vendors
- [Deployment Checklist & Troubleshooting](./deployment/04_Deployment_Checklist_And_Troubleshooting.md) - Pre-deployment validation
- [DigitalOcean MCP Deployment](./deployment/05_DigitalOcean_MCP_Deployment.md) - DigitalOcean App Platform setup
- [Step-by-Step Deployment Guide](./deployment/STEP_BY_STEP_DEPLOYMENT_GUIDE.md) - Complete deployment walkthrough

### 📖 [Guides](./guides/)
Feature-specific guides and tutorials for developers.

*(Coming soon: User guides, integration tutorials, best practices)*

### 💻 [Development](./development/)
Implementation notes, feature summaries, and development workflows.

- [Dynamic Dashboards Implementation](./development/IMPLEMENTATION_SUMMARY_DYNAMIC_DASHBOARDS.md) - Dashboard builder feature summary

### 📘 [Reference](./reference/)
Technical reference materials, data models, and specifications.

*(Coming soon: Database schema, API reference, configuration reference)*

## Quick Links

### For New Developers
1. Start with [System Overview](./architecture/SYSTEM_OVERVIEW.md) to understand architecture
2. Review [API Documentation](./api/README.md) for endpoint specifications
3. Check [CONTRIBUTING.md](../CONTRIBUTING.md) for Git workflow and contribution guidelines
4. See [main README](../README.md) for local development setup

### For DevOps Engineers
1. Review [Deployment Recommendation](./deployment/00_Deployment_Recommendation.md) for infrastructure strategy
2. Follow [Infrastructure Setup](./deployment/01_Infrastructure_Setup.md) for cloud configuration
3. Use [Deployment Checklist](./deployment/04_Deployment_Checklist_And_Troubleshooting.md) before deployments
4. Check [DigitalOcean Deployment](./deployment/05_DigitalOcean_MCP_Deployment.md) for App Platform specifics

### For Integration Developers
1. Start with [Authentication](./api/authentication.md) for auth flows
2. Review [Uploads API](./api/uploads.md) for file processing integration
3. See [BIBBI Uploads](./api/bibbi-uploads.md) for B2B reseller integration
4. Check [Vendor Processor Customization](./deployment/03_Vendor_Processor_Customization.md) for adding new vendors

## Additional Resources

- **Main README**: [../README.md](../README.md) - Project overview and quick start
- **CLAUDE.md**: [../CLAUDE.md](../CLAUDE.md) - AI assistant guidance for this codebase
- **Contributing Guide**: [../CONTRIBUTING.md](../CONTRIBUTING.md) - Development workflow and standards

## Documentation Standards

When contributing documentation:

1. **Markdown Format**: All docs use GitHub Flavored Markdown
2. **Structure**: Use clear headings, bullet points, and code blocks
3. **Code Examples**: Include practical examples with explanations
4. **Updates**: Keep documentation in sync with code changes
5. **Links**: Use relative links for internal navigation
6. **Diagrams**: Use Mermaid for architecture diagrams when appropriate

## Need Help?

- **Issues**: Report documentation gaps or errors via GitHub Issues
- **Questions**: Contact the development team or open a discussion
- **Updates**: Submit PRs to improve documentation (see [CONTRIBUTING.md](../CONTRIBUTING.md))
