import iron_rest
import logging

logger = logging.getLogger("iron_rest_test")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

@iron_rest.IronClient.retry(Exception)
def success_retry_test():
        print "SUCCESS from success_retry_test!"

@iron_rest.IronClient.retry(Exception, logger=logger)
def fail_retry_test():
        print "FAIL from fail_retry_test :("
        raise Exception()

@iron_rest.IronClient.retry(Exception, logger=logger)
def return_retry_test(msg):
        return msg

success_retry_test()
print return_retry_test("Return from return_retry_test")
fail_retry_test()
