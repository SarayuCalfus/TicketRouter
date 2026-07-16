# AutoRoute – AI-Powered Smart Ticket Router

## Overview

AutoRoute is an AI-powered application that automates the routing of customer support tickets. Using a Large Language Model (LLM), it analyzes support requests, identifies the appropriate category and priority, assigns the correct support team, and provides a brief explanation for its decision.

The application reduces manual effort, improves routing consistency, and streamlines the support workflow.

---

## Features

* AI-powered ticket classification
* Automatic priority detection (High, Medium, Low)
* Intelligent team assignment
* Ticket summarization
* Sentiment analysis
* Suggested customer reply
* Confidence score and reasoning
* Batch ticket processing with CSV upload
* Adding an attachment instead of typing the ticket
* Ticket history and analytics dashboard
* Export processed results to CSV

---

## Technology Stack

* **Python**
* **Streamlit**
* **OpenAI API**
* **PostgreSQL**
* **Pandas**
* **Plotly**

---

## Project Structure

TicketRouter/
├── assets/
├── data/
│   ├── sample_tickets.csv
│   ├── ticket_export.csv
│   └── ticket_history.csv
├── database/
│   ├── __init__.py
│   ├── crud.py
│   ├── db.py
│   └── models.py
├── pages/
│   ├── 1_Route_ticket.py
│   ├── 2_Analytics.py
│   └── 3_History.py
├── .gitignore
├── AI_guidelines.md
├── analytics.py
├── app.py
├── attachments.py
├── csv_handler.py
├── duplicate_detector.py
├── prompts.py
├── README.md
├── requirements.txt
├── router.py
├── ui.py
└── validator.py


## Sample Output

json
{
  "category": "Authentication",
  "priority": "High",
  "assigned_team": "Identity Support",
  "summary": "User cannot log into their account.",
  "sentiment": "Frustrated",
  "confidence": 96,
  "reasoning": "Login issue prevents account access."
}

## Process

The application follows the workflow below:

1. **Input Ticket**
   - The user enters a support ticket manually, add an attachment or uploads a CSV file containing multiple tickets.

2. **AI Analysis**
   - The ticket is sent to the AI model, which analyzes the content and identifies:
     - Category
     - Priority
     - Assigned Team
     - Sentiment
     - Summary
     - Suggested Reply
     - Confidence Score
     - Reasoning

3. **Validation**
   - The AI response is validated to ensure it follows the required JSON format before being displayed.

4. **Storage**
   - Processed tickets are saved to a PostgreSQL database for future reference and analytics.

5. **Results**
   - Users can view the routing results, download processed CSV files, and access ticket history.

6. **Analytics**
   - The application generates visual insights such as ticket distribution by category, priority, team assignment, and sentiment.


## How to Run

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/AutoRoute.git
cd AutoRoute
```

### 2. Create a virtual environment (Optional but Recommended)

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install the required dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root and add:

```env
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=your_postgresql_database_url
```

### 5. Start the application

```bash
streamlit run app.py
```

### 6. Open the application

If it doesn't open automatically, visit:

```
http://localhost:8501
```