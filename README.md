# triagelib
API Wrapper for new Cofense Triage API.


# Setup
triagelib requires an instance of Cofense Triage within your environment, an account with Administrator access, and an API key generated from your Triage instance.

    >>>from Triage import TriageSession
    >>>triage = TriageSession(host=<hostname>, email=<email>, apikey=<api key>)


# Other Info

Calling these methods will only return results less than 7 days old unless specific parameters are set to do otherwise.

Reports are always returned in JSON format.
  

# Getting Reports
Returns all email reports in Triage inbox and processed.

    >>>reports = triage.reports()
  
Available arguments:
- tags (list) - One or more tags of processed reports to filter on.
- page (int) - The page number for the results.
- per_page (int) - The number of results rendered per page. The maximum value is 50 results per page.
- start_date (str) - The start date and time of the query. The default is six days ago.
- end_date (str) - The end date and time of the query. The default is the current time.
- report_id (int) - The Numeric ID of a Triage report.
- category_id (int) - The category ID (1-5) for processed reports.
- match_priority (int) - The highest match priority based on rule hits for the report.


# Getting Inbox Reports
Returns all reports in inbox and recon.

    >>>reports = triage.inbox_reports()
  
Available arguments:
  - page (int) - The page number for the results.
  - per_page (int) - The number of results rendered per page. The maximum value is 50 results per page.
  - start_date (str) - The start date and time of the query. The default is six days ago.
  - end_date (str) - The end date and time of the query. The default is the current time.
  - match_priority (int) - The highest match priority based on rule hits for the report.


# Getting Processed Reports
Returns reports that are already processed.

    >>>reports = triage.processed_reports()
  
Available arguments:
  - tags (list) - One or more tags of processed reports to filter on.
  - page (int) - The page number for the results.
  - per_page (int) - The number of results rendered per page. The maximum value is 50 results per page.
  - start_date (str) - The start date and time of the query. The default is six days ago.
  - end_date (str) - The end date and time of the query. The default is the current time.
  - category_id (int) - The category ID (1-5) for processed reports.
  - match_priority (int) - The highest match priority based on rule hits for the report.


# Attachments
Returns a specified attachment by attachment ID set by Triage.

    >>>attachment = triage.attachment(attachment_id=<attachment_id>, mime_type=<mime_type>)

Required arguments:
- attachment_id (int) - The numeric ID associated with the attachment.
- mime_type (str) - mime type of the attachment.


# Searching Integrations
Returns integration results for URL of hash (md5 or sha256)

    >>>integrations = triage.integration_search()

Required arguments (ONLY ONE):
- md5 (str) - md5 hash of the file being searched.
- url (str) - url being searched. DO NOT SUBMIT IF PII IN THE URL!!!
- sha256 (str) - sha256 hash of the file being searched.
