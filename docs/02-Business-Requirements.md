# InfraGuardian AI

# 02 – Business Requirements

**Version:** 1.0
**Status:** Draft

---

# 1. Purpose

This document defines the functional and non-functional requirements for InfraGuardian AI.

It describes the capabilities the platform must provide to support Platform Engineers throughout the cloud engineering lifecycle and serves as the foundation for the logical and physical architecture.

---

# 2. Target Users

The platform is designed for engineers responsible for designing, deploying, operating and securing cloud platforms.

Primary users include:

* Platform Engineers
* Cloud Engineers
* Cloud Architects
* DevOps Engineers
* Site Reliability Engineers (SRE)
* Security Engineers
* SOC Analysts

---

# 3. Functional Requirements

## 3.1 Platform Design

The platform shall enable engineers to:

* Design cloud infrastructure using an interactive user interface.
* Generate architecture diagrams based on the selected infrastructure.
* Validate proposed architectures against engineering best practices.
* Estimate infrastructure costs.
* Review architecture recommendations before deployment.

---

## 3.2 Platform Engineering

The platform shall enable engineers to:

* Generate Infrastructure as Code for approved infrastructure designs.
* Leverage reusable Platform Library modules when generating Infrastructure as Code.
* Review generated Infrastructure as Code before deployment.
* Store deployment definitions under version control.
* Reuse infrastructure definitions across multiple environments.

---

## 3.3 Infrastructure Deployment

The platform shall enable engineers to:

* Deploy approved infrastructure through an integrated deployment workflow.
* View deployment progress.
* View deployment history.
* Redeploy existing environments.
* Destroy environments when no longer required.

---

## 3.4 Cloud Operations

The platform shall provide:

* Infrastructure health dashboards.
* Application health dashboards.
* Resource inventory.
* Operational metrics.
* Alert visualisation.
* Operational event history.

---

## 3.5 Security Operations

The platform shall provide:

* Cloud security posture visibility.
* Security event dashboards.
* Security recommendations.
* Infrastructure security assessments.
* Security incident summaries.

---

## 3.6 Artificial Intelligence

Artificial Intelligence shall assist engineers by:

* Recommending infrastructure architectures.
* Reviewing proposed infrastructure designs.
* Explaining architectural decisions.
* Selecting appropriate Platform Library modules.
* Explaining generated Infrastructure as Code.
* Summarising operational incidents.
* Summarising security incidents.
* Providing engineering recommendations.
* Suggesting infrastructure improvements.

Artificial Intelligence shall operate as an engineering assistant and shall not automatically deploy infrastructure without user approval.

---

## 3.7 Disaster Recovery

The platform shall provide:

* Disaster Recovery readiness dashboards.
* RTO and RPO visibility.
* Backup status.
* Recovery procedure guidance.
* Disaster Recovery validation reporting.

---

# 4. Non-Functional Requirements

## Security

The platform shall:

* Implement Zero Trust security principles.
* Authenticate users using Microsoft Entra ID.
* Enforce Multi-Factor Authentication.
* Use Managed Identities where supported.
* Store secrets securely using Azure Key Vault.
* Avoid hardcoded credentials.

---

## Reliability

The platform shall:

* Support repeatable infrastructure deployments.
* Support rollback of failed deployments where practical.
* Provide deployment history for auditing purposes.

---

## Maintainability

The platform shall:

* Use reusable Platform Library modules.
* Support Infrastructure as Code.
* Support modular application architecture.
* Allow engineering standards to evolve without requiring application redesign.

---

## Observability

The platform shall:

* Generate application logs.
* Generate infrastructure logs.
* Generate deployment logs.
* Generate security logs.
* Support centralised monitoring and alerting.

---

## Performance

The platform shall:

* Provide responsive dashboards.
* Generate infrastructure definitions within an acceptable timeframe.
* Support concurrent engineering workflows.

---

## Scalability

The platform shall support:

* Multiple cloud environments.
* Multiple applications.
* Future Kubernetes deployments.
* Multi-cloud expansion.

---

# 5. Assumptions

The initial implementation assumes:

* Microsoft Azure is the primary cloud platform.
* Infrastructure is provisioned using Infrastructure as Code.
* Artificial Intelligence provides engineering assistance rather than autonomous decision making.
* Engineers remain responsible for approving infrastructure deployments.

---

# 6. Constraints

The initial implementation is constrained by:

* Personal Azure subscription limits.
* Free or low-cost cloud services where practical.
* OpenAI API usage limits.
* Development within a portfolio environment rather than a production enterprise.

---

# 7. Success Criteria

The project will be considered successful when the platform can:

* Assist engineers in designing cloud infrastructure.
* Generate Infrastructure as Code using reusable Platform Library modules.
* Deploy cloud infrastructure through an integrated deployment workflow.
* Monitor deployed infrastructure.
* Assess infrastructure security posture.
* Generate AI-assisted operational insights.
* Demonstrate Disaster Recovery capabilities.
* Support future platform expansion without major architectural redesign.

---

# 8. Relationship to Other Documents

This document defines **what** InfraGuardian AI must achieve.

Subsequent documents describe **how** these requirements are implemented.

* **03 – Logical Architecture** describes the platform services and their interactions.
* **04 – Physical Architecture** maps the logical architecture to Azure resources.
* **05 – Zero Trust Architecture** describes the security model.
* **09 – Deployment Platform** describes the Platform Library, Infrastructure as Code and deployment workflows.
* **13 – AI Architecture** describes how Artificial Intelligence supports engineering workflows throughout the platform.
