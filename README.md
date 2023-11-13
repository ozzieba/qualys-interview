# Qualys Scanner report

The Python script in main.py calls the Qualys API to scan a site and produce a report; the report is output using Markdown for simplicity, and then converted using Pandoc to PDF or HTML.

The process for writing the script is detailed in Notebook.ipynb.
Note the script is not fully production ready, eg there is no handling of rate limit and server down conditions

## Q&A
### How would you scale this script and run it with resiliency to e.g. handle 1000s of domains?
For production use, the domains should come from an API endpoint or queue (eg Kafka, SQS). The service can be run on Kubernetes as a Deployment, with a Service for load balancing and an Ingress/Gateway for routing and TLS termination (if relevant). HPA can be set up to scale on queue depth

Note also that use at scale would require an agreement with Qualys to bypass the rate limit
### How would you monitor/alert on this service?
You would want to alert on:
- Qualys /info endpoint responding
- checks to a /health endpoint to make sure the system is responding
- occasional requests for a particular domain to see that the process as a whole is still working. Make sure Qualys is returning cached data for this domain, so you can measure latency.
### What would you do to handle adding new domains to scan or certificate expiry events from your service?
See above, requests should come in via HTTP or a queue
### After some time, your report requires more enhancements requested by the Tech team of the company. How would you handle these "continuous" requirement changes in a sustainable manner?
The code is kept in a git or similar repo; a deployment process is set up (eg with Jenkins or Github actions) that can deploy new versions of the service; staging and dev environments are set up for validating changes; unit and integration tests are added to the code; 
