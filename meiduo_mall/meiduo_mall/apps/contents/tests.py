import os

from django.conf import settings
from django.test import TestCase




# Create your tests here.

if __name__ == '__main__':


    # print(os.path.dirname(os.path.abspath("__file__")))
    # print(os.path.pardir)

    file_path = os.path.join('../../static/', 'test.txt')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write('1111111')