# Produce Data Quality & Shipment Reconciliation



An end-to-end data quality pipeline for validating produce shipment and receipt data, recording rejected records, loading accepted data into SQL Server, and reporting reconciliation results in Power BI.



This project uses synthetic data and is not connected to Nature Fresh Farms systems or data.



## Business Scenario



Shipment and receipt files must be validated before they are used for inventory, logistics, and reporting. The pipeline identifies missing IDs, duplicate IDs, invalid references, invalid dates, negative quantities, multiple receipts, and quantity discrepancies.



## Technology



\- Python 3.12

\- SQL Server 2025

\- T-SQL and SSMS

\- pyodbc

\- Power BI Desktop

\- Git and GitHub



## Results



\- 987 input records processed

\- 970 records accepted

\- 17 records rejected

\- 495 accepted shipments

\- 470 accepted receipts

\- 453 matched shipments

\- 21 pending receipts

\- 17 quantity discrepancies

\- 170 kg total shortfall



## Pipeline



CSV files â†’ Python profiling and validation â†’ SQL Server audit tables â†’ reconciliation view â†’ Power BI dashboard



## Run



```powershell

.\\.venv\\Scripts\\python.exe .\\src\\generate\_data.py

.\\.venv\\Scripts\\python.exe .\\src\\profile\_data.py

.\\.venv\\Scripts\\python.exe .\\src\\run\_pipeline.py


