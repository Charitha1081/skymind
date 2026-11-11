"""Sample customers for demos. The deploy page can load these with one click.

UNT Helper: facts collected from official UNT web pages in November 2026 (always
verify details on unt.edu). Acme Outdoor Gear is a made-up company.
"""

UNT_KNOWLEDGE = """
## About this assistant
This assistant answers questions about the University of North Texas (UNT) using a small set of facts collected from official UNT web pages in November 2026. For deadlines, prices and anything not covered here, it points you to unt.edu.

## About UNT
The University of North Texas (UNT) is a public university in Denton, Texas, in the Dallas-Fort Worth area. It was founded in 1890 as a teacher-training institute. UNT is classified as an R1 doctoral university, the highest research activity category in the Carnegie classification. Source: UNT Institutional Research fact sheet, Fall 2025.

## Size and enrollment
In fall 2025 UNT enrolled 43,567 students: 34,149 undergraduate students and 9,418 graduate students. UNT offers 243 degree programs: 116 bachelor's, 87 master's, 39 doctoral and 1 special professional program. UNT had 3,310 faculty as of November 3, 2025, including 1,344 full-time faculty. Source: UNT Institutional Research fact sheet, Fall 2025.

## Colleges and schools
UNT has 14 colleges and schools: College of Science; College of Liberal Arts and Social Sciences; Brint Ryan College of Business; Mayborn School of Journalism; College of Education; College of Health and Public Service; College of Engineering; College of Merchandising, Hospitality and Tourism; College of Music; College of Visual Arts and Design; College of Information; Toulouse Graduate School; Honors College; and College of Applied and Collaborative Studies.

## How to apply as a first-year (freshman) student
Apply with ApplyTexas or the Common Application. The application fee listed on the admissions page is $75 for U.S. citizens and residents and $85 for international applicants; it is non-refundable, and applicants with a fee waiver upload it to their myUNT portal. Send transcripts, preferably electronically. SAT or ACT scores are optional: applicants with an unweighted high school GPA above 3.0 may be considered without test scores. UNT's score codes are SAT 6481 and ACT 4136. After applying, check your admission status and any missing items in the myUNT portal, which requires activating your EUID account. Admission decisions are made on a rolling basis, and the page lists no fixed deadline, so check the UNT admissions website for current deadlines. Source: unt.edu/admissions/freshman/how-to-apply.

## Housing
UNT has 15 residence halls. Living Learning Communities let students live with others who share a major or interest, and the residence halls include study spaces for groups. The housing page does not explain how to apply or list prices, so check the UNT housing website (housing.unt.edu) for current information.

## Dining
Eagle Landing is UNT's newest and largest dining hall, with seven restaurants. Kitchen West is described by UNT as the first dining hall in Texas free of the Big 8 food allergens. The University Union has fast-food options including Burger King, Chick-fil-A, Fuzzy's Taco Shop and Jamba. For meal plans and prices, see dining.unt.edu.

## Tutoring and libraries
UNT Libraries, the Writing Center and the Learning Center offer free walk-in tutoring on the second floor of Willis Library, with no appointment needed. Hours change each semester, so check library.unt.edu/services/tutoring for current hours.

## Financial aid and tuition
Tuition, fees and financial aid change every year, so this assistant does not quote amounts. For financial aid, visit financialaid.unt.edu and check your myUNT portal for your own aid and scholarship status.

## AI Expo by SSAI, November 16, 2026
AI Expo by SSAI takes place on Monday, November 16, 2026, from 6:00 to 9:00 PM in the Emerald Ballroom of the University Union. UNT students present live, working AI project demos at tables (no slide decks), and ten organizations from across the Dallas-Fort Worth area have industry tables. The evening includes a live dance performance to open, a panel discussion called Building a Career AI Won't Replace, top teams pitching on stage to judges, and dinner. Competition prizes are 1st place $200, 2nd place $150 and 3rd place $100, all Visa gift cards. Entries to present closed on November 9, but anyone can come to watch by filling out the registration form. The expo is open to all UNT students and no AI background is needed.
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

EXAMPLES = [
    {
        "key": "unt",
        "bot_name": "UNT Helper",
        "company": "University of North Texas",
        "expected_concurrent_users": 500,
        "latency_target_p95": "4s",
        "memory": "window",
        "model": "auto",
        "monthly_budget": "$600",
        "knowledge": UNT_KNOWLEDGE.strip(),
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
]
