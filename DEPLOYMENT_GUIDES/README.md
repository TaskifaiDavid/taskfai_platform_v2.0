# TaskifAI Platform Deployment Guides

Complete guide for deploying TaskifAI from local development to production internet deployment, including customer onboarding workflows.

---

## 📚 Guide Overview

This directory contains comprehensive deployment and operational guides:

### [01. Infrastructure Setup Guide](./01_Infrastructure_Setup.md)
**Purpose:** Server provisioning, domain configuration, and initial deployment

**Key Topics:**
- Multi-tenant architecture overview
- Server requirements (dedicated, all-in-one, cloud)
- DNS and SSL configuration
- Central login server setup
- Tenant application server setup
- Environment configuration
- Cost estimation

**When to Use:**
- First-time deployment
- Adding new tenant infrastructure
- Understanding system architecture

---

### [02. Customer Onboarding Guide - BIBBI Example](./02_Customer_Onboarding_BIBBI_Example.md)
**Purpose:** Complete walkthrough of onboarding a new customer (BIBBI case study)

**Key Topics:**
- Pre-onboarding questionnaire
- Infrastructure provisioning
- Custom vendor processor development
- Data migration from historical files
- User training and handoff
- Post-launch support

**When to Use:**
- Onboarding a new customer
- Planning customer implementation timelines
- Estimating resource requirements

**BIBBI Scenario:**
- 10+ resellers with different file formats
- Custom data extraction requirements
- Initial data migration (2020-2024)
- 5 team members to onboard
- Timeline: 8-12 days

---

### [03. Vendor Processor Customization Guide](./03_Vendor_Processor_Customization.md)
**Purpose:** Technical guide for creating custom vendor file processors

**Key Topics:**
- Processor architecture and data flow
- Creating new processors (step-by-step)
- Common patterns (multi-sheet, CSV, aggregation)
- Testing and debugging
- Best practices

**When to Use:**
- Customer has new/unique file formats
- Existing processor needs modification
- Debugging file processing issues
- Understanding vendor detection logic

**Includes:**
- Complete processor template
- Pattern solutions (multi-sheet, date parsing, EAN validation)
- Unit test examples
- Integration test scripts

---

### [04. Deployment Checklist & Troubleshooting](./04_Deployment_Checklist_And_Troubleshooting.md)
**Purpose:** Step-by-step deployment checklist and troubleshooting playbook

**Key Topics:**
- Pre-deployment checklist
- Central login deployment steps
- Tenant deployment steps
- Post-deployment verification
- Common issues and solutions
- Emergency procedures

**When to Use:**
- Deploying to production
- Troubleshooting deployment issues
- Verifying system health
- Responding to incidents

**Troubleshooting Coverage:**
- Service won't start
- File upload fails
- Tenant discovery issues
- AI chat problems
- Data not appearing

---

## 🚀 Quick Start: Deployment Roadmap

### Phase 1: Initial Infrastructure (Day 1)

1. **Purchase Domain**
   - Register `taskifai.com`
   - Configure DNS nameservers

2. **Provision Servers**
   - Central login: 1 vCPU, 1GB RAM
   - Demo tenant: 2 vCPU, 4GB RAM

3. **Setup Supabase**
   - Create tenant registry project
   - Create demo tenant project
   - Run database schemas

4. **Deploy Central Login**
   - Follow [Infrastructure Setup Guide](./01_Infrastructure_Setup.md) → Central Login section
   - Verify: `https://app.taskifai.com`

5. **Deploy Demo Tenant**
   - Follow [Infrastructure Setup Guide](./01_Infrastructure_Setup.md) → Tenant section
   - Verify: `https://demo.taskifai.com`

**Checklist:** [Deployment Checklist](./04_Deployment_Checklist_And_Troubleshooting.md#pre-deployment-checklist)

---

### Phase 2: Customer Onboarding (Days 2-12)

**Example: BIBBI Customer**

1. **Information Gathering (Days 1-2)**
   - Send onboarding questionnaire
   - Collect sample files from resellers
   - Document requirements

2. **Infrastructure Setup (Day 3)**
   - Create Supabase project for BIBBI
   - Deploy tenant server at `bibbi.taskifai.com`
   - Register in tenant registry

3. **Vendor Processor Development (Days 4-8)**
   - Analyze 10+ reseller file formats
   - Create custom processors
   - Test with sample files
   - Register in detector/factory

4. **Data Migration (Days 9-10)**
   - Upload historical files
   - Verify data accuracy
   - Run analytics validation

5. **Training & Launch (Days 11-12)**
   - User training session
   - Documentation handoff
   - Go-live announcement

**Complete Walkthrough:** [Customer Onboarding Guide](./02_Customer_Onboarding_BIBBI_Example.md)

---

### Phase 3: Ongoing Operations

1. **Monitoring**
   - Setup uptime monitoring (Uptime Robot)
   - Configure log rotation
   - Track performance metrics

2. **Maintenance**
   - Weekly health checks
   - Monthly security updates
   - Quarterly feature releases

3. **Support**
   - Week 1: Daily check-ins
   - Month 1: Weekly reviews
   - Ongoing: Email support

**Details:** [Deployment Checklist](./04_Deployment_Checklist_And_Troubleshooting.md#monitoring--alerts)

---

## 🏗️ Architecture Overview

### Multi-Tenant Design

```
┌──────────────────────────────────────────┐
│     app.taskifai.com                     │
│     (Central Login & Routing)            │
│  ┌────────────────────────────────────┐  │
│  │ • Tenant discovery                 │  │
│  │ • Authentication initiation        │  │
│  │ • User routing                     │  │
│  └────────────────────────────────────┘  │
└──────────────┬───────────────────────────┘
               │
       ┌───────┴───────┬───────────────┐
       │               │               │
       ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ demo.       │ │ bibbi.      │ │ customer3.  │
│ taskifai    │ │ taskifai    │ │ taskifai    │
│             │ │             │ │             │
│ Full App    │ │ Full App    │ │ Full App    │
│ (Isolated)  │ │ (Isolated)  │ │ (Isolated)  │
└──────┬──────┘ └──────┬──────┘ └──────┬──────┘
       │               │               │
       ▼               ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Supabase #1 │ │ Supabase #2 │ │ Supabase #3 │
│ (demo data) │ │ (bibbi data)│ │ (cust3 data)│
└─────────────┘ └─────────────┘ └─────────────┘
```

**Key Points:**
- ✅ **Isolated data** per tenant (separate Supabase projects)
- ✅ **Centralized login** for discovery and routing
- ✅ **Scalable architecture** (add tenants without affecting others)
- ✅ **Security** through RLS and tenant isolation

---

## 🎯 Common Use Cases

### Use Case 1: Deploy First Production System

**Goal:** Get TaskifAI live on the internet

**Steps:**
1. Read [Infrastructure Setup Guide](./01_Infrastructure_Setup.md)
2. Follow [Deployment Checklist](./04_Deployment_Checklist_And_Troubleshooting.md#pre-deployment-checklist)
3. Deploy central login + demo tenant
4. Verify with health checks

**Estimated Time:** 4-6 hours

---

### Use Case 2: Onboard New Customer (BIBBI)

**Goal:** Setup BIBBI with 10+ custom resellers

**Steps:**
1. Read [Customer Onboarding Guide](./02_Customer_Onboarding_BIBBI_Example.md)
2. Gather information (questionnaire)
3. Create custom vendor processors ([Processor Guide](./03_Vendor_Processor_Customization.md))
4. Migrate historical data
5. Train users

**Estimated Time:** 8-12 days

---

### Use Case 3: Add New Reseller Format

**Goal:** Customer sends new reseller file format

**Steps:**
1. Get sample file
2. Follow [Vendor Processor Guide](./03_Vendor_Processor_Customization.md) → Creating a New Processor
3. Test with sample
4. Deploy processor update
5. Notify customer

**Estimated Time:** 2-4 hours

---

### Use Case 4: Troubleshoot Upload Issue

**Goal:** File upload failing for customer

**Steps:**
1. Check [Troubleshooting Guide](./04_Deployment_Checklist_And_Troubleshooting.md#issue-2-file-upload-fails)
2. Review Celery worker logs
3. Test vendor detection
4. Verify Redis connection
5. Fix and redeploy

**Estimated Time:** 30-60 minutes

---

## 📋 Pre-Deployment Requirements

### Essential Accounts & Services

- [ ] **Domain registrar account** (Namecheap, GoDaddy, etc.)
- [ ] **Server hosting** (DigitalOcean, AWS, Hetzner)
- [ ] **Supabase account** (https://supabase.com)
- [ ] **OpenAI account** with API access
- [ ] **SendGrid account** for email notifications
- [ ] **Redis hosting** (Upstash, Redis Cloud) OR local Redis

### Technical Skills Required

- ✅ Basic Linux/Unix command line
- ✅ SSH and server management
- ✅ Nginx configuration
- ✅ Basic Python knowledge (for custom processors)
- ✅ Understanding of databases and SQL

### Estimated Costs

**Small Setup (1-3 tenants):**
- Servers: $30/month
- Supabase: $75/month
- Redis: $10/month
- Domain: $12/year
- **Total: ~$116/month**

**Medium Setup (5-10 tenants):**
- Servers: $72/month
- Supabase: $150/month
- Redis: $20/month
- **Total: ~$242/month**

---

## 🔧 Key Configuration Files

### Central Login Server
```
/var/www/taskifai-central/
├── backend/
│   ├── .env                    # API configuration
│   └── app/
│       └── core/
│           └── config.py       # Settings
├── frontend/
│   ├── .env                    # Frontend config
│   └── dist/                   # Built static files
└── /etc/nginx/sites-available/
    └── app.taskifai.com        # Nginx config
```

### Tenant Server (e.g., demo)
```
/var/www/taskifai-demo/
├── backend/
│   ├── .env                    # API configuration
│   ├── uploads/                # Uploaded files
│   └── app/
│       └── services/
│           └── vendors/        # Custom processors
├── frontend/
│   ├── .env                    # Frontend config
│   └── dist/                   # Built static files
└── /etc/nginx/sites-available/
    └── demo.taskifai.com       # Nginx config
```

---

## 🆘 Getting Help

### Documentation Order

1. **Start here:** README (you are here)
2. **First deployment:** [Infrastructure Setup](./01_Infrastructure_Setup.md)
3. **Customer onboarding:** [BIBBI Example](./02_Customer_Onboarding_BIBBI_Example.md)
4. **Custom formats:** [Vendor Processors](./03_Vendor_Processor_Customization.md)
5. **Issues:** [Troubleshooting](./04_Deployment_Checklist_And_Troubleshooting.md)

### Common Questions

**Q: Do I need a separate server for each tenant?**
A: Recommended for production. You can use one server for development/testing.

**Q: Can I use one Supabase project for all tenants?**
A: Not recommended. Each tenant should have isolated data in separate projects.

**Q: Do I need app.taskifai.com for central login?**
A: Yes, for multi-tenant routing. Without it, users login directly at tenant subdomains.

**Q: How long does onboarding take?**
A: Simple customer (standard formats): 2-3 days. Complex (BIBBI example): 8-12 days.

**Q: Can I migrate from demo to production?**
A: Yes, export data from demo Supabase and import to production.

---

## ✅ Deployment Success Checklist

After completing deployment, verify:

- [ ] Central login accessible at `https://app.taskifai.com`
- [ ] Demo tenant accessible at `https://demo.taskifai.com`
- [ ] SSL certificates valid (A+ on SSL Labs)
- [ ] Tenant discovery working
- [ ] User can login via central portal
- [ ] File upload works
- [ ] Celery worker processing files
- [ ] Analytics dashboard shows data
- [ ] AI chat functional
- [ ] Monitoring configured
- [ ] Backups scheduled
- [ ] Documentation provided to customer

---

## 🚦 Status Indicators

Throughout these guides, you'll see:

✅ **Action completed successfully**
⚠️ **Warning or caution needed**
❌ **Error or issue to resolve**
📋 **Checklist item**
🔧 **Configuration required**
💡 **Pro tip or best practice**

---

## 📞 Support

### Issues & Bugs
- GitHub Issues: `https://github.com/yourusername/taskifai-platform/issues`
- Email: support@taskifai.com

### Security Concerns
- Email: security@taskifai.com
- Please include: affected tenant, date/time, description

### Feature Requests
- Email: product@taskifai.com
- Include use case and business value

---

## 📝 Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-01-09 | Initial deployment guides created |
| | | - Infrastructure setup |
| | | - Customer onboarding (BIBBI) |
| | | - Vendor processor customization |
| | | - Deployment checklist |

---

## 🎓 Additional Resources

### External Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Supabase Documentation](https://supabase.com/docs)
- [Nginx Configuration Guide](https://nginx.org/en/docs/)
- [Let's Encrypt SSL](https://letsencrypt.org/getting-started/)
- [Celery Documentation](https://docs.celeryq.dev/)

### Project Documentation
- [Main README](../README.md) - Project overview
- [CLAUDE.md](../CLAUDE.md) - Development guide
- [Project_docs/](../Project_docs/) - Technical architecture

---

## 🏁 Next Steps

**If you're deploying for the first time:**
1. Review this README thoroughly
2. Start with [Infrastructure Setup Guide](./01_Infrastructure_Setup.md)
3. Follow [Deployment Checklist](./04_Deployment_Checklist_And_Troubleshooting.md)

**If you're onboarding a new customer:**
1. Read [Customer Onboarding Guide](./02_Customer_Onboarding_BIBBI_Example.md)
2. Customize for your customer's needs
3. Use [Vendor Processor Guide](./03_Vendor_Processor_Customization.md) for custom formats

**If you're troubleshooting:**
1. Jump to [Troubleshooting Guide](./04_Deployment_Checklist_And_Troubleshooting.md)
2. Find your issue in Common Issues section
3. Follow solution steps

---

**Good luck with your deployment! 🚀**

*For questions or feedback on these guides, contact: devops@taskifai.com*
