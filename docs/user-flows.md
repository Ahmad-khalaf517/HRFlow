# HRFlow — User Flows

These flows describe intended navigation. `business-rules.md` controls calculations and transitions; `security-and-data-policy.md` controls permissions and sensitive-data handling.

## 1. Roles

- Admin
- HR Manager
- Payroll Officer
- Employee

---

# 2. Authentication Flow

```text
Open Application
      ↓
Login Page
      ↓
Enter Credentials
      ↓
Validate User
   ↓         ↓
Valid      Invalid
  ↓           ↓
Dashboard   Error Message
```

The visible navigation depends on role permissions.

---

# 3. HR Manager — Create Employee Flow

```text
Dashboard
   ↓
Employees
   ↓
Add Employee
   ↓
Enter Personal Information
   ↓
Select Department
   ↓
Select Position
   ↓
Save
   ↓
Employee Profile
   ↓
Add Contract
   ↓
Enter Basic Salary + Work Schedule
   ↓
Activate Contract
```

Success condition:

Employee is payroll-ready once they have an active contract.

---

# 4. HR Manager — Attendance Flow

```text
Dashboard
   ↓
Attendance
   ↓
Select Date / Employee
   ↓
Enter Check-In
   ↓
Enter Check-Out
   ↓
System Calculates Worked Hours
   ↓
System Calculates Overtime Hours
   ↓
Save Attendance
```

Important:

Attendance does not calculate money.

---

# 5. Employee — Leave Request Flow

```text
Employee Dashboard
   ↓
My Leave
   ↓
Request Leave
   ↓
Select Leave Type
   ↓
Select Start + End Date
   ↓
Enter Reason
   ↓
Submit
   ↓
Pending
```

Then HR flow:

```text
HR Dashboard
   ↓
Pending Leave Requests
   ↓
Open Request
   ↓
Review
 ↓       ↓
Approve Reject
```

If approved and unpaid, payroll later derives the unpaid leave deduction.

---

# 6. Payroll Officer — Bonus Flow

```text
Payroll Dashboard
   ↓
Bonuses
   ↓
Add Bonus
   ↓
Select Employee
   ↓
Enter Type + Amount + Effective Date
   ↓
Save
```

The bonus is included when generating payroll for the matching period.

---

# 7. Payroll Officer — Manual Deduction Flow

```text
Payroll Dashboard
   ↓
Deductions
   ↓
Add Deduction
   ↓
Select Employee
   ↓
Choose Deduction Type
   ↓
Enter Amount + Effective Date
   ↓
Save
```

Attendance-related deductions should not be entered here unless the organization intentionally overrides them.

---

# 8. Payroll Officer — Generate Payroll Flow

```text
Payroll Dashboard
   ↓
Payroll Runs
   ↓
New Payroll
   ↓
Select Month / Period
   ↓
Create Draft
   ↓
Generate Payroll
```

For each active employee:

```text
Load Active Contract
      ↓
Get Basic Salary
      ↓
Get Default Allowances
      ↓
Get Attendance Overtime Hours
      ↓
Calculate Overtime Amount
      ↓
Get Absence Days
      ↓
Calculate Absence Deduction
      ↓
Get Approved Unpaid Leave Days
      ↓
Calculate Unpaid Leave Deduction
      ↓
Get Bonuses
      ↓
Get Manual Deductions
      ↓
Calculate Tax
      ↓
Calculate Gross Salary
      ↓
Calculate Total Deductions
      ↓
Calculate Net Salary
      ↓
Save PayrollItem Snapshot
```

After all employees:

```text
Update Payroll Totals
      ↓
Status = Calculated
```

---

# 9. Payroll Review & Approval Flow

```text
Calculated Payroll
      ↓
Payroll Officer Opens Summary
      ↓
Review Totals
      ↓
Review Employee Breakdown
      ↓
Mark Reviewed
      ↓
Approve Payroll
      ↓
Status = Approved
      ↓
Lock Standard Recalculation
```

For this small MVP, a Payroll Officer may perform calculation, review, and approval. Each action remains authorized server-side and records the responsible user/timestamp.

---

# 10. Employee — Payslip Flow

```text
Employee Dashboard
      ↓
My Payslips
      ↓
Select Payroll Period
      ↓
View Payslip
      ↓
Download PDF
```

Employees can only view their own payslips.

---

# 11. Payroll Officer — Payment Flow

```text
Approved Payroll
      ↓
Open Employee Payroll Item
      ↓
Record Payment
      ↓
Enter Amount
      ↓
Select Payment Method
      ↓
Enter Payment Date
      ↓
Optional Reference Number
      ↓
Save
```

Only approved payroll items may receive payments. The MVP records one completed payment equal to each payroll item's net salary. Payroll becomes `Paid` after every item has its full payment. Partial payments and reversals are out of scope.

---

# 12. Main Demo User Flow

Recommended final demonstration:

```text
HR Login
   ↓
Create Employee
   ↓
Assign Contract
   ↓
Record Attendance
   ↓
Employee Requests Leave
   ↓
HR Approves Leave
   ↓
Payroll Adds Bonus
   ↓
Payroll Adds Manual Deduction
   ↓
Generate Payroll
   ↓
Review Calculations
   ↓
Approve Payroll
   ↓
Employee Views Payslip
   ↓
Payroll Records Payment
```

This should be the primary end-to-end acceptance test for the project.
