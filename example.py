from client import ChannelClient
from zope.interface import implements
from twisted.internet import reactor, defer
import datetime
import logging
from settings import URL, KEY_READ, KEY_WRITE

#ID = EMAIL + '/temp3'

def generate_some_data():
	import math

	data = []
	for date,value in zip([datetime.datetime.utcnow() - datetime.timedelta(hours=10) + datetime.timedelta(minutes=b*10) for b in range(10)],[round(2+math.sin(c*10), 2) for c in range(10)]):
		#milliseconds epoch time
		e = datetime.datetime.utcfromtimestamp(0)
		time = str(int((date - e).total_seconds() * 1000))
		data.append({'t':time, 'd':value})
	return data

@defer.inlineCallbacks
def test():
	a = ChannelClient(
		url_domain=URL,
		decode_json=True,
		key_read=KEY_READ,
		key_write=KEY_WRITE
	)

	#result = yield a.channel_update(field1=2)
	#result = yield a.channel_status(8991)
	#result = yield a.channel_feed(8991)
	#result = yield a.channel_feed_last(8991)
	#result = yield a.channel_feed_field(8991, 1)
	result = yield a.channel_feed_field_last(8991, 1)
	print result
	reactor.stop()


logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s : %(message)s")
test()
reactor.run()
			

	
# vim: set ts=4 sw=4:
