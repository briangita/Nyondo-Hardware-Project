#  Nyondo General Hardware Management System
## Introduction

The **Nyondo General Hardware Management System is a comprehensive, role-based web application built with Django to digitize and streamline the day-to-day operations of a hardware business.

The system replaces manual processes and scattered record-keeping with a **centralized platform** that provides visibility into:

 - Sales performance
 - Inventory levels
 - Customer financial obligations
 - Business profitability

It is designed with **real-world workflows in mind**, ensuring that each user interacts only with the parts of the system relevant to their role.

---

##  Problem Statement

Many small-to-medium hardware businesses struggle with:

❌ Manual tracking of stock and sales
❌ Lack of real-time inventory visibility
❌ Poor tracking of customer balances and schemes
❌ Limited reporting and business insights
❌ Tax Compliance
❌ No structured user access control

This leads to inefficiencies, errors, and poor decision-making.

---

## Solution

This system introduces a **modular, scalable, and role-driven architecture** that:

 - Centralizes all business operations
 - Enforces structured workflows
 - Provides actionable insights through reports
 - Controls access using a robust role-based system

---

## Key Features

### Authentication & User Lifecycle Management

 - Custom user registration with role assignment
 - Admin-controlled approval system before access is granted
 - User activation and deactivation
 - Role-based login redirection
 - Secure authentication using Django’s built-in system

---

### Role-Based Access Control (RBAC)

Access is controlled using:

 - Django **Groups**
 - Custom **decorators** for backend enforcement
 - Template **filters** for frontend visibility

#### Roles:

| Role                | Responsibilities                          |
| ------------------- | ----------------------------------------- |
| **Admin**           | Full system access, user management       |
| **Accounts**        | Financial reports, profitability tracking |
| **Store Manager**   | Inventory and stock control               |
| **Sales Attendant** | Sales and customer scheme operations      |

This ensures **security, clarity, and accountability** across the system.

---

### Dashboards

Each role is presented with a tailored dashboard containing:

- Key metrics
- Summaries of operations
- Quick access to frequently used features

Examples like:

- Sales performance overview
- Stock summaries
- Financial insights

---

###  Sales Management

The sales module allows:

- Recording of transactions
- Invoice generation
- Tracking of paid vs unpaid sales
- Editing and managing existing sales records

It also includes:
- Sales reports
- Excel export functionality for external analysis

---

###  Inventory (Stock) Management

The stock system provides:

- Recording of stock receipts
- Real-time stock level tracking
- Historical tracking of stock movement

Key benefits:

- Improved inventory accuracy
- Visibility into product availability
- Foundation for low-stock alert systems

---

###  Customer Scheme Management

This module supports:

- Customer registration
- Tracking installment-based purchases
- Recording payments
- Viewing customer balances

It enables businesses to:

- Maintain a structured customer scheme 
- Generate detailed customer statements

---

### Transport Management

- Manage vehicles used in operations
- Track transport-related data
- Lay foundation for logistics tracking

---

###  Financial Reporting System

Provides insights into business performance:

- Profit & Loss reports
- VAT calculations
- Payables and receivables tracking
- Product-level profitability

All reports can be exported to Excel for further analysis.

---

##  System Architecture

The project follows a modular Django architecture, where each domain is separated into its own app:

nyondoproject/
│
├── users/        # Authentication, roles, approvals
├── sales/        # Sales logic and invoices
├── stock/        # Inventory management
├── scheme/       # Customer scheme system
├── reports/      # Financial reporting
├── transport/    # Vehicle management
│
├── templates/
├── static/
└── manage.py

### Key Architectural Decisions:

- Separation of concerns across apps
- Reusable decorators for access control
- Template filters for clean UI logic
- Server-rendered approach for simplicity and reliability

---

## Technology Stack

| Layer          | Technology             |
| -------------- | ---------------------- |
| Backend        | Django (Python)        |
| Frontend       | HTML, Bootstrap 5      |
| Database       | SQLite (Development)   |
| Authentication | Django Auth            |
| Excel Export   | OpenPyXL               |
| Styling        | Bootstrap + Custom CSS |

---

##  Installation & Setup

in the terminal 
# Clone repository
git clone <repo-url>
cd nyondoproject

# Create virtual environment
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

---

## Initial Role Setup

from django.contrib.auth.models import Group

roles = ['admin', 'sales_attendant', 'store_manager', 'accounts']

for role in roles:
    Group.objects.get_or_create(name=role)

##  Current Limitations

While functional, the system can be improved in several areas:

- SQLite database limits scalability
- No REST API layer for integrations
- No real-time notifications (e.g., low stock alerts)
- Limited audit logging for tracking user actions
- UI is functional but not fully modernized

---

##  Future Improvements

### Backend Enhancements

- PostgreSQL for production readiness
- Django REST Framework for API support
- Background task processing (Celery + Redis)
- Audit trail for system actions

---

### Frontend Enhancements

- Modern dashboard UI/UX
- Interactive charts (Chart.js)
- Improved responsiveness and mobile support

---

### Feature Enhancements

- Low stock alert system
- Unpaid invoice notifications
- Supplier & procurement management
- Multi-branch support
- Advanced analytics

---

### Security Improvements

- Granular permission system
- Login attempt limiting
- Stronger validation and auditing

---

##  Project Strengths

- Real-world business application
- Clean and scalable architecture
- Strong role-based access control
- Modular design for easy expansion
- Practical reporting system

---

##  Author

Developed as a custom business solution for managing hardware store operations by Brian Gita Asiimwe

---

##  License

This project is intended for internal/business use.
You are free to modify and extend it as needed for education pourposes

---

## Final Thoughts

This project demonstrates how Django can be used to build a complete business management system, balancing:

- Simplicity
- Structure
- Scalability

It serves as a strong foundation for evolving into a full enterprise-grade solution.

Thanks to the tutors at refactory for the knowledge shared durin the three months training program.
