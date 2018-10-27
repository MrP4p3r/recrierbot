"""Token factory."""

import string
import random


class TokenFactory(object):

    def create(self):
        smpl = string.digits + string.ascii_letters
        token = ''.join(random.sample(smpl, 32))
        return token
