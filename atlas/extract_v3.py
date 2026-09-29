"""Conservative extraction from published HTML, without scripts or hidden data."""
import re
from datetime import datetime, timedelta
from decimal import Decimal
from html.parser import HTMLParser

SOURCES = {'federal': 'https://asterian-federal-wage-site.vercel.app/',
           'bellwether': 'https://bellwether-state-wage-site.vercel.app/'}
JURISDICTIONS = {'federal': 'Asteria', 'bellwether': 'Bellwether'}
PARSER_VERSION = 'html-v3'

INSTRUCTION_PATTERNS = (
    r'ignore\s+(all\s+)?(previous|prior|system)\s+instructions',
    r'(auto.?approve|bypass\s+(human\s+)?approval)',
    r'(system\s+prompt|reveal\s+.*api\s+key)',
    r'(mark|return)\s+(all\s+)?(employees\s+)?(as\s+)?compliant',
)

def suspicious(text):
    """A triage signal, not a comprehensive prompt-injection detector."""
    return any(re.search(pattern,text,re.I) for pattern in INSTRUCTION_PATTERNS)

class Node:
    def __init__(self, tag='', attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []

    def text(self):
        if self.tag in ('script', 'style', 'noscript') or 'hidden' in self.attrs or self.attrs.get('aria-hidden') == 'true':
            return ''
        return ' '.join(' '.join(c.text() if isinstance(c, Node) else c for c in self.children).split())

    def find(self, tag=None, cls=None, id=None):
        out = []
        for c in self.children:
            if isinstance(c, Node):
                if c.tag in ('script','style','noscript') or 'hidden' in c.attrs or c.attrs.get('aria-hidden')=='true':
                    continue
                if (tag is None or c.tag == tag) and (cls is None or cls in c.attrs.get('class', '').split()) and (id is None or c.attrs.get('id') == id):
                    out.append(c)
                out.extend(c.find(tag, cls, id))
        return out

class Document(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.stack = [self.root]
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs)
        self.stack[-1].children.append(n)
        if tag not in {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}:
            self.stack.append(n)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)

def parse_date(text):
    match = re.search(r'\b([A-Z][a-z]+ \d{1,2}, \d{4})\b', text)
    if not match:
        raise ValueError('Unrecognized or missing date: ' + text)
    return datetime.strptime(match[1], '%B %d, %Y').date().isoformat()

def metadata(node):
    keys,values=node.find('dt'),node.find('dd')
    if len(keys)!=len(values) or len({k.text() for k in keys})!=len(keys):
        raise ValueError('Ambiguous source metadata')
    return {k.text(): v.text() for k, v in zip(keys,values)}

def field_span(evidence, value):
    start=evidence.find(value)
    if start<0: raise ValueError('Extracted value is not in its evidence')
    return {'quote':value,'start':start,'end':start+len(value)}

def candidate_identity(candidate, simulated):
    """Separate the authority's own rule from an informational peer-rate card edit."""
    from .store import digest
    normalized=dict(candidate)
    if candidate.get('kind')=='DAILY_RATE' and candidate.get('classification')=='RATE_REVIEW':
        normalized.pop('field_evidence',None)
        normalized['evidence']=re.sub(r'State rate \d+(?:\.\d+)? AST/hr\s*','',normalized['evidence'])
    # The identity contract is independent of the adapter release. Unchanged
    # evidence retains existing reviews; changed meaning creates a new candidate.
    return digest([normalized,simulated,'html-v2'])

def extract(html, source):
    root = Document(html).root
    if source not in SOURCES:
        raise ValueError('Unknown source')
    jurisdiction = JURISDICTIONS[source]
    candidates, observations, warnings = [], [], []
    cards = root.find(cls='rate-card')
    articles = root.find('article', cls='notice')
    if len(cards) != 1 or not articles:
        raise ValueError('Schema drift: expected one rate card and published notices')
    card = cards[0]
    meta = metadata(card)
    effective = parse_date(meta.get('Effective', ''))
    amounts = card.find(cls='rate')
    if len(amounts) != 1 or not re.fullmatch(r'\d+(?:\.\d{1,2})?', amounts[0].text()):
        raise ValueError('Ambiguous rate card amount')
    if 'AST per hour' not in card.text() or 'Covered, nonexempt employees' not in card.text() or not meta.get('Rule ID'):
        raise ValueError('Schema drift: currency, unit, coverage or rule ID missing')
    coverage = meta.get('Coverage', meta.get('Applies to', ''))
    if coverage != 'Covered, nonexempt employees':
        raise ValueError('Unsupported rate-card coverage; review the changed scope before use')
    candidates.append(dict(source=source, jurisdiction=jurisdiction, source_rule_id=meta['Rule ID'],
        source_version=meta.get('Source version'), kind='DAILY_RATE', amount=amounts[0].text(), currency='AST', unit='hour',
        effective_from=effective, effective_to=(datetime.fromisoformat(effective).date()+timedelta(days=1)).isoformat(),
        publication_date=None, publication_date_note='Not separately specified on rate card; retrieval time retained.',
        evidence=card.text(), source_url=SOURCES[source]+'#'+card.attrs.get('id',''),
        classification='RATE_REVIEW', reason='Daily snapshot; one-day validity is an explicit conservative assumption.',
        field_evidence={'amount':field_span(card.text(),amounts[0].text()),'effective_from':field_span(card.text(),meta['Effective']),
                        'currency':field_span(card.text(),'AST'),'unit':field_span(card.text(),'per hour')},
        extraction_method='deterministic-html',coverage='covered_nonexempt'))
    observations.append({'kind':'rate_card','text':card.text()})
    for article in articles:
        content = article.text()
        observations.append({'kind':'notice','text':content})
        classes = article.attrs.get('class','').split()
        ds = article.find('details')
        notice_id = ds[0].attrs.get('id') if ds else None
        spans = (article.find(cls='notice-meta') or article.find(cls='meta'))
        spans = spans[0].find('span') if spans else []
        pub = None
        if len(spans) > 1:
            try: pub = parse_date(spans[1].text())
            except ValueError: pass
        paragraphs = article.find('p')
        statement = ' '.join(p.text() for p in paragraphs)
        base = dict(source=source, jurisdiction=jurisdiction, source_rule_id=notice_id or 'unidentified-notice',
                    source_version=metadata(article).get('Source version'), amount=None, currency='AST', unit='hour',
                    effective_from=None, effective_to=None, publication_date=pub, evidence=content,
                    source_url=SOURCES[source]+'#'+(notice_id or 'notices'))
        rate_matches = re.findall(r'(\d+(?:\.\d{1,2})?) AST per hour effective ([A-Z][a-z]+ \d{1,2}, \d{4})', statement)
        # Labels are hints, not authority. Contradictory prose must not be
        # dismissed as news/proposal or silently promoted into a wage rule.
        wage_signal=bool(re.search(r'\d+(?:\.\d+)?\s*(?:AST|USD)\s*(?:per\s*hour|/\s*h)',statement,re.I))
        contradiction = (wage_signal and 'news' in classes) or bool(re.search(
            r'\bnot\s+(?:a\s+)?(?:proposal|draft)|\b(?:withdrawn|rescinded|not final)\b', statement, re.I))
        restricted = bool(re.search(r'\b(?:retail|headcount|employer.size|employers? with|only applies|applies only|except|exclud\w*)\b', statement, re.I))
        if contradiction or (rate_matches and restricted):
            base.update(kind='UNKNOWN',classification='REVIEW_REQUIRED',
                        reason='Conflicting publication signals or unsupported coverage conditions; inspect the source before deciding scope.')
        elif 'proposal' in classes or re.search(r'\b(proposed|proposal|not effective law|draft)\b',statement,re.I):
            base.update(kind='PROPOSAL',classification='NOT_LAW',reason='Proposal is not effective law.')
        elif 'news' in classes:
            base.update(kind='NEWS',classification='IRRELEVANT',reason='Operational news; not a wage rule.')
        elif 'correction' in classes:
            if len(rate_matches)==1 and pub and notice_id and re.search(r'correct|replace|supersede',statement,re.I):
                amount,date_text=rate_matches[0]
                base.update(kind='RATE_CORRECTION',classification='RATE_REVIEW',amount=amount,effective_from=parse_date(date_text),
                            correction_required=True,reason='Numerical correction: approval requires an explicit superseded version.')
            else:
                base.update(kind='CORRECTION',classification='REVIEW_REQUIRED',reason='Correction may affect coverage; never infer a rate or supersession.')
        elif 'guidance' in classes or 'Precedence ruling' in content:
            base.update(kind='GUIDANCE',classification='INTERPRETATION',reason='Interpretation or precedence evidence; not a numerical wage rule.')
        elif 'final' in classes and len(rate_matches) == 1 and pub and notice_id:
            amount, date_text = rate_matches[0]
            base.update(kind='FINAL_NOTICE',classification='RATE_REVIEW',amount=amount,effective_from=parse_date(date_text),reason='Published final notice; review before activation, including future-effective dates.')
        else:
            base.update(kind='UNKNOWN',classification='REVIEW_REQUIRED',reason='Unsupported or ambiguous notice format.')
        base['extraction_method']='deterministic-html'
        base['coverage']='covered_nonexempt'
        if base['classification']=='RATE_REVIEW':
            base['field_evidence']={'amount':field_span(content,base['amount']),
                                    'effective_from':field_span(content,rate_matches[0][1]),
                                    'currency':field_span(content,'AST'),'unit':field_span(content,'per hour')}
        candidates.append(base)
    # Preserve all visible text for change detection, including unfamiliar layouts.
    observations.append({'kind':'visible_page','text':root.text()})
    recognized={id(n) for n in cards+articles}
    def residual(node):
        if id(node) in recognized or node.tag in ('script','style','noscript') or 'hidden' in node.attrs or node.attrs.get('aria-hidden')=='true':
            return ''
        return ' '.join(' '.join(residual(c) if isinstance(c,Node) else c for c in node.children).split())
    rest=residual(root)
    # Repeated card values/dates elsewhere on the page are expected. Normalize
    # only these source-supported values, not arbitrary new rates or prose.
    for value in re.findall(r'\d+\.\d{2}',card.text()):
        rest=re.sub(r'(?<![\d.])'+re.escape(value)+r'(?![\d.])','[card amount]',rest)
    rest=re.sub(re.escape(re.search(r'[A-Z][a-z]+ \d{1,2}, \d{4}',meta['Effective'])[0]),'[card date]',rest)
    observations.append({'kind':'unmapped_text','text':rest})
    for node in root.find():
        if node.tag not in ('article','section') or id(node) in recognized: continue
        if any(id(child) in recognized for child in node.find()): continue
        content=node.text()
        if not re.search(r'\d+(?:\.\d+)?\s*AST\s*(?:per\s*hour|/\s*h)',content,re.I): continue
        if any(c['evidence']==content for c in candidates): continue
        from .store import digest
        candidates.append(dict(source=source,jurisdiction=jurisdiction,source_rule_id='unmapped-'+digest(content)[:12],
            source_version=None,kind='UNKNOWN',classification='REVIEW_REQUIRED',amount=None,currency='AST',unit='hour',
            effective_from=None,effective_to=None,publication_date=None,evidence=content,source_url=SOURCES[source],
            reason='Wage-like content outside the supported publication layout; scope and dates require review.',
            extraction_method='visible-content-guard',coverage='unknown'))
    for candidate in candidates:
        if candidate['amount'] is not None:
            candidate['amount']=format(Decimal(candidate['amount']),'.2f')
        if suspicious(candidate['evidence']):
            candidate.update(classification='SECURITY_REVIEW',reason='Source contains instruction-like text. Quarantined; no activation permitted.')
    # Record corroborating amounts; these never become duplicate approved rules.
    peer=None
    if source=='federal' and meta.get('State rate'):
        match=re.fullmatch(r'(\d+(?:\.\d{1,2})?) AST/hr',meta['State rate'])
        if match: peer={'jurisdiction':'Bellwether','amount':format(Decimal(match[1]),'.2f')}
    elif source=='bellwether':
        for comparison in root.find(cls='comparison'):
            match=re.search(r'Asterian federal (\d+(?:\.\d{1,2})?) AST',comparison.text())
            if match: peer={'jurisdiction':'Asteria','amount':format(Decimal(match[1]),'.2f')}
    if peer: observations.append({'kind':'corroboration','text':str(peer),'effective_date':effective,**peer})
    return candidates, observations, warnings
