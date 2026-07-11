# 🛡️ InfraGuardian AI

> An enterprise-grade AI-powered Cloud Operations, Security and Resilience Platform built on Azure, Terraform, Cloudflare and AWS.

![Terraform](https://img.shields.io/badge/Terraform-IaC-623CE4)
![Azure](https://img.shields.io/badge/Microsoft-Azure-0078D4)
![AWS](https://img.shields.io/badge/AWS-Warm--Standby-FF9900)
![Cloudflare](https://img.shields.io/badge/Cloudflare-DNS%20%7C%20WAF-F38020)
![GitHub Actions](https://img.shields.io/badge/GitHub-Actions-2088FF)
![Status](https://img.shields.io/badge/Status-In%20Development-success)

---

# Overview

InfraGuardian AI is a long-term platform engineering project that demonstrates how to design, deploy, secure, monitor and recover an enterprise-grade multi-service application using Infrastructure as Code.

The project combines:

- Platform Engineering
- Cloud Engineering
- Infrastructure as Code
- DevSecOps
- Zero Trust Architecture
- Artificial Intelligence
- Disaster Recovery
- Kubernetes

Rather than creating multiple unrelated projects, InfraGuardian AI evolves through multiple phases while remaining a single cohesive platform.

---

# Objectives

The primary goals of this project are to:

- Build an enterprise Terraform module library
- Deploy complete Azure environments using reusable Infrastructure as Code
- Develop a modern AI-enabled multi-service application
- Apply Zero Trust Architecture principles
- Implement enterprise monitoring and observability
- Perform offensive security testing using Kali Linux
- Design and validate Disaster Recovery across Azure and AWS
- Migrate the same application from App Service to Kubernetes
- Demonstrate modern Platform Engineering practices

---

# Key Features

## Infrastructure

- Azure Landing Zone
- Hub-and-Spoke Networking
- Private Networking
- Managed Identities
- Azure Key Vault
- Azure SQL
- Storage Accounts
- App Service
- Private Endpoints

---

## Security

- Microsoft Entra ID
- Conditional Access
- Privileged Identity Management (PIM)
- Microsoft Defender for Cloud
- Microsoft Sentinel
- Cloudflare WAF
- Zero Trust Network Design

---

## Observability

- Azure Monitor
- Log Analytics
- Application Insights
- Azure Workbooks
- Security Analytics
- AI-generated Incident Summaries

---

## AI

InfraGuardian AI is not simply a chatbot.

Artificial Intelligence is used to:

- Explain incidents
- Summarize logs
- Analyse infrastructure health
- Detect suspicious behaviour
- Recommend remediation actions
- Generate operational reports
- Assist with Disaster Recovery investigations

---

## Disaster Recovery

Primary Environment

- Microsoft Azure

Disaster Recovery Environment

- Amazon Web Services (Warm Standby)

Capabilities

- Infrastructure recreation
- Database recovery
- DNS failover
- Recovery validation
- RTO/RPO reporting

---

# High-Level Architecture

```
                    Users
                       │
                 Cloudflare
              DNS • WAF • CDN
                       │
        ┌──────────────┴──────────────┐
        │                             │
        │      Microsoft Azure        │
        │                             │
        │  Frontend                   │
        │  API Gateway                │
        │  Authentication Service     │
        │  Orders Service             │
        │  Inventory Service          │
        │  Reporting Service          │
        │  AI Service                 │
        │                             │
        │ Azure SQL                   │
        │ Key Vault                   │
        │ Storage                     │
        │ Azure Monitor               │
        │ Sentinel                    │
        └──────────────┬──────────────┘
                       │
                 Warm Standby
                    AWS
```

---

# Repository Structure

```
InfraGuardian-AI/

├── applications/
├── architecture/
├── docs/
│   ├── adr/
│   ├── 01-Project-Overview.md
│   ├── 02-Business-Requirements.md
│   ├── 03-Logical-Architecture.md
│   ├── 04-Physical-Architecture.md
│   ├── 05-Zero-Trust-Architecture.md
│   ├── 06-Networking.md
│   ├── 07-Security.md
│   ├── 08-Observability.md
│   ├── 09-Terraform-Architecture.md
│   ├── 10-CICD.md
│   ├── 11-Disaster-Recovery.md
│   └── 12-Kubernetes.md
│
├── pipelines/
├── scripts/
├── terraform/
│   ├── modules/
│   └── environments/
│
└── README.md
```

---

# Technology Stack

## Cloud

- Microsoft Azure
- Amazon Web Services
- Cloudflare

## Infrastructure as Code

- Terraform

## CI/CD

- GitHub Actions
- Azure DevOps (planned)

## Application

- ASP.NET Core *(planned)*
- REST APIs
- Azure App Service

## Database

- Azure SQL Database

## Security

- Microsoft Entra ID
- Microsoft Defender for Cloud
- Microsoft Sentinel
- Azure Key Vault

## AI

- Azure OpenAI

## Monitoring

- Azure Monitor
- Log Analytics
- Application Insights

---

# Zero Trust Principles

InfraGuardian AI follows Microsoft's Zero Trust philosophy.

✔ Verify explicitly

✔ Use least privilege

✔ Assume breach

The implementation includes:

- Identity-first authentication
- Managed Identities
- RBAC
- Private Endpoints
- Network segmentation
- Secretless authentication
- Continuous monitoring
- AI-assisted security analysis

---

# Project Roadmap

## Phase 1

- Terraform Module Library
- Azure Landing Zone
- Enterprise Networking

## Phase 2

- Multi-Service Application
- Azure App Service
- Azure SQL
- Key Vault

## Phase 3

- CI/CD
- GitHub Actions
- Automated Deployments

## Phase 4

- AI Integration
- Operational Intelligence
- Incident Summarisation

## Phase 5

- Offensive Security Testing
- Kali Linux
- Threat Detection

## Phase 6

- Disaster Recovery
- AWS Warm Standby
- RTO/RPO Validation

## Phase 7

- Kubernetes Migration
- Azure Kubernetes Service (AKS)

## Phase 8

- AI-assisted Platform Operations
- Self-healing Workflows
- Autonomous Recommendations

---

# Documentation

Detailed architecture and implementation documents can be found under the `/docs` directory.

Topics include:

- Business Requirements
- Logical Architecture
- Physical Architecture
- Zero Trust Design
- Networking
- Security
- Observability
- Disaster Recovery
- Kubernetes
- Architecture Decision Records (ADRs)

---

# Disclaimer

InfraGuardian AI is a personal engineering project created for educational and portfolio purposes.

The project is designed to demonstrate enterprise architecture, cloud engineering, DevSecOps, platform engineering and AI integration using modern Microsoft Azure technologies.

---

# License

MIT License
