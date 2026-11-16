"""Registry inventory and AND/OR parser; L0 extraction is not L1/L2 review."""
import hashlib,re,xml.etree.ElementTree as ET
from core17_registry_inventory import inventory

def dependencies(expression):
    """Registry grammar: '+' AND, ',' OR, grouped with parentheses."""
    if not expression: return ('true',)
    tokens=re.findall(r'[A-Za-z_][A-Za-z_0-9]*(?:::[A-Za-z_][A-Za-z_0-9]*)?|[+(),]',expression)
    if ''.join(tokens)!=re.sub(r'\s+','',expression): raise ValueError('invalid dependency token')
    i=0
    def primary():
        nonlocal i
        if i>=len(tokens): raise ValueError('missing operand')
        token=tokens[i];i+=1
        if token=='(':
            node=union()
            if i>=len(tokens) or tokens[i]!=')':raise ValueError('unclosed group')
            i+=1;return node
        if token in ('+',',',')'):raise ValueError('invalid operand')
        return ('symbol',token)
    def intersection():
        nonlocal i
        nodes=[primary()]
        while i<len(tokens) and tokens[i]=='+':i+=1;nodes.append(primary())
        return nodes[0] if len(nodes)==1 else ('and',*nodes)
    def union():
        nonlocal i
        nodes=[intersection()]
        while i<len(tokens) and tokens[i]==',':i+=1;nodes.append(intersection())
        return nodes[0] if len(nodes)==1 else ('or',*nodes)
    tree=union()
    if i!=len(tokens):raise ValueError('trailing tokens')
    return tree

def evaluate(tree,capabilities):
    if tree[0]=='true':return True
    if tree[0]=='symbol':
        value=capabilities.get(tree[1])
        if value is not None and type(value) is not bool:raise ValueError('tri-state expected')
        return value
    children=[evaluate(t,capabilities) for t in tree[1:]]
    if tree[0]=='and':return False if False in children else None if None in children else True
    if tree[0]=='or':return True if True in children else None if None in children else False
    raise ValueError('unknown AST')

def collect(raw):
    if len(raw)>20_000_000 or b'<!DOCTYPE' in raw or b'<!ENTITY' in raw:raise ValueError('XML budget/entity refused')
    root=ET.fromstring(raw); inherited=inventory(raw)
    types=[]
    for t in root.findall('types/type'):
        types.append({'name':t.get('name') or t.findtext('name'),'attributes':dict(t.attrib),
          'members':[{'name':m.findtext('name'),'type':m.findtext('type'),'attributes':dict(m.attrib)} for m in t.findall('member')]})
    commands=[]
    for c in root.findall('commands/command'):
        commands.append({'name':c.get('name') or c.findtext('proto/name'),'attributes':dict(c.attrib),
                         'params':[{'name':p.findtext('name'),'type':p.findtext('type'),'attributes':dict(p.attrib)} for p in c.findall('param')]})
    expressions=sorted({x.get('depends') for x in root.iter() if x.get('depends')})
    parsed={x:dependencies(x) for x in expressions}
    sc=[{'kind':x.tag,'name':x.get('name'),'attributes':dict(x.attrib)} for x in root.iter() if 'vulkansc' in (x.get('api','')+','+x.get('supported','')).split(',')]
    return {'source_sha256':hashlib.sha256(raw).hexdigest(),'inherited_inventory':inherited,
            'types':types,'commands':commands,'dependencies':parsed,'sc_variant_records':sc,
            'claims':{'symbol_extraction':'PASS','semantic_L1_L2':'UNREVIEWED','pnext_validity':'UNREVIEWED','SC_certification':'NOT_APPLICABLE'}}

if __name__=='__main__':
    import argparse,json
    from pathlib import Path
    from core17_registry_inventory import SOURCE_SHA256
    p=argparse.ArgumentParser();p.add_argument('--xml',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();raw=a.xml.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SOURCE_SHA256:raise ValueError('wrong frozen vk.xml')
    a.out.write_text(json.dumps(collect(raw),ensure_ascii=False,indent=2)+'\n')
