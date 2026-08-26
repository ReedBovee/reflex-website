"""Build a single-file preview of the Film Tools app from app/index.html.

    python3 app/build-preview.py out.html               # Artifact fragment
    python3 app/build-preview.py out.html --standalone  # full HTML document

Both inline the logo and drop the manifest/service-worker wiring, so the
result is one self-contained file. The fragment form is what gets published
as a Claude Artifact (the publish step supplies the document skeleton); the
standalone form can be emailed or opened straight from disk.

Re-run this after changing app/index.html - the preview is generated, never
hand-edited.
"""
import base64, os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = sys.argv[1]
STANDALONE = '--standalone' in sys.argv[2:]

h = open(REPO + '/app/index.html', encoding='utf-8').read()
b64 = lambda p: 'data:image/png;base64,' + base64.b64encode(open(REPO + p, 'rb').read()).decode()

def sub1(old, new, label):
    global h
    assert h.count(old) == 1, f'{label}: expected 1 occurrence, found {h.count(old)}'
    h = h.replace(old, new)

# --- inline assets, drop file-relative refs the single file can't resolve ---
sub1('src="icons/reflex-logo.png"', 'src="' + b64('/app/icons/reflex-logo.png') + '"', 'logo')
sub1('<link rel="manifest" href="manifest.webmanifest">\n', '', 'manifest link')
sub1('<link rel="icon" href="icons/icon-192.png" sizes="192x192">\n', '', 'icon link')
sub1('<link rel="apple-touch-icon" href="icons/apple-touch-icon.png">',
     '<link rel="apple-touch-icon" href="' + b64('/app/icons/apple-touch-icon.png') + '">', 'touch icon')

# --- no service worker: nothing to register against in a single file ---
sub1("""  if('serviceWorker' in navigator){
    window.addEventListener('load',function(){
      navigator.serviceWorker.register('sw.js').catch(function(){});
    });
  }
""", '', 'sw registration')

# --- preview detection ---
sub1("  var deferred=null;\n",
     "  var deferred=null;\n  var PREVIEW=IN_VIEWER;\n", 'PREVIEW flag')

# --- the artifact viewer blocks page-initiated downloads; route CSV through
#     the downloads capability when the page is running inside it ---
sub1("""function csvDL(fn,rows){
  var c=rows.map(function(r){return r.map(function(x){return '"'+String(x).replace(/"/g,'""')+'"';}).join(',');}).join('\\r\\n');
  var b=new Blob([c],{type:'text/csv'});var u=URL.createObjectURL(b);
  var a=document.createElement('a');a.href=u;a.download=fn;document.body.appendChild(a);a.click();
  document.body.removeChild(a);setTimeout(function(){URL.revokeObjectURL(u);},1000);
}""",
"""var IN_VIEWER=(function(){try{return window.self!==window.top;}catch(e){return true;}})();
var DL=null;
if(window.claude&&window.claude.use){
  window.claude.use('downloads').then(function(ns){DL=ns;},function(){});
}
function csvText(rows){
  return rows.map(function(r){return r.map(function(x){return '"'+String(x).replace(/"/g,'""')+'"';}).join(',');}).join('\\r\\n');
}
function csvDL(fn,rows,btn){
  var c=csvText(rows);
  if(DL){
    // The viewer confirms the save; csv may not be an enabled type, so fall
    // back to the same text as .txt rather than failing silently.
    DL.save({filename:fn,data:c}).catch(function(e){
      if(e&&e.code==='extension_not_enabled') return DL.save({filename:fn.replace(/\\.csv$/,'.txt'),data:c});
      throw e;
    }).then(function(){if(btn)flash(btn,'Saved');},function(e){
      if(btn&&!(e&&e.code==='declined'))flash(btn,'Unavailable');
    });
    return;
  }
  var b=new Blob([c],{type:'text/csv'});var u=URL.createObjectURL(b);
  var a=document.createElement('a');a.href=u;a.download=fn;document.body.appendChild(a);a.click();
  document.body.removeChild(a);setTimeout(function(){URL.revokeObjectURL(u);},1000);
}""", 'csvDL')

assert h.count('.concat(rows()));') == 3, h.count('.concat(rows()));')
h = h.replace('.concat(rows()));', '.concat(rows()),this);')

# --- installing can't work from inside the viewer frame; say so instead ---
sub1("  if(iOS&&!standalone&&!dismissed()){", "  if(iOS&&!standalone&&!dismissed()&&!PREVIEW){", 'iOS guard')
sub1("    if(standalone||dismissed())return;", "    if(standalone||dismissed()||PREVIEW)return;", 'android guard')
sub1("""    setTimeout(function(){bar.classList.add('show');},1200);
  }
""", """    setTimeout(function(){bar.classList.add('show');},1200);
  }

  // Preview build: installing and offline caching need the app served from its
  // own address, so explain that rather than offering a button that can't work.
  if(PREVIEW&&!dismissed()){
    msg.innerHTML='<strong>This is a preview.</strong> Every calculator works exactly as it will on a phone. Installing to the home screen and running with no signal switch on once it is hosted at reflextechnologies.com/app/.';
    go.style.display='none';
    no.textContent='Got it';
    setTimeout(function(){bar.classList.add('show');},900);
  }
""", 'preview note')

# --- reduce to an artifact fragment: the publish step supplies the skeleton ---
title = re.search(r'<title>.*?</title>', h, re.S).group(0)
fonts = re.search(r'<link href="https://fonts\.googleapis\.com[^>]*>', h).group(0)
style = re.search(r'<style>.*?</style>', h, re.S).group(0)
body  = re.search(r'<body>\s*(.*?)\s*</body>', h, re.S).group(1)

# beat any body box the wrapper's reset supplies, at equal specificity
style = style.replace('html,body{height:100%;overflow:hidden;overscroll-behavior:none}',
                      'html,body{height:100%;margin:0;padding:0;overflow:hidden;overscroll-behavior:none}')

out = '\n'.join([title, fonts, style, '', body, ''])
for bad in ['<!DOCTYPE', '<html', '</html>', '<body>', '</body>', '<head>', '</head>', 'icons/', 'sw.js']:
    assert bad not in out, 'leftover: ' + bad

if STANDALONE:
    out = ('<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
           '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
           '<meta name="theme-color" content="#0c0e10">\n'
           + out.replace('\n' + body, '\n</head>\n<body>\n' + body)
           + '</body>\n</html>\n')

open(OUT, 'w', encoding='utf-8').write(out)
print('built', OUT, len(out), 'bytes', '(standalone)' if STANDALONE else '(artifact fragment)')
