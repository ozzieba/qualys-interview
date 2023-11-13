import requests
import json
from time import sleep
from pprint import pprint
from datetime import datetime
import click
from subprocess import check_call
import tempfile
def get_initial_info(site, debug=False):
    status = ''
    base_url=f'https://api.dev.ssllabs.com/api/v2/analyze?host={site}'
    if debug:
        url=f'{base_url}&startNew=on'
    else:
        url=base_url
    while (response:=requests.get(url).json())['status'] !='READY':
        url=base_url
        if debug:
            pprint(response)
        sleep(max([2]+[e.get('eta',2) for e in response.get('endpoints',[])]))
    return response
def get_endpoint_info(site):
    initial_info = get_initial_info(site)
    endpoint_infos = [
        requests.get(f'https://api.dev.ssllabs.com/api/v2/getEndpointData?host={site}&s={endpoint["ipAddress"]}').json() 
        for endpoint in initial_info.get('endpoints',[])
    ]
    return endpoint_infos

@click.command()
@click.option('--site', help='domain for which to generate report.')
@click.option('--filename', help='Where to save the report; end with .md, .html, or .pdf to get the appropriate file type')
def generate_markdown_report(site, filename):
    '''Script to generate Qualys report'''
    info=get_initial_info(site)
    endpoints=get_endpoint_info(site)
    clients={s['client']['id']: s for e in endpoints for s in e['details']['sims']['results']}
    sims = {client_id:{e['ipAddress']:sim 
                                for e in endpoints  
                                for sim in  e['details']['sims']['results']
                                if sim['client']['id']==client_id } 
                     for client_id in clients.keys()}
    report = f'''---
title:  Qualys Report
author: oz
geometry: margin=1cm
---
### Overview
|Key|Value|
| :-- | :-- |
|Domain| {site}|
|Report time| {datetime.utcfromtimestamp(info['startTime']//1000).strftime("%FT%T")} UTC
|(Worst) Grade| {min([f'{e["grade"]},' for e in endpoints])[:-1]}
|(Worst) Grade (ignoring certificate trust)| {min([f'{e["gradeTrustIgnored"]},' for e in endpoints])[:-1]}
|Earliest certificate expiration|{datetime.utcfromtimestamp(min([e['details']['cert']['notAfter']//1000 for e in endpoints])).strftime('%FT%T')}
|Vulnerabilities detected| {[vuln for vuln in ['heartbleed','heartbeat','freak','poodle','logjam'] if any(e.get(vuln) for e in endpoints)]}|

### Endpoints

| IP | Grade | Grade ignoring trust| expiration | heartbleed | heartbeat | poodle | logjam | drown|
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
{chr(10).join(f'| {e["ipAddress"]} | {e["grade"]} | {e["gradeTrustIgnored"]} |' 
f'{datetime.utcfromtimestamp(e["details"]["cert"]["notAfter"]//1000)}|{"|".join(str(e["details"][vuln]) for vuln in ("heartbleed", "heartbeat","freak","poodle","logjam"))}|' 
for e in endpoints)}

### Client

|Client ID| Client Name| Client Version|Platform|{"|".join(e["ipAddress"] for e in endpoints)}|
| --- | --- | --- | --- | --- |
{chr(10).join(
    f"""|{client_id}|{(
    clients[client_id]['client'].get('name',''))}|{(
    clients[client_id]['client'].get('version',''))}|{(
    clients[client_id]['client'].get('platform',''))}|{(
    '|'.join((
        '<span style="background:pink">Fail</span>' 
        if sims[client_id].get(e['ipAddress'],{}).get('attempts',0) 
            and sims[client_id].get(e['ipAddress'],{}).get('errorCode',0) 
        else '<span style="background:green">Success</span>') 
    for e in endpoints))}""" for client_id in list(clients.keys()))}
'''
    print(filename)
    if filename[-3:]=='.md':
        with open(filename,'w') as f:
            f.write(report)
    else:
        with tempfile.NamedTemporaryFile(mode='w',delete=False) as tmp:
            tmp.write(report)
            tmp.file.close()
            if filename[-4:]=='.pdf':
                
                open(filename,'w').write(md)
                check_call(f'/usr/bin/pandoc -f markdown {tmp.name} -t pdf -o {filename}'.split())
            elif filename[-5:]=='.html':
                check_call(f'/usr/bin/pandoc -f markdown {tmp.name} -t html -o {filename}'.split())
if __name__ == '__main__':
    generate_markdown_report()
