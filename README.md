# The Sibling Inventory: Bakeshop ERP & Management Dashboard 🍞

## Overview
A complete, end-to-end Enterprise Resource Planning (ERP) system and Management Dashboard built for **The Sibling Inventory**, a local bakeshop. 

Rather than relying on basic CRUD operations in the frontend, this project enforces strict business logic at the database layer using advanced **SQL Server (T-SQL)** architecture, including Stored Procedures, automated Triggers, and structured Views. The backend is wrapped in a highly responsive **Streamlit** frontend for real-time operational management.

## System Architecture & Modules
The database is divided into 5 core operational modules:

1. **Supply Chain & Inventory:** Tracks raw materials, purchase orders, and supplier data. Includes automated triggers to update live kitchen stock upon batch receipt.
2. **Recipes & Manufacturing (BOM):** Maps exact ingredient quantities to specific products. Features a feasibility engine (`sp_CheckProductFeasibility`) to calculate if current stock can fulfill a requested batch size.
3. **Point of Sale (Sales & Orders):** Handles customer invoicing, tax, and discounts. **Key Feature:** When an order is placed, a database trigger automatically deducts the exact fractional quantities of raw ingredients used from the live stock based on the recipe logic.
4. **Logistics & Delivery:** A real-time dispatch board. Features validation triggers to prevent assigning deliveries to riders already on an active route.
5. **HR & Operations:** Tracks employee payroll and monitors kitchen equipment warranty lifecycles.

## Tech Stack
* **Database:** SQL Server (T-SQL, Triggers, Stored Procedures, Views)
* **Frontend:** Python, Streamlit
