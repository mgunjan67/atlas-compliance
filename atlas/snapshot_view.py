"""Readable saved evidence; never execute or load assets from captured HTML."""
from html import escape
from urllib.parse import urlencode
from .extract import Document, Node

TAGS = {'h1','h2','h3','h4','p','div','section','article','aside','main',
        'strong','b','em','small','span','ul','ol','li','dl','dt','dd',
        'table','thead','tbody','tr','th','td','blockquote','br','hr','details','summary'}
SKIP = {'head','script','style','noscript','svg','iframe','object','embed','template',
        'nav','form','button','input','link','meta'}


def readable(node):
    if isinstance(node,str):
        return escape(node)
    if node.tag in SKIP or 'hidden' in node.attrs or node.attrs.get('aria-hidden')=='true':
        return ''
    content=''.join(readable(child) for child in node.children)
    if node.tag=='a':
        return '<span>'+content+'</span> '
    if node.tag not in TAGS:
        return content
    if node.tag in ('br','hr'):
        return '<'+node.tag+'>'
    # Only tag names survive: no source scripts, event handlers, links or styles.
    return '<'+node.tag+'>'+content+'</'+node.tag+'>'


def snapshot_page(row, mode):
    root=Document(row['raw_html']).root
    body=(root.find('main') or root.find('body') or [root])[0]
    query=urlencode({'mode':mode,'id':row['id'],'format':'raw'})
    title='Asteria' if row['source']=='federal' else 'Bellwether'
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>Saved source · '+title+'</title><link rel="stylesheet" href="/style.css"></head>'
            '<body class="saved-page"><header class="saved-header"><span class="eyebrow">ATLAS · SAVED EVIDENCE</span>'
            '<h1>'+title+' · saved copy</h1><p>Captured '+escape(row['retrieved_at'])+'</p>'
            '<p>Readable text from the saved page. Original wording is preserved; website styling and scripts are removed.</p>'
            '<a href="/api/snapshot?'+escape(query,quote=True)+'">Download original HTML</a></header>'
            '<div class="saved-content">'+readable(body)+'</div></body></html>')
