'''PartialFailure class implementation'''
import atproto_core

# pylint: disable=W0201 (attribute-defined-outside-init)
# pylint: disable=R0903 (too-few-public-methods)


class PartialFailure:
    '''Test class to simulate several atproto exceptions being raised
       but less than the failure limit. This will cause retries but not fail the
       operation'''
    def __init__(self, failure_limit, return_value):
        self.failure_limit = failure_limit
        self.return_value = return_value
        self.num_exceptions = 0

    def __call__(self, *args, **kwargs):
        self.num_exceptions += 1
        if self.num_exceptions < self.failure_limit:
            raise atproto_core.exceptions.AtProtocolError('Mocked Exception')
        return self.return_value
