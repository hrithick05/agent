#!/usr/bin/env python3
"""
html_summarizer.py (enhanced)

Usage:
    python html_summarizer.py input.html [-o summary.json] [--top N]

Enhanced features:
- All previous summary features PLUS:
  - top_repeated_containers with sample_nodes (3 examples)
  - attribute_stats per tag
  - field_hint_map (title, price, image, link, rating)
  - sample_extractions (heuristic extraction on sample nodes with per-field confidence)
  - text_patterns (currency, rating, emails, phones, dates, token-like strings)
  - top_xpath_examples (long text nodes)
  - clustered_subtrees (representative html + size)
  - confidence_summary (js-heavy estimation, many empty hrefs, etc)
  - forms_detailed (redacted values + likely_login_form flags)
"""
from __future__ import annotations
import sys, os, re, json, argparse
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse, urljoin
from typing import List, Dict, Any
try:
    from lxml import html as lxml_html, etree
    LXML_AVAILABLE = True
except Exception:
    LXML_AVAILABLE = False
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except Exception:
    BS4_AVAILABLE = False

# ----------------- utilities -----------------
def safe_read(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def is_absolute_url(href: str) -> bool:
    return bool(re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*://', href or ''))

def html_fragment_to_string(el) -> str:
    try:
        return etree.tostring(el, encoding='unicode', method='html')
    except Exception:
        # bs4 element fallback
        try:
            return str(el)
        except Exception:
            return ""

# ----------------- patterns -----------------
CURRENCY_PAT = re.compile(r'(?:(?:₹|Rs\.?|INR|USD|\$|€|€\s?)\s?[0-9][0-9,]*(?:\.\d+)?)', re.I)
RATING_PAT = re.compile(r'([0-9](?:\.[0-9])?)\s*(?:out of\s*5|/5|★|stars?)', re.I)
EMAIL_PAT = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}')
PHONE_PAT = re.compile(r'(?:\+?\d{1,4}[\s-]?)?(?:\d{3,4}[\s-]?\d{3,4}[\s-]?\d{3,4})')
DATE_PAT = re.compile(r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})\b', re.I)
TOKEN_LIKE_PAT = re.compile(r'\b[A-Za-z0-9-_]{40,}\b')  # long base64/hex-like tokens

# ----------------- form redaction helpers -----------------
SENSITIVE_KEYWORDS = ['password','pwd','pass','pin','ssn','account','acct','card','cvv','cv2','security','token','auth','otp']

def looks_sensitive_name(name: str) -> bool:
    if not name:
        return False
    n = name.lower()
    return any(k in n for k in SENSITIVE_KEYWORDS)

def detect_and_redact_forms_lxml(root):
    forms_summary = []
    for f in root.xpath('//form'):
        action = (f.get('action') or '').strip()
        method = (f.get('method') or 'GET').upper()
        external = False
        if action and is_absolute_url(action):
            try:
                host = urlparse(action).netloc
                external = True
            except:
                external = True
        inputs = []
        for inp in f.xpath('.//input|.//textarea|.//select'):
            t = (inp.get('type') or (inp.tag or 'input')).lower()
            name = (inp.get('name') or inp.get('id') or '').strip()
            value = (inp.get('value') or '').strip()
            suspicious = looks_sensitive_name(name) or t in ('password','hidden') or bool(re.search(r'(csrf|token|session|jwt)', name.lower()))
            redacted_value = None
            if value:
                redacted_value = 'REDACTED' if suspicious else '<<non-sensitive>>'
            inputs.append({'name': name, 'type': t, 'has_value': bool(value), 'redacted_value': redacted_value, 'suspicious': suspicious})
        fs = {'action': action, 'method': method, 'external_action': external, 'input_count': len(inputs), 'inputs': inputs}
        # login detection
        has_pwd = any(i['type']=='password' or ('pass' in (i['name'] or '').lower()) for i in inputs)
        has_user = any(('user' in (i['name'] or '').lower()) or ('email' in (i['name'] or '').lower()) or ('username' in (i['name'] or '').lower()) for i in inputs)
        fs['likely_login_form'] = bool(has_pwd and (has_user or any(i['type']=='text' for i in inputs)))
        forms_summary.append(fs)
    return forms_summary

# ----------------- attribute stats -----------------
def compute_attribute_stats(root):
    tag_attr = defaultdict(lambda: Counter())
    tag_attr_examples = defaultdict(lambda: defaultdict(Counter))
    for el in root.xpath('//*'):
        if not isinstance(el.tag, str):
            continue
        tag = el.tag.lower()
        for (k, v) in el.items():
            tag_attr[tag][k] += 1
            if v:
                tag_attr_examples[tag][k][v] += 1
    # prepare a serializable dict: for each tag, list attributes with counts and top values
    out = {}
    for tag, attrs in tag_attr.items():
        out[tag] = {'attr_counts': attrs.most_common(40), 'examples': {k: dict(v.most_common(10)) for k, v in tag_attr_examples[tag].items()}}
    return out

# ----------------- repeated subtree sampling & clusters -----------------
def build_signature_map(root):
    signature_map = defaultdict(list)
    for el in root.xpath('//*'):
        if not isinstance(el.tag, str):
            continue
        tag = el.tag.lower()
        cls = tuple(sorted([c for c in (el.get('class') or '').split() if c]))
        child_count = len([ch for ch in el if isinstance(ch.tag, str)])
        text_len = len((el.text_content() or '').strip())
        text_bucket = min(8, max(0, text_len // 30))
        sig = (tag, cls, child_count, text_bucket)
        signature_map[sig].append(el)
    return signature_map

def sample_html_fragments_for_sig(signature_map, sig, sample_size=3):
    nodes = signature_map.get(sig, [])
    samples = []
    # pick nodes from across the list (start/mid/end) if possible
    if not nodes:
        return samples
    idxs = [0, len(nodes)//2, -1]
    chosen = []
    for i in idxs:
        try:
            chosen.append(nodes[i])
        except:
            pass
    # if not enough, add first few
    for n in nodes:
        if len(chosen) >= sample_size:
            break
        if n not in chosen:
            chosen.append(n)
    for n in chosen[:sample_size]:
        samples.append(html_fragment_to_string(n))
    return samples

# ----------------- field hints and sample extractor -----------------
def detect_field_hints(root, candidate_containers):
    """
    Build simple candidate xpaths and regex fallbacks for common fields.
    candidate_containers: list of dicts with 'sample_nodes' (strings) and 'sample_xpath' (one sample xpath)
    """
    hints = {'title': [], 'price': [], 'image': [], 'link': [], 'rating': []}
    # heuristics from DOM
    # Titles: h1..h3 inside container, h2//a//span, largest text node
    hints['title'].extend(['.//h1/text()', './/h2//a//span/text()', './/h2//text()', './/h3//text()', 'largest_text_in_container'])
    # Price: common currency nodes or a-offscreen, or currency regex fallback
    hints['price'].extend(['.//span[contains(@class,"a-offscreen")]/text()', './/span[contains(@class,"price")]/text()', 'regex:' + CURRENCY_PAT.pattern])
    # Image: first img src or data-src
    hints['image'].extend(['.//img[1]/@src', './/img[1]/@data-src', './/img[1]/@data-image'])
    # Link: first anchor href inside container
    hints['link'].extend(['.//a[1]/@href', './/a[contains(@href,"/dp/")]/@href'])
    # Rating: a-icon-alt or text patterns
    hints['rating'].extend(['.//span[contains(@class,"rating")]/text()', './/span[contains(@class,"a-icon-alt")]/text()', 'regex:' + RATING_PAT.pattern])
    return hints

def first_nonempty_xpath(node, xpaths):
    for xp in xpaths:
        try:
            if xp.startswith('regex:'):
                continue
            res = node.xpath(xp)
            if res:
                v = res[0]
                if isinstance(v, etree._ElementUnicodeResult) or isinstance(v, str):
                    v = str(v).strip()
                else:
                    # attribute or element
                    v = html_fragment_to_string(v).strip()
                if v:
                    return v
        except Exception:
            continue
    return None

def apply_regex_fallbacks(text, regex_list):
    for rx in regex_list:
        try:
            m = re.search(rx, text)
            if m:
                return m.group(0)
        except Exception:
            continue
    return None

def extract_fields_from_node(el, hints, base_url=None):
    """
    el: lxml element
    hints: as from detect_field_hints
    returns: dict of field -> (value, confidence_score 0..1)
    """
    out = {}
    txt = (el.text_content() or '') if isinstance(el, etree._Element) else (str(el) or '')
    # Title
    title_xps = [p for p in hints['title'] if not p.startswith('regex:')]
    title = first_nonempty_xpath(el, title_xps)
    title_conf = 0.0
    if title:
        title_conf = 0.9
    else:
        # fallback: largest text in subtree
        texts = [t.strip() for t in el.xpath('.//text()') if t.strip()]
        if texts:
            candidate = max(texts, key=len)
            if len(candidate) > 7:
                title = candidate.strip()
                title_conf = 0.5
    out['title'] = {'value': title or '', 'confidence': title_conf}

    # Price
    price_xps = [p for p in hints['price'] if not p.startswith('regex:')]
    price = first_nonempty_xpath(el, price_xps)
    price_conf = 0.0
    if price:
        price_conf = 0.9
    else:
        # regex fallback from text
        p = apply_regex_fallbacks(txt, [CURRENCY_PAT.pattern])
        if p:
            price = p
            price_conf = 0.6
    out['price'] = {'value': price or '', 'confidence': price_conf}

    # Image
    img_xps = [p for p in hints['image']]
    image = None
    try:
        for xp in img_xps:
            res = el.xpath(xp)
            if res:
                image = res[0].strip()
                break
    except Exception:
        image = None
    if image and base_url and image.startswith('/'):
        image = urljoin(base_url, image)
    out['image'] = {'value': image or '', 'confidence': 0.9 if image else 0.0}

    # Link
    link = None
    try:
        res = el.xpath('.//a[1]/@href')
        if res:
            link = res[0].strip()
            if base_url and link.startswith('/'):
                link = urljoin(base_url, link)
    except Exception:
        link = None
    out['link'] = {'value': link or '', 'confidence': 0.9 if link else 0.0}

    # Rating
    rating = None
    try:
        # try rating xpaths
        res = el.xpath('.//span[contains(@class,"a-icon-alt")]/text()') or el.xpath('.//span[contains(@class,"rating")]/text()')
        if res:
            rating = res[0].strip()
        else:
            m = RATING_PAT.search(txt)
            if m:
                rating = m.group(0)
    except Exception:
        rating = None
    out['rating'] = {'value': rating or '', 'confidence': 0.9 if rating else 0.0}
    return out

# ----------------- text pattern extraction -----------------
def detect_text_patterns(root):
    full_text = ' '.join([t for t in root.xpath('//text()') if isinstance(t, str)])
    patterns = {
        'currency_examples': CURRENCY_PAT.findall(full_text)[:30],
        'rating_examples': RATING_PAT.findall(full_text)[:30],
        'emails': EMAIL_PAT.findall(full_text)[:30],
        'phones': PHONE_PAT.findall(full_text)[:30],
        'dates': DATE_PAT.findall(full_text)[:30],
        'token_like': TOKEN_LIKE_PAT.findall(full_text)[:30]
    }
    # counts
    counts = {k: len(v) for k, v in patterns.items()}
    return {'examples': patterns, 'counts': counts}

# ----------------- top xpath examples -----------------
def top_xpath_examples(root, top_n=10):
    # find text nodes with largest lengths and return their element xpaths
    texts = []
    for el in root.xpath('//*[normalize-space(text())]'):
        txt = (el.text_content() or '').strip()
        if txt:
            texts.append((len(txt), el))
    texts.sort(reverse=True, key=lambda x: x[0])
    result = []
    for ln, el in texts[:top_n]:
        try:
            path = root.getroottree().getpath(el)
        except Exception:
            path = None
        snippet = (el.text_content() or '').strip()[:400]
        result.append({'length': ln, 'xpath': path, 'preview': snippet})
    return result

# ----------------- confidence summary -----------------
def compute_confidence_summary(summary_basic):
    """
    Derive simple signals:
    - js_heavy: many scripts, big inline scripts, many token-like strings, many data-* attributes
    - many_empty_anchors
    """
    total_nodes = summary_basic.get('total_nodes', 1)
    scripts_total = summary_basic.get('scripts_styles', {}).get('scripts_total', 0)
    inline_script_count = summary_basic.get('scripts_styles', {}).get('inline_script_count', 0)
    empty_hrefs = summary_basic.get('links', {}).get('empty_hrefs', 0)
    total_anchors = summary_basic.get('links', {}).get('total', 1)
    top_classes = summary_basic.get('classes', {}).get('unique_classes', 0)
    token_count = summary_basic.get('text', {}).get('top_words', [])
    # heuristics
    js_score = min(1.0, (scripts_total / max(1, total_nodes)) * 10 + (inline_script_count / max(1, scripts_total+1)))
    empty_anchor_ratio = empty_hrefs / max(1, total_anchors)
    dynamic_hint = js_score > 0.05 or empty_anchor_ratio > 0.2 or top_classes > 100
    return {
        'js_score': round(js_score, 3),
        'empty_anchor_ratio': round(empty_anchor_ratio, 3),
        'lots_of_classes': top_classes > 100,
        'is_likely_js_heavy': bool(dynamic_hint)
    }

# ----------------- main summarizer class -----------------
class HTMLSummarizer:
    def __init__(self, html_text: str, source_path: str = None, base_url: str = None):
        self.html_text = html_text
        self.source_path = source_path
        self.base_url = base_url
        self.summary: Dict[str, Any] = {}
        self.root = None
        self._parse()

    def _parse(self):
        self.summary['parser'] = None
        if LXML_AVAILABLE:
            try:
                parser = lxml_html.HTMLParser(encoding='utf-8')
                self.root = lxml_html.fromstring(self.html_text, parser=parser)
                self.summary['parser'] = 'lxml'
                return
            except Exception as e:
                self.summary['parser_error'] = str(e)
        if BS4_AVAILABLE:
            self.soup = BeautifulSoup(self.html_text, 'html.parser')
            self.summary['parser'] = 'bs4'
        else:
            raise RuntimeError("Install lxml or beautifulsoup4 to parse HTML.")

    def summarize(self, top_n=20):
        self.summary['file_path'] = self.source_path
        self.summary['size_bytes'] = len(self.html_text.encode('utf-8'))
        # metadata (simple)
        m = re.search(r'<title[^>]*>(.*?)</title>', self.html_text, re.I|re.S)
        title = m.group(1).strip() if m else None
        charset = None
        m2 = re.search(r'<meta[^>]*charset=["\']?([^"\'>\s]+)', self.html_text, re.I)
        if m2:
            charset = m2.group(1)
        self.summary.update({'title': title, 'charset': charset})
        # choose lxml or bs4 flow
        if LXML_AVAILABLE and self.root is not None:
            return self._summarize_lxml(top_n)
        else:
            return self._summarize_bs4(top_n)

    def _summarize_lxml(self, top_n):
        root = self.root
        etree_obj = root.getroottree()
        all_nodes = root.xpath('//*')
        tag_counts = Counter([n.tag.lower() if isinstance(n.tag, str) else str(n.tag) for n in all_nodes])
        self.summary.update({
            'total_nodes': len(all_nodes),
            'unique_tags': len(tag_counts),
            'top_tags': tag_counts.most_common(top_n)
        })
        # headings
        self.summary['headings'] = {f'h{i}': len(root.xpath(f'//h{i}')) for i in range(1,7)}
        # max depth
        max_depth = 0
        def compute_depth(node, d=0):
            nonlocal max_depth
            if d > max_depth:
                max_depth = d
            for ch in node:
                if isinstance(ch.tag, str):
                    compute_depth(ch, d+1)
        compute_depth(root, 0)
        self.summary['max_dom_depth'] = max_depth
        # links
        anchors = root.xpath('//a')
        hrefs = [ (a.get('href') or '').strip() for a in anchors ]
        href_counts = Counter(hrefs)
        external = sum(1 for h in hrefs if is_absolute_url(h))
        internal = sum(1 for h in hrefs if h and not is_absolute_url(h))
        empty = sum(1 for h in hrefs if not h)
        mailto = sum(1 for h in hrefs if h.lower().startswith('mailto:'))
        tel = sum(1 for h in hrefs if h.lower().startswith('tel:'))
        hosts = Counter()
        for h in hrefs:
            if is_absolute_url(h):
                try:
                    hosts[urlparse(h).netloc] += 1
                except:
                    pass
        self.summary['links'] = {'total': len(anchors), 'empty_hrefs': empty, 'external': external, 'internal_or_relative': internal, 'mailto': mailto, 'tel': tel, 'top_hosts': hosts.most_common(10), 'top_hrefs': href_counts.most_common(30)}
        # images
        imgs = root.xpath('//img')
        img_srcs = [(img.get('src') or img.get('data-src') or img.get('data-lazy-src') or '') for img in imgs]
        missing_alt = sum(1 for img in imgs if not (img.get('alt') and img.get('alt').strip()))
        external_imgs = sum(1 for s in img_srcs if s and is_absolute_url(s))
        self.summary['images'] = {'total': len(imgs), 'missing_alt': missing_alt, 'external_src_count': external_imgs, 'top_srcs': Counter(img_srcs).most_common(30)}
        # forms
        forms = root.xpath('//form')
        inputs = root.xpath('//input')
        selects = root.xpath('//select')
        textareas = root.xpath('//textarea')
        input_types = Counter([ (inp.get('type') or 'text').lower() for inp in inputs ])
        self.summary['forms'] = {'total_forms': len(forms), 'total_inputs': len(inputs), 'input_type_counts': input_types.most_common(30), 'selects': len(selects), 'textareas': len(textareas)}
        # scripts & styles
        scripts = root.xpath('//script')
        inline_script_count = sum(1 for s in scripts if not (s.get('src')))
        external_script_count = sum(1 for s in scripts if s.get('src'))
        links_css = root.xpath('//link[@rel="stylesheet" or contains(@href,".css")]')
        style_tags = root.xpath('//style')
        self.summary['scripts_styles'] = {'scripts_total': len(scripts), 'inline_script_count': inline_script_count, 'external_script_count': external_script_count, 'stylesheets_linked': len(links_css), 'inline_style_blocks': len(style_tags)}
        # classes & ids
        classes = Counter()
        ids = Counter()
        for n in all_nodes:
            if isinstance(n.tag, str):
                cls = n.get('class')
                if cls:
                    for c in re.split(r'\s+', cls.strip()):
                        if c:
                            classes[c] += 1
                theid = n.get('id')
                if theid:
                    ids[theid] += 1
        self.summary['classes'] = {'unique_classes': len(classes), 'top_classes': classes.most_common(50)}
        self.summary['ids'] = {'unique_ids': len(ids), 'top_ids': ids.most_common(50)}
        # text stats
        text_nodes = [n.text_content().strip() for n in root.xpath('//*[normalize-space(text())]') if n.text_content().strip()]
        total_text = " ".join(text_nodes)
        words = re.findall(r"[A-Za-z0-9']{2,}", total_text)
        word_count = len(words)
        top_words = Counter([w.lower() for w in words]).most_common(50)
        longest_node = max(text_nodes, key=len) if text_nodes else ""
        self.summary['text'] = {'text_nodes': len(text_nodes), 'total_text_chars': len(total_text), 'word_count': word_count, 'top_words': top_words[:50], 'longest_text_node_length': len(longest_node), 'longest_text_node_preview': (longest_node[:400] + '...') if len(longest_node)>400 else longest_node, 'avg_words_per_text_node': (word_count/len(text_nodes)) if text_nodes else 0}
        # repeated subtree detection + clusters
        signature_map = build_signature_map(root)
        freq_sigs = [(sig, len(nodes)) for sig, nodes in signature_map.items() if len(nodes) > 1]
        freq_sigs.sort(key=lambda x: x[1], reverse=True)
        top_repeats = []
        for sig, count in freq_sigs[:60]:
            sample_xpath = None
            try:
                sample_xpath = etree_obj.getpath(signature_map[sig][0])
            except Exception:
                sample_xpath = None
            suggested_css = sig[0]
            if sig[1]:
                suggested_css += '.' + sig[1][0]
            samples = sample_html_fragments_for_sig(signature_map, sig, sample_size=3)
            top_repeats.append({'signature': {'tag': sig[0], 'classes': sig[1], 'child_count': sig[2], 'text_bucket': sig[3]}, 'count': count, 'sample_xpath': sample_xpath, 'suggested_css': suggested_css, 'sample_nodes': samples})
        self.summary['repeats'] = {'total_repeated_signatures': len(freq_sigs), 'top_repeated': top_repeats[:40]}
        # suggested container (best candidate)
        candidate = None
        for item in top_repeats:
            if item['count'] >= 3 and item['signature']['tag'] in ('div','li','article','section','a'):
                candidate = item
                break
        if candidate:
            self.summary['suggested_container'] = candidate
        # attribute stats
        self.summary['attribute_stats'] = compute_attribute_stats(root)
        # field hints
        # pass candidate containers (as dicts) to hint detector
        candidate_containers = self.summary['repeats']['top_repeated']
        self.summary['field_hint_map'] = detect_field_hints(root, candidate_containers)
        # sample extractions for the top candidate(s)
        samples_for_extraction = []
        for c in (candidate_containers[:3] if candidate_containers else []):
            # take parsed sample nodes (we need lxml elements)
            sample_xpaths = []
            # try to get element objects for the first few sample_nodes via sample_xpath
            first_xpath = c.get('sample_xpath')
            sample_el_nodes = []
            if first_xpath:
                try:
                    el = root.xpath(first_xpath)
                    if el:
                        sample_el_nodes.append(el[0])
                except Exception:
                    pass
            # fallback: evaluate relative paths inside the root using suggested_css
            # collect up to 3 elements from signature_map by matching signature values
            sig = tuple([c['signature']['tag'], tuple(c['signature']['classes']), c['signature']['child_count'], c['signature']['text_bucket']]) if 'signature' in c else None
            if sig and sig in signature_map:
                sample_el_nodes.extend(signature_map[sig][:3])
            # remove duplicates and None
            seen = []
            final_nodes = []
            for n in sample_el_nodes:
                if n is not None and n not in seen:
                    final_nodes.append(n); seen.append(n)
                if len(final_nodes) >= 3:
                    break
            # run extraction heuristics on each sample element
            for n in final_nodes:
                extracted = extract_fields_from_node(n, self.summary['field_hint_map'], base_url=self.base_url)
                samples_for_extraction.append({'container_signature': c['signature'], 'extraction': extracted, 'sample_xpath': etree_obj.getpath(n)})
        self.summary['sample_extractions'] = samples_for_extraction[:30]
        # text patterns
        self.summary['text_patterns'] = detect_text_patterns(root)
        # top xpath examples
        self.summary['top_xpath_examples'] = top_xpath_examples(root, top_n=20)
        # clustered_subtrees (represent top_repeats as clusters)
        clusters = []
        for item in top_repeats[:30]:
            clusters.append({'signature': item['signature'], 'count': item['count'], 'sample_nodes': item['sample_nodes'], 'suggested_css': item['suggested_css'], 'sample_xpath': item['sample_xpath']})
        self.summary['clustered_subtrees'] = clusters
        # forms detailed + redaction
        self.summary['forms_detailed'] = detect_and_redact_forms_lxml(root)
        self.summary['has_forms_posting_external'] = any(f['external_action'] for f in self.summary['forms_detailed'])
        # confidence
        self.summary['confidence_summary'] = compute_confidence_summary(self.summary)
        return self.summary

    def _summarize_bs4(self, top_n):
        # degraded flow using BeautifulSoup
        soup = self.soup
        all_nodes = soup.find_all()
        tag_counts = Counter([n.name for n in all_nodes if n.name])
        self.summary.update({'total_nodes': len(all_nodes), 'unique_tags': len(tag_counts), 'top_tags': tag_counts.most_common(top_n)})
        self.summary['headings'] = {f'h{i}': len(soup.find_all(f'h{i}')) for i in range(1,7)}
        # links
        anchors = soup.find_all('a')
        hrefs = [(a.get('href') or '').strip() for a in anchors]
        external = sum(1 for h in hrefs if is_absolute_url(h))
        empty = sum(1 for h in hrefs if not h)
        self.summary['links'] = {'total': len(anchors), 'empty_hrefs': empty, 'external': external, 'top_hrefs': Counter(hrefs).most_common(30)}
        # images
        imgs = soup.find_all('img')
        img_srcs = [(img.get('src') or img.get('data-src') or '') for img in imgs]
        self.summary['images'] = {'total': len(imgs), 'missing_alt': sum(1 for img in imgs if not (img.get('alt') and img.get('alt').strip())), 'top_srcs': Counter(img_srcs).most_common(30)}
        # classes/ids
        classes = Counter()
        ids = Counter()
        for n in all_nodes:
            if getattr(n, 'attrs', None):
                cls = n.attrs.get('class') or []
                for c in (cls if isinstance(cls, list) else [cls]):
                    if c:
                        classes[c] += 1
                theid = n.attrs.get('id')
                if theid:
                    ids[theid] += 1
        self.summary['classes'] = {'unique_classes': len(classes), 'top_classes': classes.most_common(50)}
        self.summary['ids'] = {'unique_ids': len(ids), 'top_ids': ids.most_common(50)}
        # text patterns & top xpaths not available in bs4
        self.summary['text'] = {'text_nodes': len(list(soup.stripped_strings))}
        self.summary['text_patterns'] = {'examples': {}, 'counts': {}}
        # forms (redacted)
        forms_summary = []
        for f in soup.find_all('form'):
            action = (f.get('action') or '').strip()
            inputs = []
            for inp in f.find_all(['input','textarea','select']):
                t = (inp.get('type') or inp.name or 'input').lower()
                name = (inp.get('name') or inp.get('id') or '').strip()
                value = (inp.get('value') or '').strip()
                suspicious = looks_sensitive_name(name) or t in ('password','hidden')
                redacted_value = 'REDACTED' if suspicious and value else (None if not value else '<<non-sensitive>>')
                inputs.append({'name': name, 'type': t, 'has_value': bool(value), 'redacted_value': redacted_value, 'suspicious': suspicious})
            forms_summary.append({'action': action, 'input_count': len(inputs), 'inputs': inputs})
        self.summary['forms_detailed'] = forms_summary
        self.summary['confidence_summary'] = {'is_likely_js_heavy': False}
        return self.summary

# ----------------- CLI -----------------
def main():
    parser = argparse.ArgumentParser(description="Enhanced HTML summarizer (LLM-ready JSON).")
    parser.add_argument("input", help="Path to HTML file")
    parser.add_argument("-o", "--output", help="Write JSON summary to this file", default=None)
    parser.add_argument("--top", help="Top-N for tag/class frequency", type=int, default=20)
    parser.add_argument("--base-url", help="Base URL to resolve relative links/imgs (optional)", default=None)
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print("Input file not found:", args.input, file=sys.stderr)
        sys.exit(2)
    html_text = safe_read(args.input)
    summarizer = HTMLSummarizer(html_text, source_path=args.input, base_url=args.base_url)
    summary = summarizer.summarize(top_n=args.top)

    # print compact overview
    print(f"\nHTML Summary for: {args.input}\nSize: {summary.get('size_bytes')} bytes  Parser: {summary.get('parser')}\n")
    print("Title:", summary.get('title'))
    print("Total nodes:", summary.get('total_nodes'))
    print("Top tags:", summary.get('top_tags', [])[:8])
    print("Top repeated signatures (sample):")
    for r in summary.get('repeats', {}).get('top_repeated', [])[:8]:
        print(f"  - tag={r['signature']['tag']} classes={r['signature']['classes'][:3]} count={r['count']} xpath={r.get('sample_xpath')}")
    print("\nSuggested container (if any):", bool(summary.get('suggested_container')))
    print("Forms total:", summary.get('forms', {}).get('total_forms'))
    print("Confidence summary:", summary.get('confidence_summary'))
    # save json if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as fh:
            json.dump(summary, fh, indent=2, ensure_ascii=False)
        print("\nSaved extended JSON summary to:", args.output)

def analyze_html(html_content: str, output_file: str = None, top_n: int = 10) -> dict:
    """
    Simple function to analyze HTML content and return JSON analysis.
    
    Args:
        html_content: HTML content as string
        output_file: Optional output JSON file path (if None, returns dict directly)
        top_n: Top-N for tag/class frequency (default: 10)
    
    Returns:
        JSON analysis as dictionary, or file path if output_file is provided
    """
    # Create summarizer and analyze
    summarizer = HTMLSummarizer(html_content)
    summary = summarizer.summarize(top_n=top_n)
    
    # Save to JSON file if path provided
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as fh:
            json.dump(summary, fh, indent=2, ensure_ascii=False)
        print(f"✅ HTML analysis saved to: {output_file}")
        return output_file
    
    # Return dict directly
    return summary

if __name__ == "__main__":
    main()
