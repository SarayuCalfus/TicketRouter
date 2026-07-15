I am building an AI project for my internship evaluation.

You are my senior software engineer.

Your job is NOT to generate the whole project at once.

Your job is to help me build a production-quality application one file at a time.

Whenever I ask for a file, generate ONLY that file and wait for my confirmation before moving to the next one.

------------------------------------------------------------

PROJECT NAME

TicketRouter

Tagline:

AI Support Intelligence Dashboard

------------------------------------------------------------

PROJECT OVERVIEW

Customer support teams spend a lot of time manually reading support tickets, deciding their category, assigning them to the correct team, prioritizing them, and replying to customers.

This project uses an LLM to automate that workflow.

Instead of only routing tickets, the application should function as an AI support assistant.

The AI should analyze every ticket and return structured JSON which will power the dashboard.

------------------------------------------------------------

TECH STACK

Python

Streamlit

OpenAI API

python-dotenv

Pandas

Plotly

CSV

JSON

------------------------------------------------------------

CURRENT FOLDER STRUCTURE

ticketrouter/

│

├── app.py

├── router.py

├── validator.py

├── analytics.py

├── csv_handler.py

├── prompts.py

├── ui.py

│

├── pages/

│   ├── 1_Route_Ticket.py

│   ├── 2_Analytics.py

│   └── 3_History.py

│

├── data/

│   ├── ticket_history.csv

│   └── sample_tickets.csv

│

├── assets/

│

├── .env

├── requirements.txt

├── README.md

└── .gitignore

------------------------------------------------------------

RESPONSIBILITY OF EACH FILE

app.py

Main Streamlit entry point.

Responsible only for navigation, page configuration, session state and launching the application.

No AI logic.

------------------------------------------------------------

router.py

Contains all OpenAI API calls.

Receives a support ticket.

Creates prompts.

Calls the LLM.

Returns validated JSON.

No UI code.

------------------------------------------------------------

validator.py

Responsible for validating AI responses.

Ensure valid JSON.

Handle malformed JSON.

Retry if necessary.

Provide fallback response.

------------------------------------------------------------

prompts.py

Contains ALL prompt templates.

System Prompt

Ticket Routing Prompt

Weekly Insights Prompt

Batch Processing Prompt

Reply Generation Prompt

No Python logic besides prompt strings.

------------------------------------------------------------

analytics.py

Responsible for dashboard metrics.

Category counts.

Priority counts.

Sentiment counts.

Average confidence.

Weekly statistics.

Trend calculations.

------------------------------------------------------------

csv_handler.py

Responsible for

Saving ticket history

Loading history

CSV export

CSV import

Batch processing

JSON export

------------------------------------------------------------

ui.py

Contains reusable Streamlit UI components.

Cards

Metrics

Badges

Tag chips

Status indicators

Color helpers

No business logic.

------------------------------------------------------------

PAGE 1

Route Ticket

User pastes a support ticket.

Clicks Route Ticket.

The application displays

Category

Priority

Assigned Team

Sentiment

Confidence

Needs Human Review

Tags

Ticket Summary

Suggested Reply

AI Reasoning

Buttons

Save

Download JSON

------------------------------------------------------------

PAGE 2

Analytics Dashboard

Display

Total Tickets

High Priority Tickets

Average Confidence

Needs Human Review

Charts

Category Distribution

Priority Distribution

Sentiment Distribution

Weekly AI Insights

------------------------------------------------------------

PAGE 3

History

Display previous tickets.

Search.

Filter.

Download CSV.

Download JSON.

------------------------------------------------------------

AI OUTPUT

The AI MUST return ONLY valid JSON.

Never markdown.

Never explanation.

Schema

{
  "category": "",
  "priority": "",
  "assigned_team": "",
  "sentiment": "",
  "confidence": "High | Medium | Low",
  "needs_human_review": false,
  "summary": "",
  "tags": [],
  "auto_reply": "",
  "reason": ""
}

------------------------------------------------------------

EDGE CASES

Handle these gracefully.

1.

Angry customer.

2.

Very short ticket.

Example

"Help"

3.

Ambiguous ticket.

Example

"Nothing works."

------------------------------------------------------------

REQUIRED FEATURES

✔ Ticket Classification

✔ Priority Detection

✔ Team Assignment

✔ Sentiment Analysis

✔ AI Ticket Summary

✔ AI Suggested Reply

✔ AI Tags

✔ Confidence Level

✔ Human Review Recommendation

✔ Dashboard Analytics

✔ Weekly AI Insights

✔ CSV Export

✔ CSV Import

✔ Batch Ticket Processing

------------------------------------------------------------

USER INTERFACE

Professional.

Modern.

Clean.

Minimal.

Use Streamlit containers.

Columns.

Metrics.

Expanders.

Status badges.

Icons.

Sidebar navigation.

Do NOT display raw JSON by default.

Instead present a polished dashboard.

Provide an optional Developer Mode that displays the raw JSON returned by the AI.

------------------------------------------------------------

CODING STANDARDS

Use Python best practices.

Type hints.

Functions.

Docstrings.

Meaningful variable names.

Proper error handling.

Avoid duplicated code.

Separate UI from business logic.

Keep every file focused on one responsibility.

------------------------------------------------------------

IMPORTANT

Do NOT generate multiple files.

Generate only the file I request.

Before writing code,

first explain

1. Why the file exists

2. What its responsibility is

3. How it interacts with the other files

Then generate the complete code.

Do not leave TODOs or placeholders unless I specifically request them.

Assume this project will be demonstrated to an internship mentor and should look like production-quality software rather than a beginner assignment.

# TicketRouter Development Tasks

## Phase 1
- [ ] Create app.py
- [ ] Configure Streamlit
- [ ] Sidebar navigation
- [ ] Session state

## Phase 2
- [ ] prompts.py
- [ ] router.py
- [ ] validator.py

## Phase 3
- [ ] Route Ticket page
- [ ] Dashboard cards
- [ ] Summary
- [ ] Sentiment
- [ ] Tags

## Phase 4
- [ ] Analytics
- [ ] CSV Export
- [ ] History

## Phase 5
- [ ] Weekly AI Insights
- [ ] Batch Upload
- [ ] README
- [ ] GitHub