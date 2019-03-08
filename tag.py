#!/usr/bin/env python
from __future__ import print_function
import sys
import json
import logging
from argparse import ArgumentParser, REMAINDER
from util import get_url, post_and_wait, put_and_wait, delete_and_wait

def show_tags():
    response = get_url("dna/intent/api/v1/tag")
    print('{0:50}:{1:12}'.format('TagName','TagId'))
    for tag in response['response']:
        print ('{0:50}:{1:12}'.format(tag['name'], tag['id']))

def tag_mapping(tagId):
    '''

    :param tag: tag to look for
    :return: all device ID matching that tag
    '''
    if tagId is None:
        return []
    response = get_url('dna/intent/api/v1/tag/{}/member?memberType=networkdevice'.format(tagId))
    return [(association['instanceUuid'], association['managementIpAddress']) for association in response['response']]

def device2id(device):
    response = get_url('network-device/ip-address/{0}'.format(device))
    return response['response']['id']

def id2device(deviceId):
    response = get_url('network-device/{0}'.format(deviceId))
    return response['response']['managementIpAddress']


def tag2id(tagName):
    response = get_url("dna/intent/api/v1/tag?name={}".format(tagName))
    return response['response'][0]['id']

# dont use this.. will trash all existing tags on device.  which is expected as it is a PUT not a POST
def assign_tag_OLD(tag_id, device):
    # this will remove all existing tags..
    deviceId = device2id(device)
    payload = {
        "memberType":"networkdevice",
        "memberToTags":{deviceId:[tag_id]}}
    print(payload)
    response = put_and_wait('dna/intent/api/v1/tag/member', payload)
    print(response['progress'])

def assign_tag(tag_id, devicelist):
    # should refactor this to provide a list of devices
    deviceIds = list(map(device2id,devicelist))

    # this is a list of deviceIds
    payload = {
	"networkdevice" :deviceIds}

    print(payload)
    response = post_and_wait('dna/intent/api/v1/tag/{}/member'.format(tag_id), payload)
    print(response['progress'])

def remove_tag(tagId,device):
    deviceId = device2id(device)
    response = delete_and_wait('dna/intent/api/v1/tag/{}/member/{}'.format(tagId, deviceId))
    print(response['progress'])

def delete_tag(tag, devices):
    #tag/association/{{tagId}}?resourceType=network-device&resourceId={{deviceId}}
    print("\nDeleting tag:{0}".format(tag))
    tagId = tag2id(tag)

    for device in devices:
        remove_tag(tagId, device)
    # if no devices, then try to delete the tag
    if devices == []:

        response = delete_and_wait('dna/intent/api/v1/tag/{}'.format(tagId))
        print("Deleting tag {}: {}".format(tag,response['progress']))

def create_tag(tag):
    print ("Creating tag: {0}".format(tag))
    payload = { "name" : tag }
    response = post_and_wait('dna/intent/api/v1/tag', payload)
    print (response['progress'])

def add_tag(tag, devices):
    print("\nAdding tag:{0}".format(tag))
    try:
        tag_id = tag2id(tag)
    except IndexError as e:
        create_tag(tag)
    tag_id = tag2id(tag)
    assign_tag(tag_id, devices)

if __name__ == "__main__":
    parser = ArgumentParser(description='Select options.')
    parser.add_argument('--tag', type=str, required=False,
                        help="show devices with a tag")

    parser.add_argument('--addtag', type=str, required=False,
                        help="add tag to devices")
    parser.add_argument('--deletetag', type=str, required=False,
                        help="delete tag from devices")
    parser.add_argument('-v', action='store_true',
                        help="verbose")
    parser.add_argument('rest', nargs=REMAINDER)
    args = parser.parse_args()
    if args.v:
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    if args.tag:
        tag_id = tag2id(args.tag)
        id_ips = tag_mapping(tag_id)
        print ("{:38s}{:20s}".format("Device UUID","Device IP"))
        for id_ip in id_ips:
            print("{:38s}{:20s}".format(id_ip[0], id_ip[1]))

    elif args.addtag:
        add_tag(args.addtag, args.rest)
    elif args.deletetag:
        delete_tag(args.deletetag, args.rest)
    else:
        show_tags()
