# RFPGPT

## Description

Proof-of-concept of a chat augmented with docs.fortinet.com, rfpio.com and custom documents.
The idea is to have a chatbot that can answer questions about the FortiGate product line to respond to RFPs (Response For Prososal)
The thought process is handled by langchain.
Queries are fetch from docs.fortinet.com and rfpio.com through custom langchain tools.
Each responses are embedded with OpenAI API embeddings and stored in a chromaDB.

## Tasks

- [x] Tools
  - [x] RFPIO -> scaping using selenium to handle MFA
  - [x] docs.fortinet.com -> scraping using requests and beautifulsoup
  - [x] custom file
- [ ] Web interface

## Authors

Charles Prevot <cprevot@fortinet.com>, Feb 2023
