"""Sample customers for demos. The deploy page can load these with one click.

Fernleaf Software, Acme Outdoor Gear and Kestrel Logistics are made-up companies. Fernleaf is the
sample shown on the live site (an assistant and a code reviewer). Acme is a second, smaller company used
by the tests to prove that one company's documents and memory never reach another's. Kestrel is a
second evaluation corpus of a different kind (a long employee handbook full of rules and exceptions),
so search and answer quality are not judged on one document set alone. Neither is deployed.
"""
import standards

FERNLEAF_KNOWLEDGE = """
## About this assistant
This assistant answers questions about Fernleaf Software and its product, Fernleaf, using the company's help documents. Fernleaf Software is a made-up company used to demonstrate SkyMind. For anything not covered here, it points you to Fernleaf's support team.

## About Fernleaf
Fernleaf Software is a startup based in Austin, Texas, founded in 2021 by Maya Chen and Arjun Patel. It makes Fernleaf, an all-in-one tool for small teams to plan projects, track time and send invoices. Fernleaf is used by agencies, consultants and small product teams of 3 to 200 people.

## Company size and customers
Fernleaf Software has 48 employees and more than 3,200 paying customer teams in 41 countries. About 70 percent of customers are agencies and consultancies. The company raised a $6 million seed round in 2023.

## Product modules
Fernleaf has 14 modules: Projects, Tasks, Boards, Timelines, Time Tracking, Timesheets, Invoicing, Expenses, Client Portal, Docs, Forms, Reports, Automations and Integrations. Every plan includes Projects, Tasks, Boards and Docs; the other modules depend on the plan.

## How to set up a new workspace
To set up a new workspace, sign up at the Fernleaf website with your work email, choose a workspace name, then pick a template (Agency, Consulting or Product Team) or start blank. Next, invite your team from Settings, then Members, then Invite, and give each person a role. Finally, connect your calendar and any integrations you use, and create your first project. Most teams finish setup in about 15 minutes.

## Pricing plans
Fernleaf has three pricing plans available: Starter, Team and Business. The Starter plan is free for up to 3 users and 5 projects. The Team plan costs $12 per user per month billed yearly, or $15 per user per month billed monthly, and adds Time Tracking, Invoicing and Automations. The Business plan costs $24 per user per month billed yearly and adds single sign-on (SSO), advanced reports, audit logs and priority support. How much you pay depends on the plan and the number of users.

## Pricing contact
For questions about plans, quotes or larger teams, contact the sales team at sales@fernleaf.example or book a call from the Pricing page. Sales replies within one business day, Monday to Friday, 9 AM to 6 PM Central Time.

## Enterprise plans
Teams of more than 200 people can ask for an Enterprise plan with custom pricing, a dedicated success manager and a custom contract. This assistant does not quote Enterprise prices; contact sales for a quote.

## Billing and invoices
Fernleaf bills by credit card or, on yearly Business plans, by bank transfer. Your Fernleaf invoices are emailed to the billing owner and can be downloaded from Settings, then Billing. Prices do not include sales tax or VAT, which is added where required.

## Free trial
Every new workspace gets a 14-day free trial of the Business plan, with no credit card needed. When the trial ends, the workspace moves to the free Starter plan unless you choose a paid plan, and no data is deleted.

## Upgrading or downgrading
You can upgrade at any time from Settings, then Billing, and the new features turn on immediately; you pay only the prorated difference. Downgrades take effect at the end of the current billing period.

## Cancelling a subscription
To cancel, the billing owner goes to Settings, then Billing, then Cancel subscription. The workspace stays on the paid plan until the end of the period you paid for, then moves to Starter. Yearly plans cancelled within 30 days of payment get a full refund.

## Discounts for startups and nonprofits
Registered nonprofits get 50 percent off the Team and Business plans. Startups less than two years old with under $1 million in funding get 30 percent off for their first year. Students and teachers can use the Team plan free with a school email address.

## Integrations
Fernleaf connects with Slack, Microsoft Teams, Google Calendar, Outlook Calendar, GitHub, GitLab, QuickBooks, Xero, Stripe and Zapier. Integrations are set up from Settings, then Integrations, by an admin.

## API and developer docs
Fernleaf has a REST API and webhooks on the Team and Business plans. API keys are created in Settings, then Developer. The API allows 100 requests per minute per workspace. Documentation is in the Developer Center.

## Mobile apps
Fernleaf has free mobile apps for iPhone (iOS 16 or later) and Android (Android 11 or later). The apps support tasks, comments, time tracking and approvals; invoicing and reports are web only.

## Team roles and permissions
Fernleaf has four roles: Owner, Admin, Member and Guest. Owners manage billing; Admins manage members, settings and integrations; Members work on projects they belong to; Guests (for example clients) see only the projects shared with them and are free on all plans.

## Storage limits
Starter workspaces get 2 GB of file storage, Team workspaces get 100 GB, and Business workspaces get 1 TB. A single uploaded file can be up to 250 MB.

## Data export and backups
Admins can export all workspace data as CSV and JSON from Settings, then Export. Fernleaf backs up all data every hour and keeps backups for 35 days. Deleted projects can be restored from the Trash for 30 days.

## Data security and compliance
Fernleaf encrypts data in transit (TLS 1.3) and at rest (AES-256). Data is hosted in the United States, with a European Union region available on the Business plan. Fernleaf has a SOC 2 Type II report, available to customers on request.

## Privacy and GDPR
Fernleaf follows GDPR and signs a Data Processing Agreement with customers on request. Fernleaf never sells customer data or uses it to train AI models. Privacy questions go to privacy@fernleaf.example.

## Accessibility
The Fernleaf web app aims to meet WCAG 2.2 level AA. It supports keyboard navigation, screen readers and a high-contrast theme. Report accessibility problems to support.

## Uptime and status page
Fernleaf targets 99.9 percent uptime each month, and Business plans have this in their service level agreement. Live status, incidents and planned maintenance are posted on the Fernleaf status page.

## Customer support hours
Support is available by chat and email at support@fernleaf.example, Monday to Friday, 8 AM to 8 PM Central Time. Starter and Team customers get a first reply within one business day; Business customers get priority support with a first reply within 4 hours.

## Login, passwords and SSO
If you forget your password, click Forgot password on the login page and follow the email link, which expires after 1 hour. Two-factor authentication can be turned on in your profile, and admins can require it for everyone. Business plans support single sign-on (SSO) with Google Workspace, Microsoft Entra ID and Okta.

## Help center and webinars
The Help Center has step-by-step guides and short videos. Fernleaf runs a free 45-minute onboarding webinar every Tuesday at 11 AM Central Time; sign up from the Help Center.

## Fernleaf Summit, November 16, 2026
Fernleaf Summit, the company's yearly customer event, takes place on Monday, November 16, 2026, from 9:00 AM to 5:00 PM in Harbor Hall at the Austin Convention Center. It includes product talks, a roadmap keynote by the founders, hands-on workshops and a customer awards session. Tickets are free for customers; register from the Events page.

## Product roadmap 2027
Planned for 2027: AI meeting notes linked to tasks, resource planning across projects, a client approval flow for invoices, and an offline mode for the mobile apps. Dates can change; the roadmap is updated every quarter.

## Release notes
Fernleaf releases updates every two weeks. Release notes are posted in the app under What's New and in the Help Center. Recent releases added recurring tasks, invoice reminders and a dark theme.

## Careers at Fernleaf
Fernleaf Software is hiring engineers, designers and customer success staff. The team works remotely across the United States and Canada, with an office in Austin. Open roles are listed on the Careers page.

## Partner program
Agencies and consultants who set up Fernleaf for clients can join the Partner program for a 20 percent revenue share, a free Business workspace and a listing in the partner directory.

## Referral program
Refer another team and you both get one month of your current plan free when they start a paid plan. Find your referral link in Settings, then Referrals.

## Office locations
Fernleaf's head office is at 500 Congress Avenue, Suite 1200, Austin, Texas 78701. The company also has a small office in Toronto, Canada.
"""

ACME_KNOWLEDGE = """
## About Acme Outdoor Gear
Acme Outdoor Gear is a fictional company used for demos. It sells tents, backpacks, hiking boots and camping equipment online and in two stores.

## Shipping
Shipping is free on orders over $50. Standard shipping takes 3 to 5 business days within the United States. Express shipping takes 1 to 2 business days and costs $15. Orders placed before 2 PM on a business day ship the same day. We do not ship to PO boxes outside the United States.

## Returns and refunds
You can return unused items in their original packaging within 30 days of delivery for a full refund. Start a return from the Orders page of your account or contact support. Refunds go back to your original payment method within 5 to 7 business days after we receive the item. Sale items can be exchanged but not refunded.

## Warranty
All Acme backpacks and tents carry a 1-year warranty against defects in materials and workmanship. The warranty does not cover normal wear, damage from misuse, or accidents. To make a claim, send your order number and a photo of the defect to support.

## Store hours and locations
The Denver store is open Monday to Saturday 9 AM to 6 PM and Sunday 11 AM to 5 PM. The Austin store is open Monday to Saturday 10 AM to 7 PM and closed on Sunday. Both stores are closed on Thanksgiving and Christmas Day.

## Contact support
Email support@acme.example or call 555-0100, Monday to Friday 8 AM to 8 PM Central. Live chat is available on weekdays. Typical email response time is one business day.

## Gift cards and promotions
Gift cards never expire and can be used online or in stores. Promo codes cannot be combined, and they do not apply to gift card purchases.
"""

ACME_ENGINEERING_RULES = """
## About these rules
Engineering rules for the Python services the Fernleaf engineering team builds and maintains, SkyMind included. Reviews cite these rules by section title.

## Security rules
Never write API keys, passwords or tokens in code; read them from environment variables (os.environ) and keep them in the secrets manager. A key that was ever committed must be rotated the same day. Never build SQL with string formatting or +; always use parameterised queries. Never call eval() or exec() on anything a user can influence. Validate every input from users (student IDs, course numbers, form fields) before using it.

## Error handling and logging
No bare except: catch the specific exception you expect. Never silently ignore an error; log it with the logging module, not print(). Customer-facing errors must not show stack traces or internal details.

## HTTP calls and performance
Every HTTP call needs a timeout (10 seconds for partner APIs). Never make network or database calls inside a loop over records; batch them. Cache prices for at most 5 minutes.

## Python style
Follow PEP 8 with a maximum line length of 100 characters. Use type hints on public functions and a one-line docstring explaining what the function does. Names are snake_case for functions and variables. Keep functions under 50 lines. Compare with None using "is None". No TODO or FIXME in merged code: finish it or link a ticket.

## Money and prices
Store and calculate money as integer cents or Decimal, never float. Round only when displaying. Discounts can never make a price negative.

## Testing
Every bug fix comes with a test that fails before the fix. Use pytest. New code in sign-in, payments or anything that costs money needs tests for the normal case, an empty or zero case, and an invalid input case.

## Pull requests
Keep pull requests under 400 changed lines. Describe what changed and why, and link the ticket. At least one reviewer must approve; sign-in and payment changes need two.
"""

ACME_GOALS = """
## Goals for 2027
Acme Outdoor Gear wants to grow repeat customers by 20%, sell more to first-time campers, and cut product returns, which are mostly tents returned because they were the wrong size. The marketing budget is small, so ideas should be cheap to test.

## Customers
Most customers are 25 to 45, buy online, and camp a few weekends a year. A growing group are first-time campers who don't know what gear they need. Customers often ask which tent size fits their group.

## Limits
Acme has two stores (Denver and Austin), a small support team, and no mobile app. Any new idea must work with the existing website and stores.
"""

KESTREL_KNOWLEDGE = """
## About this handbook
This is the employee handbook of Kestrel Logistics, a made-up freight and warehousing company used to test SkyMind on long policy documents. It applies to all employees in the United States unless a section says otherwise. If a local law gives you more than this handbook does, the law applies. Questions about anything not covered here go to People Operations.

## About Kestrel Logistics
Kestrel Logistics moves and stores freight for retailers and manufacturers. It was founded in 2009 in Columbus, Ohio, where its head office still is, and it runs six warehouses (Columbus, Indianapolis, Memphis, Dallas, Reno and Allentown) and a fleet of 420 trucks. Kestrel has about 2,300 employees: roughly 1,500 in warehouses, 500 drivers and 300 in offices.

## Employment types
Kestrel has four employment types. Full-time employees work 40 hours a week. Part-time employees work fewer than 30 hours a week. Seasonal employees are hired for the October to January peak and their contract ends on January 31. Interns work up to 12 weeks in summer. Benefits in this handbook apply to full-time employees unless the section says otherwise; part-time employees who work at least 20 hours a week get paid time off at half the full-time rate.

## Probation period
Every new employee starts with a 90-day probation period. During probation your manager meets you every 30 days to review your progress. Probation can be extended once by up to 60 more days. Paid time off builds up during probation, but you cannot take vacation days until probation ends, except for sick leave and bereavement leave.

## Working hours and shifts
Office hours are 9 AM to 5:30 PM, Monday to Friday, with a 30-minute unpaid lunch. Warehouses run three shifts: first shift 6 AM to 2:30 PM, second shift 2 PM to 10:30 PM, and third shift 10 PM to 6:30 AM. Second shift is paid an extra $1.50 an hour and third shift an extra $2.50 an hour. Shift swaps must be approved by the shift supervisor at least 24 hours in advance.

## Overtime
Hourly employees are paid 1.5 times their normal rate for hours over 40 in a week, and 2 times their normal rate for hours worked on a public holiday. Overtime must be approved by a supervisor before it is worked, except in an emergency. During the October to January peak, warehouse employees may be scheduled for up to 10 hours of overtime a week with 7 days' notice.

## Pay and payroll
Employees are paid every two weeks, on Friday, by direct deposit. Pay stubs are in the Kestrel Hub app under Pay. If a payday falls on a public holiday, you are paid on the working day before. Report a pay error to payroll@kestrel.example within 30 days; corrections are paid in the next pay run, or within 3 working days if the error is more than $200.

## Paid time off
Full-time employees earn paid time off (PTO) every pay period. In years 1 and 2 you earn 15 days a year; in years 3 to 5, 20 days; after 5 years, 25 days. You can carry over up to 5 unused days into the next year; anything above 5 days is lost on December 31. Request PTO in Kestrel Hub at least 2 weeks ahead for 3 or more days in a row. Warehouse PTO between November 15 and January 5 needs director approval.

## Sick leave
Sick leave is separate from PTO. Full-time employees get 10 sick days a year and part-time employees 5, available from the first day of work. Sick days do not carry over. You need a doctor's note only for more than 3 sick days in a row. Sick leave can also be used to care for a sick child, partner or parent.

## Public holidays
Kestrel observes 10 paid public holidays: New Year's Day, Martin Luther King Jr. Day, Memorial Day, Juneteenth, Independence Day, Labor Day, Thanksgiving, the day after Thanksgiving, Christmas Eve and Christmas Day. Warehouse employees who work on a public holiday are paid double time and get another day off within 60 days.

## Parental leave
Employees with at least 6 months of service get 16 weeks of fully paid parental leave after the birth, adoption or foster placement of a child. It can be taken in one block or in up to three blocks within 12 months of the child's arrival. Tell your manager and People Operations at least 30 days before the leave starts when you can. You can return to the same or an equivalent job.

## Bereavement leave
After the death of a close family member (partner, child, parent, sibling or grandparent) you get 5 paid days off. For other relatives and close friends you get 2 paid days. Bereavement leave does not need advance notice and does not use your PTO or sick leave.

## Jury duty and voting
Kestrel pays your normal pay for up to 10 days of jury duty a year; show your jury summons to your manager. Employees get up to 2 hours of paid time off to vote in any public election if their shift does not leave 3 free hours while polls are open.

## Health insurance
Full-time employees can join the Kestrel health plan from the first day of the month after they start. Kestrel pays 80 percent of the premium for employees and 60 percent for family members. There are two plans: Standard, with a $1,500 deductible, and Plus, with a $500 deductible. Open enrollment runs every year from November 1 to November 15.

## Dental and vision
Dental and vision cover start at the same time as health insurance. Kestrel pays 100 percent of the dental premium for employees. Vision cover includes one eye exam a year and up to $150 a year for glasses or contact lenses.

## Retirement plan (401k)
All employees aged 21 or older can join the 401(k) plan after 30 days. Kestrel matches 100 percent of the first 4 percent of pay you put in. Your own contributions are always yours; the company match vests fully after 2 years of service.

## Employee assistance program
The employee assistance program (EAP) gives free, confidential counseling: up to 6 sessions per issue each year, for employees and their household. It also helps with legal and money questions. Call 1-800-555-0142 any time, day or night. Your manager is not told that you used it.

## Remote and hybrid work
Office employees can work from home up to 2 days a week with their manager's agreement. Warehouse and driver roles are on site. Remote days must be in the United States. Kestrel gives hybrid employees a one-time $300 allowance for a desk or chair, and pays $40 a month toward home internet.

## Travel and expenses
Book work travel through the Kestrel travel portal at least 14 days ahead when you can. Flights under 6 hours are economy class. The daily meal allowance is $60 within the United States. Mileage in your own car is paid at $0.67 a mile. Submit expenses with receipts in Kestrel Hub within 30 days of the trip; expenses submitted later need your director's approval.

## Company vehicles and drivers
Drivers must hold a valid commercial driver's license (CDL) and pass a medical exam every 2 years. Drivers may drive no more than 11 hours in a 14-hour work period and must take a 30-minute break after 8 hours of driving. Report any accident, however small, to dispatch right away and file the incident form in Kestrel Hub within 24 hours.

## Workplace safety
Steel-toe boots and a high-visibility vest are required on every warehouse floor. Forklifts may be driven only by employees with a current Kestrel forklift certificate, renewed every 3 years. Report injuries and near misses to your supervisor the same day. Stopping work you believe is unsafe is always allowed, and you will not be punished for it.

## Drug and alcohol policy
Being under the influence of alcohol or illegal drugs at work is not allowed. Drivers and forklift operators are tested before hire, at random, and after any accident. Employees who ask for help with substance use before a test or an incident can use the EAP and take unpaid leave to get treatment without losing their job.

## Code of conduct
Treat colleagues, customers and drivers from other companies with respect. Gifts from suppliers or customers worth more than $75 must be declined or reported to your manager. Conflicts of interest, such as a second job with a competitor or a family member at a supplier, must be disclosed in Kestrel Hub.

## Harassment and discrimination
Kestrel does not tolerate harassment or discrimination of any kind. Report it to your manager, to People Operations, or anonymously through the Speak Up line at 1-800-555-0177 or speakup.kestrel.example. Every report is investigated, usually within 10 working days, and retaliation against anyone who reports in good faith is a firing offense.

## Performance reviews
Performance reviews happen twice a year, in March and September. Your manager rates you on a 4-point scale: Below, Meets, Exceeds and Outstanding. Pay raises are decided in the March review and take effect on April 1. An employee rated Below gets a written improvement plan of 60 days.

## Training and tuition
Every employee gets 24 paid hours of training a year. Full-time employees with at least 1 year of service can get up to $5,250 a year in tuition assistance for courses related to their job. If you leave Kestrel within 12 months of receiving tuition assistance, you must pay back half of it.

## Referral bonus
Refer a friend for an open job and get a bonus when they have worked at Kestrel for 90 days: $500 for warehouse and office roles and $1,500 for drivers. Referrals are submitted in Kestrel Hub before the candidate applies.

## Equipment and IT
Office employees get a laptop; warehouse leads get a rugged handheld scanner. Report a lost or stolen device to the IT service desk within 24 hours at it@kestrel.example or extension 4357. Passwords must be at least 14 characters and are never shared, including with IT.

## Leaving Kestrel
Please give 2 weeks' notice, or 4 weeks if you are a manager. Unused PTO is paid out in your final paycheck; unused sick days are not. Return all equipment, badges and fuel cards on your last day. You can ask People Operations for an exit interview.

## People Operations contact
People Operations is open Monday to Friday, 8 AM to 6 PM Eastern Time. Email people@kestrel.example, call extension 2200, or open a request in Kestrel Hub. Every warehouse also has an on-site People partner on first and second shift.
"""

EXAMPLES = [
    {
        "key": "fernleaf",
        "bot_name": "Fernleaf Assistant",
        "company": "Fernleaf Software",
        "expected_concurrent_users": 500,
        "latency_target_p95": "4s",
        "memory": "window",
        "model": "auto",
        "monthly_budget": "$600",
        "knowledge": FERNLEAF_KNOWLEDGE.strip(),
    },
    {
        "key": "acme",
        "bot_name": "Acme Support",
        "company": "Acme Outdoor Gear",
        "expected_concurrent_users": 100,
        "latency_target_p95": "4s",
        "memory": "window",
        "model": "auto",
        "monthly_budget": "$150",
        "knowledge": ACME_KNOWLEDGE.strip(),
    },
    {
        "key": "acme-review",
        "bot_name": "Fernleaf Code Reviewer",
        "company": "Fernleaf Software",
        "job": "code_review",
        "expected_concurrent_users": 20,
        "latency_target_p95": "15s",
        "memory": "window",
        "model": "strong",
        "monthly_budget": "$150",
        "knowledge": ACME_ENGINEERING_RULES.strip() + "\n\n" + standards.OWASP_TOP10.strip(),
    },
    {
        "key": "acme-ideas",
        "bot_name": "Acme Idea Partner",
        "company": "Acme Outdoor Gear",
        "job": "ideas",
        "expected_concurrent_users": 20,
        "latency_target_p95": "15s",
        "memory": "window",
        "model": "strong",
        "monthly_budget": "$100",
        "knowledge": (ACME_KNOWLEDGE.strip() + "\n\n" + ACME_GOALS.strip()),
    },
    {
        "key": "kestrel",
        "bot_name": "Kestrel HR Helper",
        "company": "Kestrel Logistics",
        "expected_concurrent_users": 300,
        "latency_target_p95": "4s",
        "memory": "window",
        "model": "auto",
        "monthly_budget": "$400",
        "knowledge": KESTREL_KNOWLEDGE.strip(),
    },
]

DEPLOY_KEYS = ("fernleaf", "acme-review")  # the sample bots that are actually deployed
