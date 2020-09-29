import xmltodict


def dispatch_wechat_message(request):
    req_data = request.data
    xml_dict = xmltodict.parse(req_data)
    msg_dict = xml_dict.get('xml')
    print(xml_dict)

    msg_type = msg_dict.get('MsgType')
    if msg_type == 'text':
        pass
    elif msg_type == 'image':
        pass
    elif msg_type == 'image':
        pass
    elif msg_type == 'voice':
        pass
    elif msg_type == 'amr':
        pass
    elif msg_type == 'video':
        pass
    elif msg_type == 'shortvideo':
        pass
    elif msg_type == 'shortvideo':
        pass
    elif msg_type == 'shortvideo':
        pass














