import plistlib
import re
import sys
import zipfile


def analyze_ipa_with_plistlib(ipa_path):
    ipa_file = zipfile.ZipFile(ipa_path)
    plist_path = find_plist_path(ipa_file)
    plist_data = ipa_file.read(plist_path)
    plist_root = plistlib.loads(plist_data)
    # print(plist_root)
    # print_ipa_info(plist_root)
    return plist_root['CFBundleShortVersionString']


def print_ipa_info(plist_root):
    print('Display Name: %s' % plist_root['CFBundleName'])
    print('Bundle Identifier: %s' % plist_root['CFBundleIdentifier'])
    print('Version: %s' % plist_root['CFBundleShortVersionString'])


def find_plist_path(zip_file):
    name_list = zip_file.namelist()
    # print name_list
    pattern = re.compile(r'Payload/[^/]*.app/Info.plist')
    for path in name_list:
        m = pattern.match(path)
        if m is not None:
            return m.group()


if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) < 1:
        print('Usage: python ipaInfo3.py /path/to/ipa')
        exit(0)

    ipa_path = args[0]
    analyze_ipa_with_plistlib(ipa_path)
