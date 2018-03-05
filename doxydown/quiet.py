from collections import OrderedDict
import os.path

from doxygen import DoxygenXMLConsumer
from jsdoc import walk_docs as jsdoc_walk_docs
from templates import *


reflinks = {}


def build_text_block(items, fixed=False):
    elements = []
    for item in items:
        link = None
        if item.get('linkable') and item.get('ref') in reflinks and not fixed:
            link = reflinks[item.get('ref')]
            elements.append('[')
        if item.get('paragraph'):
            elements.append('\n')
        if item.get('ref') and not fixed:
            elements.append('`')
        if item.get('fixed') and not fixed:
            elements.append('`')
        elements.append(item['text'].replace('\n', ''))
        if item.get('ref') and not fixed:
            elements.append('`')
        if item.get('fixed') and not fixed:
            elements.append('`')
        if link:
            elements.append(']')
            elements.append('({link})'.format(link=link))

    return ''.join(elements).strip()


def build_argstring(args, indentlevel):
    argstrings = []
    optional_level = 0
    for index, arg in enumerate(args):
        if arg.get('optional'):
            argstrings.append(' [')
            optional_level += 1
        if index != 0:
            if indentlevel >= 0:
                argstrings.append(',\n')
                argstrings.append(' ' * indentlevel)
            else:
                argstrings.append(', ')
        if arg['type']:
            argstrings.append(build_text_block(arg['type'], fixed=True))
            if not arg['type'][-1]['text'].endswith(' *'):
                argstrings.append(' ')
        argstrings.append(arg['name'])
    if optional_level:
        argstrings.append(']' * optional_level)

    return ''.join(argstrings)


def build_objc_argstring(fragments, args, indentlevel):
    argstrings = []
    for index, arg in enumerate(args):
        if index != 0:
            if indentlevel >= 0:
                argstrings.append('\n')
                # indentlevel here will set indent of ':'
                # so we need to make a relative length
                indent = max(indentlevel - len(fragments[index]), 0)
                argstrings.append(' ' * indent)
            else:
                argstrings.append(' ')
            argstrings.append(fragments[index])
        if arg['type']:
            argstrings.append('(')
            argstrings.append(build_text_block(arg['type'], fixed=True))
            argstrings.append(')')

        argstrings.append(arg['name'])

    return ''.join(argstrings)


def build_function_description(brief_desc, long_desc):
    body = []
    args = OrderedDict()
    ret = []
    errors = OrderedDict()
    if brief_desc and not long_desc:
        body.extend(brief_desc)
    for item in long_desc:
        if item.get('return'):
            ret.append(item)
        elif item.get('exception'):
            errors.setdefault(item['param'], [])
            errors[item['param']].append(item)
        elif item.get('param'):
            args.setdefault(item['param'], [])
            args[item['param']].append(item)
        else:
            body.append(item)

    components = []
    if body:
        components.append(build_text_block(body))
    if args:
        arg_body = []
        for arg, arg_desc in args.iteritems():
            arg_body.append(func_parameter_template.format(
                name=arg,
                desc=build_text_block(arg_desc),
            ))
        components.append(func_parameters_template.format(
            parameters='\n'.join(arg_body),
        ))
    if ret:
        components.append(func_return_template.format(
            returns=build_text_block(ret),
        ))
    if errors:
        error_body = []
        for error, error_desc in errors.iteritems():
            error_body.append(func_error_template.format(
                name=error,
                desc=build_text_block(error_desc),
            ))
        components.append(func_errors_template.format(
            errors='\n'.join(error_body),
        ))
    return '\n'.join(components)


def gen_markdown_function(func, language):
    func_template = {
        'c': c_func_template,
        'objc': objc_method_template,
        'java': java_func_template,
        'js': js_func_template,
    }[language]
    template_kw = {
        'function_name': func['name'],
        'language': language,
        'return_type': build_text_block(func['ret'], fixed=True),
        'description': build_function_description(func['brief_desc'], func['long_desc']),
    }
    if language == 'objc':
        name_fragments = func['name'].split(':')
        if (len(name_fragments) > 1):
            name_fragments = [f + ':' for f in name_fragments]
        template_kw['base_name'] = name_fragments[0]
        indent = len('- ()') + len(template_kw['return_type']) + len(name_fragments[0])
        template_kw['argstring'] = build_objc_argstring(name_fragments, func['args'], indent)
    else:
        template_kw['argstring'] = build_argstring(func['args'], len(func['name']) + 1)

    if language == 'java':
        template_kw['visibility'] = func['protection']
        template_kw['throws'] = build_text_block(func['exceptions'], fixed=True)
    if language == 'objc':
        template_kw['method_type'] = '+' if func['static'] else '-'

    return func_template.format(**template_kw)


def gen_markdown_c_struct(struct):
    members = []
    desc = []
    desc.append(build_text_block(struct['longdesc']))
    desc.append('\n')

    if len(struct['members']) == 0:
        return c_opaque_typedef_struct_template.format(
            class_name=struct['name'],
            description=''.join(desc),
        )

    for index, member in enumerate(struct['members'].itervalues()):
        if index != 0:
            members.append('\n')
        members.append(c_struct_member_template.format(
            indent=' '*4,
            type=build_text_block(member['type'], fixed=True),
            name=member['name'],
        ))
        description = [build_text_block(member['brief_desc']), build_text_block(member['long_desc'])]
        desc.append(c_struct_member_desc_template.format(
            name=member['name'],
            description='\n'.join(description),
        ))
    return c_typedef_struct_template.format(
        class_name=struct['name'],
        struct_body=''.join(members),
        description=''.join(desc),
    )


def gen_markdown_c_enum(enum):
    values = []
    desc = []
    desc.append(build_text_block(enum['long_desc']))
    desc.append('\n')

    for index, value in enumerate(enum['values']):
        if index != 0:
            values.append(',\n')
        initializer = value['initializer']
        values.append(c_enum_value_template.format(
            indent=' '*4,
            value_name=value['name'],
            initializer=' ' + initializer if initializer else '',
        ))
        description = [build_text_block(value['brief_desc']), build_text_block(value['long_desc'])]
        desc.append(c_enum_value_desc_template.format(
            name=value['name'],
            description='\n'.join(description),
        ))
    return c_enum_template.format(
        enum_name=enum['name'],
        enum_body=''.join(values),
        description=''.join(desc),
    )


def gen_markdown_c_typedef(typedef):
    return c_typedef_template.format(
        type=build_text_block(typedef['type']),
        name=typedef['name'],
        description=build_text_block(typedef['long_desc']),
    )


def gen_markdown_java_class(klass):
    members = []
    methods = []
    desc = []
    desc.append(build_text_block(klass['longdesc']))
    desc.append('\n')

    index = 0

    for index, member in enumerate(klass['members'].itervalues()):
        if index != 0:
            members.append('\n')
        members.append(java_class_member_template.format(
            indent=' '*4,
            type=build_text_block(member['type']),
            name=member['name'],
        ))
        description = [build_text_block(member['brief_desc']), build_text_block(member['long_desc'])]
        desc.append(java_class_member_desc_template.format(
            name=member['name'],
            description='\n'.join(description),
        ))

    for index, method in enumerate(klass['functions'], index):
        if index != 0:
            methods.append('\n')
        throws = build_text_block(method['exceptions'], fixed=True)
        throws = ' ' + throws if throws else ''
        typestrings = []
        typestrings.append(method['protection'])
        if method['ret']:
            typestrings.append(build_text_block(method['ret'], fixed=True))
        methods.append(java_class_method_template.format(
            indent=' '*4,
            type=' '.join(typestrings),
            name=method['name'],
            args=build_argstring(method['args'], -1),
            throws=throws,
        ))

    members.extend(methods)

    declaration = []
    declaration.append(klass['protection'])
    declaration.append('class')
    declaration.append(klass['name'])

    return java_class_template.format(
        class_name=klass['name'],
        class_declaration=' '.join(declaration),
        class_body=''.join(members),
        description=''.join(desc),
    )


def gen_markdown_objc_interface(interface):
    properties = []
    methods = []
    desc = []
    desc.append(build_text_block(interface['longdesc']))
    desc.append('\n')

    index = 0

    for index, property in enumerate(interface['properties'].itervalues()):
        if index != 0:
            properties.append('\n')
        properties.append(objc_interface_property_template.format(
            indent=' '*4,
            type=build_text_block(property['type']),
            name=property['name'],
        ))
        description = [build_text_block(property['brief_desc']), build_text_block(property['long_desc'])]
        desc.append(objc_interface_property_desc_template.format(
            name=property['name'],
            description='\n'.join(description),
        ))

    for index, method in enumerate(interface['functions'], index):
        if index != 0:
            methods.append('\n')

        name_fragments = method['name'].split(':')
        if (len(name_fragments) > 1):
            name_fragments = [f + ':' for f in name_fragments]
        methods.append(objc_interface_method_template.format(
            method_type='+' if method['static'] else '-',
            return_type=build_text_block(method['ret']),
            base_name=name_fragments[0],
            args=build_objc_argstring(name_fragments, method['args'], -1),
        ))

    properties.extend(methods)

    return objc_interface_template.format(
        class_name=interface['name'],
        base_name=interface['base'],
        interface_body=''.join(properties),
        description=''.join(desc),
    )


def gen_markdown_js_object(obj):
    desc = []
    desc.append(build_text_block(obj['longdesc']))
    desc.append('\n')

    for member in obj['members'].itervalues():
        description = [build_text_block(member['brief_desc']), build_text_block(member['long_desc'])]
        desc.append(js_object_property_desc_template.format(
            name=member['name'],
            description='\n'.join(description),
        ))

    for method in obj['functions']:
        desc.append(js_object_method_desc_template.format(
            name=method['name'],
            description=build_text_block(method['brief_desc']),
        ))

    return js_object_template.format(
        object_name=obj['name'],
        description=''.join(desc),
    )


def gen_markdown_file_c(docs, filename, content):
    with open(filename, 'w') as f:
        f.write(md_header)
        for path in content:
            item = docs
            for part in path:
                item = item[part]
            if item['kind'] == 'function':
                f.write(gen_markdown_function(item, 'c'))
            elif item['kind'] == 'struct':
                f.write(gen_markdown_c_struct(item))
            elif item['kind'] == 'enum':
                f.write(gen_markdown_c_enum(item))
            elif item['kind'] == 'typedef':
                f.write(gen_markdown_c_typedef(item))
            else:
                raise Exception('unrecognized item kind ' + item['kind'])


def gen_markdown_c(quiet_path, docs_path):
    docs = DoxygenXMLConsumer(os.path.join(quiet_path, 'docs/xml/'), gen_docs=quiet_path).docs
    content = {
        'transmitting': [
            ('quiet_portaudio_encoder',),
        ],
        'receiving': [
            ('quiet_portaudio_decoder',),
        ],
        'encoding': [
            ('quiet.h', 'typedefs', 'quiet_sample_t'),
            ('quiet_encoder',),
        ],
        'decoding': [
            ('quiet_decoder',),
        ],
        'configuration': [],
        'errors': [
            ('quiet.h', 'enums', 'quiet_error',),
        ],
        'frame-stats': [
            ('quiet_decoder_frame_stats',),
            ('quiet_complex',),
        ],
    }

    for index, func in enumerate(docs['quiet-portaudio.h']['functions']):
        name = func['name']
        if name.startswith('quiet_portaudio_encoder_'):
            content['transmitting'].append(('quiet-portaudio.h', 'functions', index))
        elif name.startswith('quiet_portaudio_decoder_'):
            content['receiving'].append(('quiet-portaudio.h', 'functions', index))
    for index, func in enumerate(docs['quiet.h']['functions']):
        name = func['name']
        if name.startswith('quiet_encoder_') and not name.startswith('quiet_encoder_profile'):
            content['encoding'].append(('quiet.h', 'functions', index))
        elif name.startswith('quiet_decoder_') and not name.startswith('quiet_decoder_profile'):
            content['decoding'].append(('quiet.h', 'functions', index))
        elif name.startswith('quiet_encoder_profile'):
            content['configuration'].append(('quiet.h', 'functions', index))
        elif name.startswith('quiet_decoder_profile'):
            content['configuration'].append(('quiet.h', 'functions', index))
        elif name == 'quiet_get_last_error':
            content['errors'].append(('quiet.h', 'functions', index))

    content['configuration'].append(('quiet_encoder_options',))
    content['configuration'].append(('quiet_decoder_options',))
    content['configuration'].append(('quiet_modulator_options',))
    content['configuration'].append(('quiet_demodulator_options',))
    content['configuration'].append(('quiet.h', 'enums', 'quiet_encoding_t',))
    content['configuration'].append(('quiet_ofdm_options',))
    content['configuration'].append(('quiet.h', 'enums', 'quiet_checksum_scheme_t',))
    content['configuration'].append(('quiet.h', 'enums', 'quiet_error_correction_scheme_t',))
    content['configuration'].append(('quiet.h', 'enums', 'quiet_modulation_scheme_t',))
    content['configuration'].append(('quiet_dc_filter_options',))
    content['configuration'].append(('quiet_resampler_options',))

    indices = {}
    for page, items in content.iteritems():
        for item in items:
            reflinks[item[-1]] = '{page}/#{item}'.format(page=page, item=item[-1])


    gen_markdown_file_c(docs, os.path.join(docs_path, 'transmitting.md'), content['transmitting'])
    gen_markdown_file_c(docs, os.path.join(docs_path, 'receiving.md',), content['receiving'])
    gen_markdown_file_c(docs, os.path.join(docs_path, 'encoding.md',), content['encoding'])
    gen_markdown_file_c(docs, os.path.join(docs_path, 'decoding.md',), content['decoding'])
    gen_markdown_file_c(docs, os.path.join(docs_path, 'configuration', 'auto.md',), content['configuration'])
    gen_markdown_file_c(docs, os.path.join(docs_path, 'errors.md',), content['errors'])
    gen_markdown_file_c(docs, os.path.join(docs_path, 'frame-stats.md',), content['frame-stats'])


def gen_markdown_android(quiet_path, docs_path):
    docs = DoxygenXMLConsumer(os.path.join(quiet_path, 'docs/xml/'), gen_docs=quiet_path).docs
    with open(os.path.join(docs_path, 'transmitting.md'), 'w') as f:
        f.write(md_header)
        f.write(gen_markdown_java_class(docs['FrameTransmitter']))
        for func in docs['FrameTransmitter']['functions']:
            f.write(gen_markdown_function(func, 'java'))
    with open(os.path.join(docs_path, 'receiving.md'), 'w') as f:
        f.write(md_header)
        f.write(gen_markdown_java_class(docs['FrameReceiver']))
        for func in docs['FrameReceiver']['functions']:
            f.write(gen_markdown_function(func, 'java'))
    with open(os.path.join(docs_path, 'configuration', 'auto.md'), 'w') as f:
        f.write(md_header)
        f.write(gen_markdown_java_class(docs['FrameTransmitterConfig']))
        for func in docs['FrameTransmitterConfig']['functions']:
            f.write(gen_markdown_function(func, 'java'))
        f.write(gen_markdown_java_class(docs['FrameReceiverConfig']))
        for func in docs['FrameReceiverConfig']['functions']:
            f.write(gen_markdown_function(func, 'java'))


def gen_markdown_ios(quiet_path, docs_path):
    docs = DoxygenXMLConsumer(os.path.join(quiet_path, 'docs/xml/'), gen_docs=quiet_path).docs
    with open(os.path.join(docs_path, 'transmitting.md'), 'w') as f:
        f.write(md_header)
        f.write(gen_markdown_objc_interface(docs['QMFrameTransmitter']))
        for func in docs['QMFrameTransmitter']['functions']:
            f.write(gen_markdown_function(func, 'objc'))
    with open(os.path.join(docs_path, 'receiving.md'), 'w') as f:
        f.write(md_header)
        f.write(gen_markdown_objc_interface(docs['QMFrameReceiver']))
        for func in docs['QMFrameReceiver']['functions']:
            f.write(gen_markdown_function(func, 'objc'))
    with open(os.path.join(docs_path, 'configuration', 'auto.md'), 'w') as f:
        f.write(md_header)
        f.write(gen_markdown_objc_interface(docs['QMTransmitterConfig']))
        for func in docs['QMTransmitterConfig']['functions']:
            f.write(gen_markdown_function(func, 'objc'))
        f.write(gen_markdown_objc_interface(docs['QMReceiverConfig']))
        for func in docs['QMReceiverConfig']['functions']:
            f.write(gen_markdown_function(func, 'objc'))


def gen_markdown_js(quiet_path, docs_path):
    docs = jsdoc_walk_docs(quiet_path)
    with open(os.path.join(docs_path, 'transmitting.md'), 'w') as f:
        f.write(md_header)
        f.write(gen_markdown_js_object(docs['Transmitter']))
        for func in docs['Quiet']['functions']:
            if func['name'] == 'Quiet.transmitter':
                f.write(gen_markdown_function(func, 'js'))
        for func in docs['Transmitter']['functions']:
            f.write(gen_markdown_function(func, 'js'))
    with open(os.path.join(docs_path, 'receiving.md'), 'w') as f:
        f.write(md_header)
        f.write(gen_markdown_js_object(docs['Receiver']))
        for func in docs['Quiet']['functions']:
            if func['name'] == 'Quiet.receiver':
                f.write(gen_markdown_function(func, 'js'))
        for func in docs['Receiver']['functions']:
            f.write(gen_markdown_function(func, 'js'))


def gen_markdown(path):
    gen_markdown_c(
            os.path.join(path, 'quiet'),
            os.path.join(path, 'docs/quiet')
    )
    gen_markdown_android(
            os.path.join(path, 'org.quietmodem.Quiet'),
            os.path.join(path, 'docs/org.quietmodem.Quiet'),
    )
    gen_markdown_ios(
            os.path.join(path, 'QuietModemKit'),
            os.path.join(path, 'docs/QuietModemKit'),
    )
    gen_markdown_js(
            os.path.join(path, 'quiet-js'),
            os.path.join(path, 'docs/quiet-js'),
    )


if __name__ == '__main__':
    scriptpath = os.path.dirname(os.path.realpath(__file__))
    gen_markdown(os.path.join(scriptpath, '..'))
