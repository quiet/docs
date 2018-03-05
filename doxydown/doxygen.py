import xml.etree.ElementTree as ET
from collections import OrderedDict
import os.path
import subprocess


class DoxygenXMLConsumer(object):
    def __init__(self, base_path, gen_docs=None):
        if gen_docs:
            subprocess.call(('doxygen', 'Doxyfile'), cwd=gen_docs)
        self._refs, self._filenames = self._find_symbols(os.path.join(base_path, 'index.xml'))
        self._inverted_refs = {v: k for k, v in self._refs.iteritems()}
        self.docs = self._walk_docs(base_path)

    def _find_symbols(self, path):
        index_tree = ET.parse(path)
        index_root = index_tree.getroot()
        filenames = []
        refs = {}
        for c in index_root.iterfind('compound'):
            name = c.find('name')
            ref = c.attrib.get('refid', None)
            if name is not None and ref:
                filenames.append(ref)
                refs[name.text] = ref

        return refs, filenames


    def _append_desc(self, l, text, attrib):
        if text.strip():
            d = dict(attrib or {})
            d['text'] = text
            l.append(d)


    def _attrib_from_element(self, element):
        if element.tag == 'ref':
            refid = element.attrib.get('refid')
            if refid in self._inverted_refs:
                return {
                    'ref': self._inverted_refs[refid],
                    'linkable': True,
                }
            return {
                'ref': refid,
                'linkable': False,
            }
        if element.tag == 'simplesect':
            sect_type = element.attrib.get('kind')
            if sect_type == 'return':
                return {
                    'return': True,
                }
            if sect_type == 'note':
                return {
                    'note': True,
                }
            if sect_type == 'warning':
                return {
                    'warning': True,
                }
            raise Exception('unrecognized simplesect kind ' + sect_type)
        if element.tag == 'computeroutput':
            return {
                'fixed': True,
            }
        if element.tag == 'emphasis':
            return {
                'emphasis': True,
            }
        if element.tag == 'ndash':
            return {
                'ndash': True,
            }
        if element.tag == 'para':
            return {
                'paragraph': True,
            }
        if element.tag == 'programlisting':
            return {
                'example': True,
            }
        if element.tag == 'highlight':
            return {
                'info': True,
            }
        if element.tag == 'parameterlist' and element.attrib.get('kind') == 'exception':
            return {
                'exception': True,
            }
        if element.tag in ('type',
                           'briefdescription',
                           'detaileddescription',
                           'parameterlist',
                           'parameternamelist',
                           'parametername',
                           'parameterdescription',
                           'codeline',
                           'exceptions',):
            return None
        if element.tag == 'parameteritem':
            params = []
            for p in element.find('parameternamelist').iterfind('parametername'):
                params.append(p.text)
            if len(params) > 1:
                raise Exception('doc referencing more than one param found')
            return {
                'param': params[0],
            }
        raise Exception('unrecognized desc element ' + element.tag)


    def _desc_from_element(self, element, attribs=None):
        if element is None:
            return []
        if element.tag in ('parameternamelist',):
            return []
        desc = []
        parent_attribs = attribs
        attrib = self._attrib_from_element(element)
        if attrib:
            attribs = dict(attribs or {})
            attribs.update(attrib)
        if element.text is not None:
            self._append_desc(desc, element.text, attribs)
        if attribs:
            attribs.pop('paragraph', None)
        for child in element:
            desc.extend(self._desc_from_element(child, attribs=attribs))
        if element.tail is not None:
            self._append_desc(desc, element.tail, parent_attribs)
        return desc


    def _bool_from_yesno(self, yesno):
        if yesno == 'yes':
            return True
        if yesno == 'no':
            return False
        raise Exception('unrecognized yesno ' + yesno)


    def _func_from_element(self, element):
        args = []
        for param in element.iterfind('param'):
            attrib = param.find('attribute')
            args.append({
                'name': param.find('declname').text,
                'type': self._desc_from_element(param.find('type')),
            })
        return {
            'name': element.find('name').text,
            'kind': element.attrib.get('kind'),
            'brief_desc': self._desc_from_element(element.find('briefdescription')),
            'long_desc': self._desc_from_element(element.find('detaileddescription')),
            'args': args,
            'ret': self._desc_from_element(element.find('type')),
            'protection': element.attrib.get('prot', 'public'),
            'exceptions': self._desc_from_element(element.find('exceptions')),
            'static': self._bool_from_yesno(element.attrib.get('static', 'no')),
            'const': self._bool_from_yesno(element.attrib.get('const', 'no')),
        }


    def _member_from_element(self, element):
        return {
            'name': element.find('name').text,
            'kind': element.attrib.get('kind'),
            'type': self._desc_from_element(element.find('type')),
            'brief_desc': self._desc_from_element(element.find('briefdescription')),
            'long_desc': self._desc_from_element(element.find('detaileddescription')),
        }


    def _enum_from_element(self, element):
        values = []
        for value in element.iterfind('enumvalue'):
            initializer = value.find('initializer')
            values.append({
                'name': value.find('name').text,
                'brief_desc': self._desc_from_element(value.find('briefdescription')),
                'long_desc': self._desc_from_element(value.find('detaileddescription')),
                'initializer': initializer.text if initializer is not None else '',
            })
        return {
            'name': element.find('name').text,
            'kind': element.attrib.get('kind'),
            'values': values,
            'brief_desc': self._desc_from_element(element.find('briefdescription')),
            'long_desc': self._desc_from_element(element.find('detaileddescription')),
        }


    def _typedef_from_element(self, element):
        return {
            'name': element.find('name').text,
            'kind': element.attrib.get('kind'),
            'type': self._desc_from_element(element.find('type')),
            'brief_desc': self._desc_from_element(element.find('briefdescription')),
            'long_desc': self._desc_from_element(element.find('detaileddescription')),
        }


    def _property_from_element(self, element):
        return {
            'name': element.find('name').text,
            'kind': element.attrib.get('kind'),
            'type': self._desc_from_element(element.find('type')),
            'brief_desc': self._desc_from_element(element.find('briefdescription')),
            'long_desc': self._desc_from_element(element.find('detaileddescription')),
        }


    def _walk_docs(self, base_path):
        structs = {}
        for f in self._filenames:
            path = base_path + f + '.xml'
            t = ET.parse(path)
            r = t.getroot()
            compounddef = r.find('compounddef')
            functions = []
            members = OrderedDict()
            enums = OrderedDict()
            typedefs = OrderedDict()
            properties = OrderedDict()

            for sectiondef in compounddef.iterfind('sectiondef'):
                for m in sectiondef.iterfind('memberdef'):
                    if m.attrib.get('prot') not in ('public', 'protected'):
                        if m.attrib.get('prot') not in ('private', 'package'):
                            raise Exception('unrecognized prot ' + m.attrib.get('prot'))
                        continue
                    kind = m.attrib.get('kind', None)
                    if kind == 'variable':
                        member = self._member_from_element(m)
                        members[member['name']] = member
                    elif kind == 'function':
                        func = self._func_from_element(m)
                        functions.append(func)
                    elif kind == 'enum':
                        enum = self._enum_from_element(m)
                        enums[enum['name']] = enum
                    elif kind == 'typedef':
                        typedef = self._typedef_from_element(m)
                        typedefs[typedef['name']] = typedef
                    elif kind == 'property':
                        prop = self._property_from_element(m)
                        properties[prop['name']] = prop
                    else:
                        raise Exception('unrecognized kind ' + kind)

            name = compounddef.find('compoundname').text.split(':')[-1]
            base = compounddef.find('basecompoundref')
            structs[name] = {
                'name': name,
                'kind': compounddef.attrib.get('kind'),
                'shortdesc': self._desc_from_element(compounddef.find('briefdescription')),
                'longdesc': self._desc_from_element(compounddef.find('detaileddescription')),
                'functions': functions,
                'members': members,
                'enums': enums,
                'typedefs': typedefs,
                'properties': properties,
                'protection': compounddef.attrib.get('prot'),
                'base': base.text if base is not None else None,
            }

        return structs
