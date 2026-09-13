from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .models import DatasetRecord, SourceRecord
from .normalize import canonical_title, content_hash, normalize_accession, normalize_doi, normalize_pmid
from .state import DiscoveryState

@dataclass(frozen=True)
class Query:
    text: str
    start: datetime
    end: datetime
    limit: int = 50

class RateLimitError(RuntimeError):
    pass

class HTTPClient:
    def __init__(self, timeout: float = 30.0, user_agent: str = "Virelion-Intelligence/0.3") -> None:
        self.client = httpx.Client(timeout=timeout, follow_redirects=True, headers={"User-Agent": f"{user_agent} (+https://github.com/Virelion-Biotech/Virelion-Intelligence)"})

    @retry(retry=retry_if_exception_type((httpx.TransportError, RateLimitError)), stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=1, max=30), reraise=True)
    def get(self, url: str, **params: Any) -> httpx.Response:
        response = self.client.get(url, params=params)
        if response.status_code == 429:
            raise RateLimitError(f"HTTP 429 from {url}; Retry-After={response.headers.get('Retry-After', 'unspecified')}")
        response.raise_for_status()
        return response

    def close(self) -> None:
        self.client.close()

class PubMedAdapter:
    source_id = "pubmed"
    def __init__(self, http=None, state: DiscoveryState | None = None): self.http, self.state = http or HTTPClient(), state
    def search(self, query: Query) -> list[SourceRecord]:
        term = f"({query.text}) AND ({query.start.date()}[PDAT] : {query.end.date()}[PDAT])"; start = int((self.state.get(self.source_id, query.text).get('retstart') or 0)) if self.state else 0; ids=[]
        while len(ids) < query.limit:
            n=min(100, query.limit-len(ids)); r=self.http.get('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi',db='pubmed',term=term,retmode='json',retmax=n,retstart=start,sort='pub date').json(); x=[str(v) for v in r.get('esearchresult',{}).get('idlist',[])]; ids.extend(x); total=int(r.get('esearchresult',{}).get('count',len(ids)) or len(ids)); start+=len(x)
            if self.state: self.state.set(self.source_id,query.text,retstart=start,total=total,complete=start>=total)
            if not x or start>=total: break
        if not ids: return []
        data=self.http.get('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi',db='pubmed',id=','.join(ids),retmode='json').json().get('result',{}); out=[]
        for pmid in ids:
            item=data.get(pmid,{}); date=_parse_pubdate(item.get('pubdate'))
            if not item or not _within_window(date,query): continue
            title=str(item.get('title') or '').strip(); out.append(SourceRecord(source_id=f'pubmed:{pmid}',source_type='literature',title=title,url=f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/',published_at=date,publisher=item.get('fulljournalname'),authors=[str(a.get('name')) for a in item.get('authors',[]) if a.get('name')],pmid=pmid,authority='primary',content_hash=content_hash(title,pmid),tags=['pubmed']))
        return out

class EuropePMCAdapter:
    source_id='europe_pmc'
    def __init__(self,http=None,state:DiscoveryState|None=None): self.http,self.state=http or HTTPClient(),state
    def search(self,query:Query)->list[SourceRecord]:
        q=f'({query.text}) AND FIRST_PDATE:[{query.start.date()} TO {query.end.date()}]'; page=int((self.state.get(self.source_id,query.text).get('page') or 1)) if self.state else 1; out=[]
        while len(out)<query.limit:
            n=min(100,query.limit-len(out)); body=self.http.get('https://www.ebi.ac.uk/europepmc/webservices/rest/search',query=q,format='json',pageSize=n,page=page,resultType='core').json(); rows=body.get('resultList',{}).get('result',[])
            for item in rows:
                pmid,doi=normalize_pmid(item.get('pmid')),normalize_doi(item.get('doi')); title=str(item.get('title') or '').strip(); date=_parse_pubdate(item.get('firstPublicationDate'))
                if not _within_window(date,query): continue
                out.append(SourceRecord(source_id=f'europepmc:{pmid or doi or canonical_title(title)}',source_type='literature',title=title,url=f'https://europepmc.org/article/MED/{pmid}' if pmid else (f'https://doi.org/{doi}' if doi else 'https://europepmc.org/'),published_at=date,publisher=item.get('journalTitle'),authors=[a for a in str(item.get('authorString') or '').split(', ') if a],doi=doi,pmid=pmid,pmcid=item.get('pmcid'),abstract=item.get('abstractText'),authority='primary',content_hash=content_hash(title,doi,pmid),tags=['europepmc']))
            total=int(body.get('hitCount',len(out)) or len(out));
            if not rows or page*n>=total or len(out)>=query.limit:
                if self.state:self.state.set(self.source_id,query.text,page=page,total=total,complete=True)
                break
            page+=1
            if self.state:self.state.set(self.source_id,query.text,page=page,total=total,complete=False)
        return out[:query.limit]

class GEOAdapter:
    source_id='geo'
    def __init__(self,http=None,state:DiscoveryState|None=None): self.http,self.state=http or HTTPClient(),state
    def search(self,query:Query)->list[DatasetRecord]:
        body=self.http.get('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi',db='gds',term=query.text,retmode='json',retmax=query.limit,retstart=0).json(); ids=[str(v) for v in body.get('esearchresult',{}).get('idlist',[])]
        if not ids:return []
        data=self.http.get('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi',db='gds',id=','.join(ids),retmode='json').json().get('result',{}); out=[]
        for uid in ids:
            item=data.get(uid,{}); accession=normalize_accession(item.get('accession')) or f'UID{uid}'; title=str(item.get('title') or '').strip(); samples=_safe_int(item.get('n_samples'))
            out.append(DatasetRecord(dataset_id=f'geo:{accession}',source='GEO',accession=accession,title=title,url=f'https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={accession}',sample_count=samples,identity_status='UNRESOLVED',suitability_status='REVIEW_REQUIRED',metadata_notes=['Study-level discovery only; sample identity and temporal metadata require downstream GSM review.',f'Query window: {query.start.date()} to {query.end.date()}.']))
        return out

class ClinicalTrialsAdapter:
    source_id='clinicaltrials'
    def __init__(self,http=None,state:DiscoveryState|None=None): self.http,self.state=http or HTTPClient(),state
    def search(self,query:Query)->list[SourceRecord]:
        token=self.state.get(self.source_id,query.text).get('page_token') if self.state else None; out=[]
        while len(out)<query.limit:
            p={'query.term':query.text,'pageSize':min(100,query.limit-len(out)),'format':'json'}
            if token:p['pageToken']=token
            body=self.http.get('https://clinicaltrials.gov/api/v2/studies',**p).json()
            for s in body.get('studies',[]):
                proto=s.get('protocolSection',{}); ident=proto.get('identificationModule',{}); status=proto.get('statusModule',{}); nct=ident.get('nctId'); date=_parse_pubdate(status.get('studyFirstPostDateStruct',{}).get('date')) if nct else None
                if not nct or not _within_window(date,query):continue
                title=ident.get('briefTitle') or ident.get('officialTitle') or nct; out.append(SourceRecord(source_id=f'clinicaltrials:{nct}',source_type='clinical',title=str(title),url=f'https://clinicaltrials.gov/study/{nct}',published_at=date,publisher='ClinicalTrials.gov',accession=nct,authority='primary',abstract=str(proto.get('descriptionModule',{}).get('briefSummary') or '') or None,content_hash=content_hash(nct,title),tags=['clinical-trial']))
            token=body.get('nextPageToken')
            if not token:
                if self.state:self.state.set(self.source_id,query.text,page_token=None,complete=True)
                break
            if self.state:self.state.set(self.source_id,query.text,page_token=token,complete=False)
        return out[:query.limit]

class GitHubAdapter:
    source_id='github'
    def __init__(self,http=None,state:DiscoveryState|None=None): self.http,self.state=http or HTTPClient(user_agent='Virelion-Intelligence/0.3 github-search'),state
    def search(self,query:Query)->list[SourceRecord]:
        page=int((self.state.get(self.source_id,query.text).get('page') or 1)) if self.state else 1; out=[]
        while len(out)<query.limit and page<=10:
            n=min(100,query.limit-len(out)); items=self.http.get('https://api.github.com/search/repositories',q=query.text,per_page=n,page=page,sort='updated',order='desc').json().get('items',[])
            for item in items:
                full=item.get('full_name'); pushed=_parse_pubdate(item.get('pushed_at'))
                if full and _within_window(pushed,query): out.append(SourceRecord(source_id=f'github:{full}',source_type='software',title=str(full),url=str(item.get('html_url') or ''),published_at=_parse_pubdate(item.get('updated_at')),publisher='GitHub',authority='secondary',abstract=item.get('description'),content_hash=content_hash(full,item.get('pushed_at')),tags=['github','software']))
            if len(items)<n:
                if self.state:self.state.set(self.source_id,query.text,page=page,complete=True)
                break
            page+=1
            if self.state:self.state.set(self.source_id,query.text,page=page,complete=False)
        return out[:query.limit]

def _within_window(value:datetime|None,query:Query)->bool:
    if value is None:return False
    v=value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc); start=query.start.astimezone(timezone.utc) if query.start.tzinfo else query.start.replace(tzinfo=timezone.utc); end=query.end.astimezone(timezone.utc) if query.end.tzinfo else query.end.replace(tzinfo=timezone.utc); return start<=v<=end

def _safe_int(value:Any)->int|None:
    try:return int(value)
    except (TypeError,ValueError):return None

def _parse_pubdate(value:Any)->datetime|None:
    if not value:return None
    text=str(value).strip()
    for fmt in ('%Y-%m-%d','%Y-%m','%Y','%Y-%m-%dT%H:%M:%SZ','%Y-%m-%dT%H:%M:%S%z'):
        try:
            dt=datetime.strptime(text,fmt); return dt.replace(tzinfo=dt.tzinfo or timezone.utc)
        except ValueError:continue
    return None
