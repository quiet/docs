import os.path
import subprocess
import pprint
import json
from collections import OrderedDict


def find_typedefs(root, prefix):
    if not isinstance(root, list) and not isinstance(root, dict):
        return [], {}
    paths = []
    refs = {}
    if root.get('typedefs'):
        for index, typedef in enumerate(root['typedefs']):
            path = prefix + ('typedefs', index)
            paths.append(path)
            refs[typedef['name']] = path

    for k, v in root.iteritems():
        if isinstance(v, list):
            for index, item in enumerate(v):
                next_prefix = prefix + (k, index)
                found_paths, found_refs = find_typedefs(item, next_prefix)
                paths.extend(found_paths)
                refs.update(found_refs)
        else:
            next_prefix = prefix + (k,)
            found_paths, found_refs = find_typedefs(v, next_prefix)
            paths.extend(found_paths)
            refs.update(found_refs)

    return paths, refs


def find_symbols(docs):
    paths = []
    refs = {}
    for index, namespace in enumerate(docs.get('namespaces', [])):
        path = ('namespaces', index)
        paths.append(path)
        refs[namespace['name']] = path
    typedef_paths, typedef_refs = find_typedefs(docs, tuple())
    paths.extend(typedef_paths)
    refs.update(typedef_refs)

    return refs, paths


def make_text_list(s, tags=None):
    paragraphs = s.split('\n\n')
    l = []
    for index, paragraph in enumerate(paragraphs):
        item = {'text': paragraph.replace('\n', ' ')}
        if index != 0:
            item['paragraph'] = True
        if tags:
            item.update(tags)
        l.append(item)
    return l


def build_function(function):
    args = []
    desc_paragraphs = make_text_list(function['description'])
    brief_desc = []
    desc = []
    if desc_paragraphs:
        brief_desc.append(desc_paragraphs.pop(0))
        desc.extend(desc_paragraphs)
    for arg in function['parameters']:
        args.append({
            'name': arg['name'],
            'optional': arg['optional'] or False,
            'type': [],
        })
        desc.extend(make_text_list(
            arg['description'],
            tags={'param': arg['name']}
        ))
    if 'returns' in function:
        desc.extend(make_text_list(
            function['returns']['description'],
            tags={'return': True}
        ))
    return {
        'name': function['name'],
        'brief_desc': brief_desc,
        'long_desc': desc,
        'args': args,
        'ret': [],
    }


def build_prop_function(prop, type_obj):
    func = {
        'parameters': [],
    }
    func.update(prop)
    func.update(type_obj)
    return build_function(func)


def build_prop(prop):
    desc_paragraphs = make_text_list(prop['description'])
    brief_desc = []
    desc = []
    if desc_paragraphs:
        brief_desc.append(desc_paragraphs.pop(0))
        desc.extend(desc_paragraphs)
    return {
        'name': prop['name'],
        'type': prop['type'],
        'brief_desc': brief_desc,
        'long_desc': desc,
    }


def walk_docs(path):
    docs = json.loads(subprocess.check_output(('jsdoc', 'quiet.js', '-r', '-t', 'templates/haruki', '-d', 'console'), cwd=path))
    namespaces = {}
    refs, paths = find_symbols(docs)
    for doc_path in paths:
        obj = docs
        for p in doc_path:
            obj = obj[p]
        functions = []
        members = OrderedDict()

        for function in obj.get('functions', []):
            functions.append(build_function(function))
        for prop in obj.get('properties', []):
            if prop.get('type') == 'function':
                functions.append(build_prop_function(prop, {}))
            elif prop.get('type') in refs:
                type_obj = docs
                for path in refs[prop['type']]:
                    type_obj = type_obj[path]
                functions.append(build_prop_function(prop, type_obj))
            else:
                members[prop['name']] = build_prop(prop)

        for func in functions:
            func['name'] = '.'.join((obj['name'], func['name']))

        desc_paragraphs = make_text_list(obj['description'])
        brief_desc = []
        desc = []
        if desc_paragraphs:
            brief_desc.append(desc_paragraphs.pop(0))
            desc.extend(desc_paragraphs)
        namespace = {
            'name': obj['name'],
            'shortdesc': brief_desc,
            'longdesc': desc,
            'functions': functions,
            'members': members,
            'enums': {},
            'typedefs': {},
            'properties': {},
        }
        namespaces[namespace['name']] = namespace

    return namespaces


if __name__ == '__main__':
    scriptpath = os.path.dirname(os.path.realpath(__file__))
    path = os.path.join(scriptpath, '..', 'quiet-js/')
    pprint.pprint(walk_docs(path))
